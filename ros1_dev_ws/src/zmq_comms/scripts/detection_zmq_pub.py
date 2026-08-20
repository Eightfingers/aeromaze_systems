#!/usr/bin/env python3

import zmq
import rospy
from std_msgs.msg import String

# Subscribes to a ROS String topic carrying the detection table as JSON and
# forwards the raw JSON string over a ZMQ PUB socket on port 5556.

class DetectionZMQPub:
    def __init__(self):
        rospy.init_node('detection_zmq_pub', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        self.detection_sub = rospy.Subscriber('/detections_table', String, self.detection_cb)

        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:5556")
        rospy.loginfo("Detection ZMQ publisher ready on tcp://*:5556")

    def detection_cb(self, msg):
        self.socket.send(msg.data.encode('utf-8'))
        rospy.loginfo("Forwarded detection over ZMQ: " + msg.data)

    def shutdown_node(self):
        rospy.loginfo("Shutting down detection ZMQ publisher")
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    node = DetectionZMQPub()
    rospy.spin()
