import rospy
from geometry_msgs.msg import TwistStamped

rospy.init_node('twist_stamped_publisher', anonymous=True)

rospy.loginfo("Twist Stamped publisher node started, waiting for messages...")
pub = rospy.Publisher('/planning/cmd_linear_vel_2', TwistStamped, queue_size=10)
rate = rospy.Rate(10)  # 1 Hz

while not rospy.is_shutdown():
    msg = TwistStamped()
    msg.twist.linear.x = 0.2
    msg.twist.linear.y = 0.0
    msg.twist.linear.z = 0.0
    msg.header.stamp = rospy.Time.now()
    msg.header.frame_id = "wtf"
    pub.publish(msg)
    rospy.loginfo(f"Published Velocity Command: x={msg.twist.linear.x}, y={msg.twist.linear.y}, z={msg.twist.linear.z}")
    rate.sleep()
