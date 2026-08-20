#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import PoseStamped

class FollowScript:
    def __init__(self):
        rospy.init_node('pose_mavros_setpoint_pub', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        self.other_drone_pose_sub = rospy.Subscriber('/other_drone/global_position/pose', PoseStamped, self.other_pose_callback)
        self.mavros_setpoint_pub = rospy.Publisher("/mavros/setpoint_position/local", PoseStamped, queue_size=10)
        rospy.loginfo("Init finished")

    
    def other_pose_callback(self, msg):
        msg.pose.position.x += 2
        msg.pose.position.z = 2 
        # rospy.loginfo("Publishing local position setpoint")
        self.mavros_setpoint_pub.publish(msg)

    def shutdown_node(self):
        rospy.loginfo("Shutting down self mavros_setpoint_pub")

if __name__ == "__main__":
    node = FollowScript()
    rospy.spin()
