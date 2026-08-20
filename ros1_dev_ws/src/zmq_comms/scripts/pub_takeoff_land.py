#!/usr/bin/env python3

import zmq
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
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
    
    # "2" for take off, "6" to land
    def pub_agent_state(self, data="2"):
        # Create a BytesIO buffer for serialization
        buffer = io.BytesIO()
        msg = String()
        msg.data = data 

        # Serialize the message into the buffer
        msg.serialize(buffer)
        # serialized_msg = roslib.message.serialize_message(msg)D
        # Send serialized message over ZeroMQ
        message = b"GoalPose " + buffer.getvalue()  # Combine topic label and serialized message
        self.socket.send(message)  # Send raw bytes

    def shutdown_node(self):
        print("Shutting down node")
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    node = PosePublisher()
    node.pub_agent_state("2")
    time.sleep(1)
    node.pub_agent_state("2")
    time.sleep(1)
    node.shutdown_node()
