#!/usr/bin/env python3

import zmq
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import io
import time
from typing import List

class PosePublisher:
    def __init__(self):
        rospy.init_node('timer_pose_publish', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)
        num_pub_sub_pairs = 10

        # Setup a list of ros pubs and making it strongly typed
        self.pub_odom_lists: List[rospy.Publisher] = []
        
        start_init = time.time()
        for i in range(num_pub_sub_pairs):
            start_pub = time.time()
            odom_pub = rospy.Publisher(f"/ros_pub/global_position/odom_{i}", Odometry, queue_size=10)
            end_pub = time.time()
            print(f"Time taken to create ROS odom publisher: {end_pub - start_pub:.6f} seconds")
            self.pub_odom_lists.append(odom_pub)

        end_init = time.time()
        print(f"Time taken to create every ROS publisher: {end_init - start_init:.6f} seconds")

        # Setup ZeroMQ publishers
        self.zmq_sockets: List[zmq.Socket] = []
        self.context = zmq.Context()
        start_zmq_init = time.time()
        for i in range(num_pub_sub_pairs):
            start_zmq_pub = time.time()
            socket = self.context.socket(zmq.PUB)
            socket.setsockopt(zmq.LINGER, 0)
            socket.bind(f"tcp://*:555{i}")
            self.zmq_sockets.append(socket)
            end_zmq_pub = time.time()
            print(f"Time taken to create ZMQ pose publisher: {end_zmq_pub - start_zmq_pub:.6f} seconds")
        end_zmq_init = time.time()
        print(f"Time taken to create every ZMQ Pose publisher: {end_zmq_init - start_zmq_init:.6f} seconds")
        rospy.loginfo("Local socket is ready ")

        # 20 Hz => 1 / 20 = 0.05 seconds
        self.timer = rospy.Timer(rospy.Duration(0.05), self.timer_pose_publish)
    
    def timer_pose_publish(self, event):
        odom_msg = Odometry()
        odom_msg.pose.pose.position.x = 0
        odom_msg.pose.pose.position.y = 0
        odom_msg.pose.pose.position.z = 1
        odom_msg.header.frame_id = 'map'
        odom_msg.header.stamp = rospy.Time.now()

        # Publish as ROS odom
        for odom_pub in self.pub_odom_lists:
            odom_pub.publish(odom_msg)

        # serialized_msg = roslib.message.serialize_message(msg)
        # Send serialized message over ZeroMQ
        for id, socket in enumerate(self.zmq_sockets):
            if socket.closed:
                print("Socket is already closed! Stopping timer")
                return
            else:
                # Create a BytesIO buffer for serialization
                buffer = io.BytesIO()
                # Serialize the message into the buffer
                odom_msg.serialize(buffer)
                prefix = f"Odometry{id} "
                message = prefix.encode() + buffer.getvalue()  # Combine topic label and serialized message
                # print("Length of message in bytes:", len(message))
                socket.send(message)
    
    def shutdown_node(self):
        rospy.loginfo("Shutting down self pose publisher")        
        for socket in self.zmq_sockets:
            socket.close()
        self.context.term()

if __name__ == "__main__":
    node = PosePublisher()
    rospy.spin()
