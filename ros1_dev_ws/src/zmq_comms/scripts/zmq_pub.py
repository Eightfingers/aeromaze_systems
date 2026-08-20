#!/usr/bin/env python3

import zmq
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import io
import os, sys

# Reponsible for republishing mavros local position with offsets (therefore its global position) and over ZMQ to other drones
# Odom and Pose contain the same data value its more for compatibility!!

class ZMQCommsPub:
    def __init__(self):
        rospy.init_node('pose_publisher', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        print("Loading offsets from environment variables...")
        try:
            self.x_offset = float(os.environ['X_OFFSET'])
            self.y_offset = float(os.environ['Y_OFFSET'])
            self.z_offset = float(os.environ['Z_OFFSET'])
            self.agent_id = int(os.environ['AGENT_ID'])
        except (ValueError, KeyError) as e:
            print("Invalid environment variables detected! Ensure that the .env file is loaded and contains valid float values!")
            sys.exit(1)

        self.mavros_local_sub = rospy.Subscriber('/mavros/local_position/pose', PoseStamped, self.pose_callback)
        self.agent_takeoff_offset_sub = rospy.Subscriber(f"/drone_self/offset_pose", PoseStamped, self.agent_offset_cb)
        self.self_drone_pose_pub = rospy.Publisher("/drone_self/global_position/pose", PoseStamped, queue_size=10)
        self.self_drone_odom_pub = rospy.Publisher("/drone_self/global_position/odom", Odometry, queue_size=10)

        # Limit the amount of publishing
        self.counter = 0
        self.counter_max = 2

        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")  # Publisher binds to port 5555
        rospy.loginfo("Local socket is ready ")
    
    def pose_callback(self, msg):
        # Create a BytesIO buffer for serialization
        buffer = io.BytesIO()
        msg.pose.position.x += self.x_offset
        msg.pose.position.y += self.y_offset
        msg.pose.position.z += self.z_offset
        msg.header.frame_id = 'map'
        self.counter += 1
        
        if self.counter == self.counter_max:
            self.counter = 0
            # Serialize the message into the buffer
            msg.serialize(buffer)

            # Send serialized message over ZeroMQ
            message = b"Odometry " + buffer.getvalue()  # Combine topic label and serialized message
            self.socket.send(message)  # Send raw bytes

        # Publish self pose
        self.self_drone_pose_pub.publish(msg)

        # Publish self odom
        odom_msg = Odometry()
        odom_msg.pose.pose = msg.pose
        odom_msg.header= msg.header
        self.self_drone_odom_pub.publish(odom_msg)

    def agent_offset_cb(self, msg):
        buffer = io.BytesIO()
        # Serialize the message into the buffer
        msg.serialize(buffer)

        # Send serialized message over ZeroMQ
        message = b"Offset " + buffer.getvalue()  # Combine topic label and serialized message
        self.socket.send(message)  # Send raw bytes

    def shutdown_node(self):
        rospy.loginfo("Shutting down self pose publisher")
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    node = ZMQCommsPub()
    rospy.spin()