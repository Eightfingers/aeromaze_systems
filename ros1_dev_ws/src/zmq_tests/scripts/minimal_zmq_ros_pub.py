#!/usr/bin/env python3

import zmq
import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import io
import time

class ZMQCommsClient:
    def __init__(self):

        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5555")  
        # Publisher binds to port 5555
        rospy.init_node("minimal_zmq_pub")
        rospy.loginfo("Local socket is ready!")
    
        # Create a BytesIO buffer for serialization
        buffer = io.BytesIO()
        msg = PoseStamped()
        msg.pose.position.x = 1
        msg.pose.position.y = 1
        msg.pose.position.z = 1
        msg.header.frame_id = 'map'
        # Serialize the message into a buffer
        msg.serialize(buffer)
        # Send multi-part ZMQ message
        print("Sending using multipart")
        self.socket.send_multipart([b"GoalPose", buffer.getvalue()])

        time.sleep(1)

        print("Sending using SNDMORE option, functionally the same as multipart")
        msg.pose.position.x = 0
        msg.pose.position.y = 0
        msg.pose.position.z = 0
        msg.header.frame_id = 'map'
        # Serialize the message into a buffer
        msg.serialize(buffer)
        self.socket.send_string("GoalPose", zmq.SNDMORE)
        self.socket.send(buffer.getvalue())

    def shutdown_node(self):
        rospy.loginfo("ZMQCommsClient")
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    node = ZMQCommsClient()
    rospy.spin()