#!/usr/bin/env python3

from geometry_msgs.msg import PoseStamped
import zmq
import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
import threading
import time
from typing import List

global global_polling
global_polling = True

class ExternalComms():

    def __init__(self):
        rospy.init_node('other_drone_odometry', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        self.num_pub_sub_pairs = 10
        self.number_of_msgs_to_count = 200

        self.zmq_sockets: List[zmq.Socket] = []
        self.zmq_total_time_taken = []
        self.zmq_msg_counter = []
        self.zmq_sub_init_time = []
        self.num_filled_up_sockets = 0

        self.context = zmq.Context()
        self.poller = zmq.Poller()
        for i in range(self.num_pub_sub_pairs):
            self.zmq_total_time_taken.append(0.0)
            self.zmq_msg_counter.append(0) 

        start_zmq_init = time.time()
        for i in range(self.num_pub_sub_pairs):
            start_zmq_sub = time.time()
            socket = self.context.socket(zmq.SUB)
            socket.setsockopt(zmq.LINGER, 0)
            socket.setsockopt_string(zmq.SUBSCRIBE, f"Odometry{i}")
            socket.connect(f"tcp://localhost:555{i}")
            self.zmq_sockets.append(socket)
            self.poller.register(socket, zmq.POLLIN)
            end_zmq_sub = time.time()
            self.zmq_sub_init_time.append(end_zmq_sub)
            print(f"Time taken to connect to ZMQ socket{i} : {end_zmq_sub - start_zmq_sub:.6f} seconds")
        end_zmq_init = time.time()
        print(f"All ZMQ sockets took : {end_zmq_init - start_zmq_init:.6f} seconds to create")

    def run_poller(self):
        while global_polling:
            # Check for any data in sockets..
            socks = dict(self.poller.poll(timeout=10))
            for socket in socks:
                if socket in self.zmq_sockets:
                    try:
                        message = socket.recv()
                        # print("Length of message in bytes:", len(message))
                        topic, serialized_data = message.split(b" ", 1)  # Split by whitespace
                        for i in range(self.num_pub_sub_pairs):
                            if topic.decode() == f"Odometry{i}":
                                # Time to process the msg
                                odom_deserialized_msg = Odometry()
                                odom_deserialized_msg.deserialize(serialized_data)
                                time_taken = rospy.Time.now() - odom_deserialized_msg.header.stamp
                                # print(f"End to End time taken for sub{i}: ", time_taken.to_sec())
                                self.zmq_total_time_taken[i] += time_taken.to_sec()
                                self.zmq_msg_counter[i] += 1
                                # print(f"End to End time taken for sub{i}: ", time_taken.to_sec())
                                if (self.zmq_msg_counter[i] == self.number_of_msgs_to_count):
                                    avg_time = self.zmq_total_time_taken[i] / self.zmq_msg_counter[i]
                                    time_taken_to_fill_up = time.time() - self.zmq_sub_init_time[i]
                                    print(f"Average end to end time taken for sub{i}: {avg_time:.6f} seconds and it took {time_taken_to_fill_up:.6f} seconds to fill up the socket.")
                                    # Reset counters
                                    # self.zmq_total_time_taken[i] = 0.0
                                    # self.zmq_msg_counter[i] = 0
                                    self.num_filled_up_sockets += 1
                                if self.num_filled_up_sockets == self.num_pub_sub_pairs:
                                    rospy.signal_shutdown("All sockets have reached the limit.. shutting down node.")

                    except Exception as e:
                        print(f"Error processing message: {e}")

    def shutdown_node(self):
        global global_polling
        global_polling = False
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    zmq_node.run_poller()
