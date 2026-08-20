#!/usr/bin/env python3

import zmq
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
import time
from typing import List
import os

class ExternalComms():

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

    def __init__(self):
        rospy.init_node('other_drone_odometry', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        # Variables
        self.global_polling = True
        self.num_drones = int(os.environ['NUM_DRONES'])
        self.agent_id = int(os.environ['AGENT_ID'])
        self.str_start_ip = os.environ['START_IP']
        self.validate_ipv4_address(self.str_start_ip)
        self.num_pub_sub_pairs = int(self.num_drones)
        parts = self.str_start_ip.split('.')        
        self.start_ip_fourth_octet = int(parts[3])
        self.str_first_second_third_octet = parts[0] + "." + parts[1] + "." + parts[2] + "."

        # For Statistics
        self.number_of_msgs_to_count = 100
        self.zmq_msg_counter = []
        for i in range(self.num_pub_sub_pairs):
            self.zmq_msg_counter.append(0.0)

        # Init ZMQ 
        self.zmq_sockets: List[zmq.Socket] = []
        self.zmq_sockets_map = {}
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        # i+1 as we start enumarting agents from 1!!!!!
        for i in range(self.num_pub_sub_pairs):
            str_current_ip = self.str_first_second_third_octet + str(self.start_ip_fourth_octet + i)
            if i+1 == self.agent_id:
                print(f"Skipping establishing connecting to myself at: {str_current_ip}")
            else:
                socket = self.context.socket(zmq.SUB)
                socket.setsockopt(zmq.LINGER, 0)
                socket.setsockopt_string(zmq.SUBSCRIBE, f"Odometry")
            
            # socket.connect(f"tcp://localhost:555{i}")
            socket.connect(f"tcp://{str_current_ip}:5555")
            self.zmq_sockets.append(socket)
            self.zmq_sockets_map[socket] = i
            self.poller.register(socket, zmq.POLLIN)
            print(f"ZMQ socket for tcp://{str_current_ip}:5555 is established")

        # socket.connect(f"tcp://localhost:5555")
        # self.zmq_sockets.append(socket)
        # self.zmq_sockets_map[socket] = 1
        # self.poller.register(socket, zmq.POLLIN)
        # print(f"ZMQ socket for tcp://localhost:5555 is established")


        # Initialize the corresponding ros publishers to pipe the ZMQ data through
        self.pub_odom_lists: List[rospy.Publisher] = []
        self.pub_pose_lists: List[rospy.Publisher] = []
        for i in range(self.num_pub_sub_pairs):
            if i+1 == self.agent_id:
                pass
            else:
                odom_pub = rospy.Publisher(f"/agent{i+1}/global_position/odom", Odometry, queue_size=10)
                pose_pub = rospy.Publisher(f"/agent{i+1}/global_position/pose", PoseStamped, queue_size=10)
                print(f"Created publisher for /agent{i+1}/global_position/odom ")
                self.pub_odom_lists.append(odom_pub)
                self.pub_pose_lists.append(pose_pub)

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
                        # print(topic.decode())

                        pose_deserialized_msg = PoseStamped()
                        pose_deserialized_msg.deserialize(serialized_data)
                        time_taken = rospy.Time.now() - pose_deserialized_msg.header.stamp
                        
                        odometry_msg = Odometry()
                        odometry_msg.header = pose_deserialized_msg.header
                        odometry_msg.pose.pose = pose_deserialized_msg.pose

                        self.pub_pose_lists[agent_index].publish(pose_deserialized_msg)
                        self.pub_odom_lists[agent_index].publish(odometry_msg)

                    except zmq.ZMQError as e:
                        print("Recv error:", e)

            # for socket in socks:
            #     if socket in self.zmq_sockets:
            #         try:
            #             message = socket.recv()
            #             # print("Length of message in bytes:", len(message))
            #             topic, serialized_data = message.split(b" ", 1)  # Split by whitespace
            #             for i in range(self.num_pub_sub_pairs):
            #                 if topic.decode() == f"Odometry{i}":
            #                     # Time to process the msg
            #                     odom_deserialized_msg = Odometry()
            #                     odom_deserialized_msg.deserialize(serialized_data)
            #                     time_taken = rospy.Time.now() - odom_deserialized_msg.header.stamp
                                
            #                     pose_msg = PoseStamped()
            #                     pose_msg.header = odom_deserialized_msg.header
            #                     pose_msg.pose = odom_deserialized_msg.pose.pose

            #                     self.pub_odom_lists[i+1].publish(odom_deserialized_msg)
            #                     self.pub_pose_lists[i+1].publish(pose_msg)
            #                     # print(f"End to End time taken for sub{i}: ", time_taken.to_sec())
            #                     # print(f"End to End time taken for sub{i}: ", time_taken.to_sec())

            #         except Exception as e:
            #             print(f"Error processing message: {e}")

    def shutdown_node(self):
        self.global_polling = False
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    zmq_node.run_poller()
