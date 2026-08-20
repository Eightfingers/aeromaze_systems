import rospy
from zmq_comms.msg import PositionCommand

def handle_position_command(msg: PositionCommand):
    rospy.loginfo(f"Received PositionCommand: x={msg.position.x}, y={msg.position.y}, z={msg.position.z}, yaw={msg.yaw}")

rospy.init_node('position_command_listener', anonymous=True)
rospy.Subscriber('position_command_topic', PositionCommand, handle_position_command)
rospy.loginfo("PositionCommand listener node started, waiting for messages...")
rospy.spin()
