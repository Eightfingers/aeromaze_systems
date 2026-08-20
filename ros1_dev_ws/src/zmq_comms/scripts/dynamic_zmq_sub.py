#!/usr/bin/env python3

# Listens to ROS odom messages over ZMQ from other drones and republish it locally in ROS 
# PARAMETERS ARE CONFIGURED USING ENV VARIABLES FOR EASY DOCKER USAGE INSTEAD OF LAUNCH FILES (?)

import zmq
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, String
from typing import List
import os, sys
import threading
import time

class ExternalComms():

    def __init__(self):
        rospy.init_node('other_drone_odometry', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        # Variables
        self.num_drones = int(os.environ['NUM_DRONES'])
        self.agent_id = int(os.environ['AGENT_ID'])
        self.str_start_ip = os.environ['START_IP']
        self.ground_station_ip = os.environ['GROUND_STATION_IP']

        print("Loading configuration from environment variables...")
        try:
            self.num_drones = int(os.environ['NUM_DRONES'])
            self.agent_id = int(os.environ['AGENT_ID'])
            self.str_start_ip = os.environ['START_IP']
            self.ground_station_ip = os.environ['GROUND_STATION_IP']
        except KeyError as e:
            # This triggers if a variable is MISSING
            print(f"CRITICAL: Environment variable {e} is not set!")
            sys.exit(1)
        except ValueError as e:
            # This triggers if int() conversion FAILS (e.g., NUM_DRONES="abc")
            print(f"CRITICAL: Environment variable has invalid type: {e}")
            sys.exit(1)

        self.global_polling = True
        self.validate_ipv4_address(self.str_start_ip)
        self.num_pub_sub_pairs = int(self.num_drones)
        parts = self.str_start_ip.split('.')
        self.start_ip_fourth_octet = int(parts[3])
        self.str_first_second_third_octet = parts[0] + "." + parts[1] + "." + parts[2] + "."

        # ROS goal setpoint topics
        self.move_bool_pub = rospy.Publisher("/move_base_simple/goal_bool", Bool, queue_size=10)
        self.goal_pose_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=10)
        self.take_off_pub = rospy.Publisher("/drone_self/state", String, queue_size=10)
        
        # Initialize the other agent ros publishers 
        self.pub_odom_lists: List[rospy.Publisher] = []
        self.pub_pose_lists: List[rospy.Publisher] = []
        self.pub_offset_lists: List[rospy.Publisher] = []
        for i in range(self.num_pub_sub_pairs):
            if i >= 9: # Formatting stuff
                odom_pub = rospy.Publisher(f"/agent0{i+1}/global_position/odom", Odometry, queue_size=10)
                pose_pub = rospy.Publisher(f"/agent0{i+1}/global_position/pose", PoseStamped, queue_size=10)
                offset_pub = rospy.Publisher(f"/agent0{i+1}/takeoff_offset", PoseStamped, queue_size=10)
                print(f"Created publishers for /agent0{i+1}")
                self.pub_odom_lists.append(odom_pub)
                self.pub_pose_lists.append(pose_pub)
                self.pub_offset_lists.append(offset_pub)
            else:
                odom_pub = rospy.Publisher(f"/agent00{i+1}/global_position/odom", Odometry, queue_size=10)
                pose_pub = rospy.Publisher(f"/agent00{i+1}/global_position/pose", PoseStamped, queue_size=10)
                offset_pub = rospy.Publisher(f"/agent00{i+1}/takeoff_offset", PoseStamped, queue_size=10)
                print(f"Created publishers for /agent00{i+1} ")
                self.pub_odom_lists.append(odom_pub)
                self.pub_pose_lists.append(pose_pub)
                self.pub_offset_lists.append(offset_pub)

        # Init ZMQ 
        self.zmq_sockets_map = {}
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        # Goal socket
        self.goal_sub_socket = self.context.socket(zmq.SUB)
        self.goal_publisher_address = "tcp://{}:5555".format(self.ground_station_ip)
        print("Listening goal poses at: " + self.goal_publisher_address)
        self.goal_sub_socket.connect(self.goal_publisher_address)
        self.goal_sub_socket.setsockopt_string(zmq.SUBSCRIBE, "GoalPose")
        self.zmq_sockets_map[self.goal_sub_socket] = 1000 # THE GOAL PUBLISHER!!
        self.poller.register(self.goal_sub_socket, zmq.POLLIN)
        # Agent sockets
        for i in range(self.num_pub_sub_pairs):
            str_current_ip = self.str_first_second_third_octet + str(self.start_ip_fourth_octet + i)
            agent_socket = self.context.socket(zmq.SUB)
            agent_socket.setsockopt(zmq.LINGER, 0)
            agent_socket.setsockopt_string(zmq.SUBSCRIBE, f"Odometry")
            agent_socket.setsockopt_string(zmq.SUBSCRIBE, f"Offset")
            agent_socket.connect(f"tcp://{str_current_ip}:5555")
            self.zmq_sockets_map[agent_socket] = i
            self.poller.register(agent_socket, zmq.POLLIN)
            print(f"ZMQ socket for tcp://{str_current_ip}:5555 is established")

    def delayed_publish(self, msg):
        time.sleep(1)
        if msg.data == "2":
            print("Taking off!!")
            self.move_bool_pub.publish(True)
        elif msg.data == "6":
            print("Landing")
        self.take_off_pub.publish(msg.data)

    def validate_ipv4_address(self, ip_address: str):
        parts = ip_address.split('.')
        if len(parts) != 4:
            raise ValueError("Invalid IPv4 address: must contain exactly four octets.")
        for part in parts:
            if not part.isdigit():
                raise ValueError(f"Invalid octet detected! '{part}': must be numeric.")
            value = int(part)
            if not (0 <= value <= 255):
                raise ValueError(f"Invalid octet detected! '{part}': must be in range 0–255.")

    def run_poller(self):
        while self.global_polling:
            # Check for any data in sockets..
            socks = dict(self.poller.poll(timeout=10))
            for sock, event in socks.items():
                agent_index = self.zmq_sockets_map[sock]
                if event & zmq.POLLIN:
                    try:
                        message = sock.recv()
                        topic, serialized_data = message.split(b" ", 1)  # Split by whitespace
                        # time_taken = rospy.Time.now() - pose_deserialized_msg.header.stamp

                        if agent_index == 1000:
                            agent_state_msg = String()
                            agent_state_msg.deserialize(serialized_data)
                            threading.Thread(target=self.delayed_publish(agent_state_msg), daemon=True).start()
                        else:
                            # print(topic.decode())
                            if topic == b'Odometry':
                                pose_deserialized_msg = PoseStamped()
                                pose_deserialized_msg.deserialize(serialized_data)
                                odometry_msg = Odometry()
                                odometry_msg.header = pose_deserialized_msg.header
                                odometry_msg.pose.pose = pose_deserialized_msg.pose

                                self.pub_pose_lists[agent_index].publish(pose_deserialized_msg)
                                self.pub_odom_lists[agent_index].publish(odometry_msg)
                            elif topic == b'Offset':
                                pose_deserialized_msg = PoseStamped()
                                pose_deserialized_msg.deserialize(serialized_data)
                                self.pub_offset_lists[agent_index].publish(pose_deserialized_msg)
                                pass

                    except zmq.ZMQError as e:
                        print("Recv error:", e)

    def shutdown_node(self):
        self.global_polling = False
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    zmq_node.run_poller()
