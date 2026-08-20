#!/usr/bin/env python3

import zmq
from geometry_msgs.msg import PoseStamped
import io
import time

# Run this script to publish setpoints to all drones on the Ground Control Computer!!!

# STARLING 2 Camera POV
# Positive X -> Right 
# Positive Y -> Forward 

# EMNAVI GLOBAL FRAME, INITIALIZED WITH CAMERA FACING FORWARD
# Positive X -> Foward
# Positive Y -> LEFT

# NUS VICON ROOM
# POSITIVE X -> is Left
# POSITIVE Y -> is backward

class PosePublisher:
    def __init__(self):
        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")  # Publisher binds to port 5555
        print("ZMQ setup ready")
    
    def pose_pub(self):
        # Create a BytesIO buffer for serialization
        buffer = io.BytesIO()

        msg = PoseStamped()
        msg.header.frame_id = 'map'
        # msg.pose.position.x = -1.8
        # msg.pose.position.y = 1.2
        # msg.pose.position.z = 1.0

        # msg.pose.position.x = 0.65 
        # msg.pose.position.y = 2.00
        # msg.pose.position.z = 1.0

        msg.pose.position.x = 1.5
        msg.pose.position.y = 1.0
        # msg.pose.position.y = 0.0
        msg.pose.position.z = 1.2

        # msg.pose.position.x = 0.0
        # msg.pose.position.y = 2.0
        # # msg.pose.position.y = 0.0
        # msg.pose.position.z = 1.2

        # Serialize the message into the buffer
        msg.serialize(buffer)

        # serialized_msg = roslib.message.serialize_message(msg)D
        # Send serialized message over ZeroMQ
        print("Sent goal pose: x:{}, y:{}, z:{}".format(msg.pose.position.x, msg.pose.position.y, msg.pose.position.z))
        message = b"GoalPose " + buffer.getvalue()  # Combine topic label and serialized message
        self.socket.send(message)  # Send raw bytes

    def shutdown_node(self):
        print("Shutting down node")
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    node = PosePublisher()
    node.pose_pub()
    time.sleep(1)
    node.pose_pub()
    time.sleep(1)
    node.shutdown_node()
