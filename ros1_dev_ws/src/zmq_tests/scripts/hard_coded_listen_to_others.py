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

        init_start_sub = time.time()

        start_sub = time.time()
        sub0 = rospy.Subscriber(f"/ros_pub/global_position/odom_0", Odometry, self.odom_callback0, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub1 = rospy.Subscriber(f"/ros_pub/global_position/odom_1", Odometry, self.odom_callback1, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub2 = rospy.Subscriber(f"/ros_pub/global_position/odom_2", Odometry, self.odom_callback2, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub3 = rospy.Subscriber(f"/ros_pub/global_position/odom_3", Odometry, self.odom_callback3, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub4 = rospy.Subscriber(f"/ros_pub/global_position/odom_4", Odometry, self.odom_callback4, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub5 = rospy.Subscriber(f"/ros_pub/global_position/odom_5", Odometry, self.odom_callback5, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub6 = rospy.Subscriber(f"/ros_pub/global_position/odom_6", Odometry, self.odom_callback6, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub7 = rospy.Subscriber(f"/ros_pub/global_position/odom_7", Odometry, self.odom_callback7, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub8 = rospy.Subscriber(f"/ros_pub/global_position/odom_8", Odometry, self.odom_callback8, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        start_sub = time.time()
        sub9 = rospy.Subscriber(f"/ros_pub/global_position/odom_9", Odometry, self.odom_callback9, queue_size=10) 
        end_sub = time.time()
        print(f"Time taken to create ROS odom sub: {end_sub - start_sub:.6f} seconds")

        init_end_sub = time.time()
        print(f"Time taken to init all ROS odom sub: {init_end_sub - init_start_sub:.6f} seconds")
    
    def odom_callback0(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub0: ", time_taken.to_sec())
    def odom_callback1(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub1: ", time_taken.to_sec())
    def odom_callback2(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub2: ", time_taken.to_sec())
    def odom_callback3(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub3: ", time_taken.to_sec())
    def odom_callback4(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub4: ", time_taken.to_sec())
    def odom_callback5(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub5: ", time_taken.to_sec())
    def odom_callback6(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub6: ", time_taken.to_sec())
    def odom_callback7(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub7: ", time_taken.to_sec())
    def odom_callback8(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub8: ", time_taken.to_sec())
    def odom_callback9(self, msg):
        time_taken = rospy.Time.now() - msg.header.stamp
        print("End to End time taken for sub9: ", time_taken.to_sec())

    def shutdown_node(self):
        global global_polling
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    rospy.spin()