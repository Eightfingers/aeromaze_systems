#!/usr/bin/env python

# Script to takes in NUS velocity and yaw setpoints
# And outputs them to mavros commands

import rospy
from mavros_msgs.msg import PositionTarget
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandBoolRequest, SetMode, SetModeRequest
from geometry_msgs.msg import TwistStamped
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String

from std_msgs.msg import Header


if __name__ == "__main__":
    rospy.init_node("pub_cmd_vel", anonymous=True)
    velocity_pub = rospy.Publisher("/planning/cmd_linear_vel_1", TwistStamped, queue_size=10)
    ros_msg = TwistStamped()
    ros_msg.header = Header()
    ros_msg.header.frame_id = "world"
    ros_msg.twist.linear.x = 4.0
    ros_msg.twist.linear.y = -1.1
    ros_msg.twist.linear.z = 5

    rate = rospy.Rate(20)

    # Enter Main Control Loop
    while not rospy.is_shutdown():
        ros_msg.header.stamp = rospy.Time.now()
        velocity_pub.publish(ros_msg)
        rate.sleep()
