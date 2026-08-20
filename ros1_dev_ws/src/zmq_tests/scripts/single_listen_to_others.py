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

        num_pub_sub_pairs = 10

        # Initialize trackers 
        self.ros_total_time_taken = []
        self.ros_msg_counter = []
        for i in range(num_pub_sub_pairs):
            self.ros_total_time_taken.append(0.0)
            self.ros_msg_counter.append(0) 
            
        start_sub = time.time()
        sub0 = rospy.Subscriber(f"/ros_pub/global_position/odom_0", Odometry, self.odom_callback0, queue_size=10) 
        end_sub = time.time()
    
    def odom_callback0(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub0: ", time_taken.to_sec())

    def shutdown_node(self):
        global global_polling
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    rospy.spin()