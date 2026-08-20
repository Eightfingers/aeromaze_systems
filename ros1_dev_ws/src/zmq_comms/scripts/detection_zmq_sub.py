#!/usr/bin/env python3

import json
import os
import sys
import time
import zmq
import rospy
from std_msgs.msg import String

# ZMQ SUB node that collates detection tables received over ZMQ from each
# agent (each agent publishes on *:5556) together with local detections
# arriving on the /detections ROS topic. The merged table is republished on
# /detections_table every second. Agent addresses are derived from START_IP +
# NUM_DRONES env vars, mirroring the pattern used in dynamic_zmq_sub.py.

class DetectionZMQSub:
    def __init__(self):
        rospy.init_node('detection_zmq_sub', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        print("Loading configuration from environment variables...")
        try:
            self.num_drones = int(os.environ['NUM_DRONES'])
            self.str_start_ip = os.environ['START_IP']
        except KeyError as e:
            print(f"CRITICAL: Environment variable {e} is not set!")
            sys.exit(1)
        except ValueError as e:
            print(f"CRITICAL: Environment variable has invalid type: {e}")
            sys.exit(1)

        self.validate_ipv4_address(self.str_start_ip)
        parts = self.str_start_ip.split('.')
        self.start_ip_fourth_octet = int(parts[3])
        self.str_first_second_third_octet = parts[0] + "." + parts[1] + "." + parts[2] + "."

        # Collation table: from_agent -> {data, last_update}
        self.detections = {}
        self.global_polling = True

        # ROS setup: ingest local detections, republish the merged table
        self.detection_sub = rospy.Subscriber('/detections', String, self.detection_cb)
        self.table_pub = rospy.Publisher('/detections_table', String, queue_size=10)

        # ZeroMQ setup: one SUB socket per agent
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        self.sockets = []
        for i in range(self.num_drones):
            str_current_ip = self.str_first_second_third_octet + str(self.start_ip_fourth_octet + i)
            socket = self.context.socket(zmq.SUB)
            socket.setsockopt(zmq.LINGER, 0)
            socket.setsockopt_string(zmq.SUBSCRIBE, "")
            socket.connect(f"tcp://{str_current_ip}:5556")
            self.poller.register(socket, zmq.POLLIN)
            self.sockets.append(socket)
            print(f"Detection ZMQ socket for tcp://{str_current_ip}:5556 established")

        rospy.loginfo("Detection ZMQ subscriber ready")
        self.table_timer = rospy.Timer(rospy.Duration(1.0), self.publish_table)

    def validate_ipv4_address(self, ip_address: str):
        parts = ip_address.split('.')
        if len(parts) != 4:
            raise ValueError("Invalid IPv4 address: must contain exactly four octets.")
        for part in parts:
            if not part.isdigit():
                raise ValueError(f"Invalid octet detected! '{part}': must be numeric.")
            value = int(part)
            if not (0 <= value <= 255):
                raise ValueError(f"Invalid octet detected! '{part}': must be in range 0-255.")

    def detection_cb(self, msg):
        try:
            parsed = json.loads(msg.data)
            self.merge_detection(parsed, time.time())
        except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
            rospy.logwarn(f"Malformed JSON detection dropped: {e}")

    def merge_detection(self, data, last_update):
        agent_id = data.get('from_agent')
        if agent_id is None:
            rospy.logwarn("Received detection missing 'from_agent' field, skipping")
            return
        entry = self.detections.get(agent_id)
        if entry is not None and entry["last_update"] >= last_update:
            return
        self.detections[agent_id] = {
            "data": data,
            "last_update": last_update,
        }

    def run_poller(self):
        while self.global_polling:
            socks = dict(self.poller.poll(timeout=10))
            for sock, event in socks.items():
                if event & zmq.POLLIN:
                    try:
                        raw = sock.recv()
                        parsed = json.loads(raw.decode('utf-8'))
                        if not isinstance(parsed, list):
                            rospy.logwarn("Received detection table is not a JSON list, skipping")
                            continue
                        last_update = time.time()
                        for entry in parsed:
                            self.merge_detection(entry, last_update)
                    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
                        rospy.logwarn(f"Malformed JSON detection table dropped: {e}")
                    except zmq.ZMQError as e:
                        print("Recv error:", e)

    def publish_table(self, event):
        if not self.detections:
            return
        table = [
            dict(entry["data"], last_update=entry["last_update"])
            for entry in self.detections.values()
        ]
        self.table_pub.publish(String(data=json.dumps(table)))

        rows = []
        for agent_id, entry in self.detections.items():
            d = entry["data"]
            pose = d.get("global_pose", {})
            rows.append(
                f"| {agent_id:<5} | {d.get('type', '-'):<10} | {d.get('confidence', '-'):<5} "
                f"| {pose.get('x', '-'):<6} | {pose.get('y', '-'):<6} | {pose.get('z', '-'):<6} "
                f"| {entry['last_update']:.2f} |"
            )
        header = "| Agent | Type       | Conf  | X      | Y      | Z      | Last Update |"
        separator = "+-------+------------+-------+--------+--------+--------+-------------+"
        rospy.loginfo("\n" + separator + "\n" + header + "\n" + separator + "\n" + "\n".join(rows) + "\n" + separator)

    def shutdown_node(self):
        self.global_polling = False
        self.table_timer.shutdown()
        rospy.loginfo("Shutting down detection ZMQ subscriber")
        for sock in self.sockets:
            self.poller.unregister(sock)
            sock.close()
        self.context.term()

if __name__ == '__main__':
    node = DetectionZMQSub()
    node.run_poller()
