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
        start_node = time.time()
        rospy.init_node('other_drone_odometry', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)
        end_node = time.time()
        print(f"Time taken to create ROS node: {end_node - start_node:.6f} seconds")

        self.num_pub_sub_pairs = 10
        self.number_of_msgs_to_count = 200
        self.num_filled_up_sockets = 0

        # Initialize trackers 
        self.ros_total_time_taken = []
        self.ros_sub_init_time = []
        self.ros_msg_counter = []
        for i in range(self.num_pub_sub_pairs):
            self.ros_total_time_taken.append(0.0)
            self.ros_msg_counter.append(0) 

        # Setup a list of ros subs and making it strongly typed
        self.sub_odom_lists: List[rospy.Subscriber] = []
        start_sub_init = time.time()
        for i in range(self.num_pub_sub_pairs):
            start_sub = time.time()
            sub = rospy.Subscriber(f"/ros_pub/global_position/odom_{i}", Odometry, self.odom_callback, callback_args=i, queue_size=10) 
            end_sub = time.time()
            print(f"Time taken to create ROS odom sub{i}: {end_sub - start_sub:.6f} seconds")
            self.sub_odom_lists.append(sub)
            self.ros_sub_init_time.append(end_sub)
        end_sub_init = time.time()
        print(f"All ROS subs took : {end_sub_init - start_sub_init:.6f} seconds to create")

    def odom_callback(self, msg, agent_id):
        time_taken = rospy.Time.now() - msg.header.stamp
        self.ros_total_time_taken[agent_id] += time_taken.to_sec()
        self.ros_msg_counter[agent_id] += 1
        if (self.ros_msg_counter[agent_id] == self.number_of_msgs_to_count):
            avg_time = self.ros_total_time_taken[agent_id] / self.ros_msg_counter[agent_id]
            time_taken_to_fill_up = time.time() - self.ros_sub_init_time[agent_id]
            print(f"Average end to end time taken for sub{agent_id}: {avg_time:.6f} seconds and it took {time_taken_to_fill_up:.6f} seconds to fill up the socket.")
            self.num_filled_up_sockets += 1
            # Reset counters
            # self.ros_total_time_taken[agent_id] = 0.0
            # self.ros_msg_counter[agent_id] = 0
        if self.num_filled_up_sockets == self.num_pub_sub_pairs:
            rospy.signal_shutdown("All sockets have reached the limit.. shutting down node.")

        # print(f"End to End taken for sub{agent_id}: ", time_taken.to_sec())
                               
    def shutdown_node(self):
        global global_polling
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ExternalComms()
    rospy.spin()