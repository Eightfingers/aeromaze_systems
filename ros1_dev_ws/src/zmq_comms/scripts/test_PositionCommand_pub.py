import rospy
from quadrotor_msgs.msg import PositionCommand

rospy.init_node('position_command_publisher', anonymous=True)

rospy.loginfo("PositionCommand publisher node started, waiting for messages...")
pub = rospy.Publisher('agent001/action', PositionCommand, queue_size=10)
rate = rospy.Rate(10)  # 1 Hz

while not rospy.is_shutdown():
    msg = PositionCommand()
    # msg.position.x = 1.0
    # msg.position.y = 2.0
    # msg.position.z = 3.0
    msg.velocity.x = 0.2
    msg.velocity.y = 0.0
    msg.velocity.z = 0.0
    pub.publish(msg)
    rospy.loginfo(f"Published Velocity Command: x={msg.velocity.x}, y={msg.velocity.y}, z={msg.velocity.z}, yaw={msg.yaw}")
    rate.sleep()
