#!/usr/bin/env python3

# Listens to ROS odom messages over ZMQ from other drones and republish it locally in ROS 
# PARAMETERS ARE CONFIGURED USING ENV VARIABLES FOR EASY DOCKER USAGE INSTEAD OF ROS LAUNCH FILES (?)

import zmq
import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool, String
from typing import List
import os, sys
import threading
import time

class ZMQCommsServer():

    def __init__(self):
        rospy.init_node('zmq_comms_server', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)
        
        self.test_publisher = rospy.Publisher("/test/pose", PoseStamped, queue_size=10)
        self.global_polling = True

        # Init ZMQ 
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        # Goal socket
        self.sub_socket = self.context.socket(zmq.SUB)
        self.server_address = "tcp://localhost:5555"
        print("Listening goal poses at: " + self.server_address)
        self.sub_socket.connect(self.server_address)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "GoalPose") # listen to GoalPose
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, "RobotStatus") # listen to GoalPose
        self.poller.register(self.sub_socket, zmq.POLLIN)

    def run_poller(self):
        while self.global_polling:
            # Check for any data in sockets..
            socks = dict(self.poller.poll(timeout=10))
            # Iterate through all the sockets that recieved data
            for sock, event in socks.items():
                if event & zmq.POLLIN:
                    # Receive BOTH frames
                    topic, serialized_data = sock.recv_multipart()
                    print("Obtained data...")
                    if topic == b"GoalPose":
                        print ("Obtained Goalpose msg")
                    elif topic == b"RobotStatus":
                        print ("Obtained RobotStatus msg")
                    else:
                        print(f"ERROR! Received message on topic prefix: {topic}")

    def shutdown_node(self):
        self.global_polling = False
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ZMQCommsServer()
    zmq_node.run_poller()
