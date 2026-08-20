#!/usr/bin/env python3

from geometry_msgs.msg import PoseStamped
import zmq
import rospy
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool
import threading
import time

global global_polling
global_polling = True

class ZMQCommsSub():

    def __init__(self):
        rospy.init_node('other_drone_odometry', anonymous=True)
        rospy.on_shutdown(self.shutdown_node)

        self.other_drone_pose_pub1 = rospy.Publisher("/other_drone1/global_position/pose", PoseStamped, queue_size=10)
        self.other_drone_odom_pub1 = rospy.Publisher("/other_drone1/global_position/odom", Odometry, queue_size=10)

        self.other_drone_pose_pub2 = rospy.Publisher("/other_drone2/global_position/pose", PoseStamped, queue_size=10)
        self.other_drone_odom_pub2 = rospy.Publisher("/other_drone2/global_position/odom", Odometry, queue_size=10)

        self.other_drone_pose_pub3 = rospy.Publisher("/other_drone3/global_position/pose", PoseStamped, queue_size=10)
        self.other_drone_odom_pub3 = rospy.Publisher("/other_drone3/global_position/odom", Odometry, queue_size=10)

        self.move_bool_pub = rospy.Publisher("/move_base_simple/goal_bool", Bool, queue_size=10)
        self.goal_pose_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=10)
        # self.goal_pose_pub = rospy.Publisher("/setpoint_goal/global/pose", PoseStamped, queue_size=10)

        # Set up the context and socket for subscribing
        self.context = zmq.Context() 
        
        self.goal_sub_socket = self.context.socket(zmq.SUB)
        self.goal_publisher_address = rospy.get_param('goal_publisher_address', "tcp://192.168.65.100:5555")
        print("Listening goal post at: " + self.goal_publisher_address)
        self.goal_sub_socket.connect(self.goal_publisher_address)
        self.goal_sub_socket.setsockopt_string(zmq.SUBSCRIBE, "GoalPose")

        # ZMQ subs to other sockets
        self.other_drone_zmq_sub_socket1 = self.context.socket(zmq.SUB)
        self.other_drone_address1 = rospy.get_param('other_drone_address1', "tcp://192.168.65.199:5555")
        # self.other_drone_zmq_sub_socket1.connect("tcp://192.168.65.132:5555")
        print("Listening to: " + self.other_drone_address1)
        self.other_drone_zmq_sub_socket1.connect(self.other_drone_address1)
        self.other_drone_zmq_sub_socket1.setsockopt_string(zmq.SUBSCRIBE, "Odometry")

        self.other_drone_zmq_sub_socket2 = self.context.socket(zmq.SUB)
        self.other_drone_address2 = rospy.get_param('other_drone_address2', "tcp://192.168.65.199:5555")
        # self.other_drone_zmq_sub_socket1.connect("tcp://192.168.65.132:5555")
        print("Listening to: " + self.other_drone_address2)
        self.other_drone_zmq_sub_socket2.connect(self.other_drone_address2)
        self.other_drone_zmq_sub_socket2.setsockopt_string(zmq.SUBSCRIBE, "Odometry")
        
        # Initialize poll set
        self.poller = zmq.Poller()
        self.poller.register(self.other_drone_zmq_sub_socket1, zmq.POLLIN)
        self.poller.register(self.other_drone_zmq_sub_socket2, zmq.POLLIN)
        self.poller.register(self.goal_sub_socket, zmq.POLLIN)
        rospy.loginfo("Finished init")

    def delayed_publish(self):
        time.sleep(1)
        self.move_bool_pub.publish(True)

    def poll_zmq_messages(self):
        if self.other_drone_zmq_sub_socket1.closed and self.goal_sub_socket.closed:
            rospy.loginfo("Socket is closed. Exiting poll loop.")
        else:
            try:
                socks = dict(self.poller.poll())

                if not socks:
                    # Sleep only if no sockets had data
                    # time.sleep(0.01)  # Light sleep to reduce CPU usage when idle
                    return

                for socket in [self.other_drone_zmq_sub_socket1, self.other_drone_zmq_sub_socket2, self.goal_sub_socket]:
                    if socket in socks:
                        serialized_msg = socket.recv()
                        # topic, serialized_data = serialized_msg.split(b" ", 1)  # Split by whitespace

                        # Identify which socket received the message
                        if socket == self.other_drone_zmq_sub_socket1:
                            topic, serialized_data = serialized_msg.split(b" ", 1)  # Split by whitespace
                            
                            other_drone_pose_deserialized_msg = PoseStamped()
                            other_drone_pose_deserialized_msg.deserialize(serialized_data)
                            self.other_drone_pose_pub1.publish(other_drone_pose_deserialized_msg)

                            odom_msg = Odometry()
                            odom_msg.pose.pose = other_drone_pose_deserialized_msg.pose
                            odom_msg.header = other_drone_pose_deserialized_msg.header
                            self.other_drone_odom_pub1.publish(odom_msg)

                        # Identify which socket received the message
                        elif socket == self.other_drone_zmq_sub_socket2:
                            topic, serialized_data = serialized_msg.split(b" ", 1)  # Split by whitespace
                            
                            other_drone_pose_deserialized_msg = PoseStamped()
                            other_drone_pose_deserialized_msg.deserialize(serialized_data)
                            self.other_drone_pose_pub2.publish(other_drone_pose_deserialized_msg)

                            odom_msg = Odometry()
                            odom_msg.pose.pose = other_drone_pose_deserialized_msg.pose
                            odom_msg.header = other_drone_pose_deserialized_msg.header
                            self.other_drone_odom_pub2.publish(odom_msg)

                        elif socket == self.goal_sub_socket:
                            topic, serialized_data = serialized_msg.split(b" ", 1)  # Split by whitespace
                            
                            goal_deserialized_msg = PoseStamped()
                            goal_deserialized_msg.deserialize(serialized_data)
                            self.goal_pose_pub.publish(goal_deserialized_msg)
                            threading.Thread(target=self.delayed_publish, daemon=True).start()
                            print("Recieved goal position x:{}, y:{}, z:{}".format(goal_deserialized_msg.pose.position.x, 
                                                                                   goal_deserialized_msg.pose.position.y, 
                                                                                   goal_deserialized_msg.pose.position.z))
            except zmq.error.ZMQError as e:
                print(f"ZMQ Error: {e}, most likely caused by socket is already closed")
                                

    def shutdown_node(self):
        global global_polling
        self.other_drone_zmq_sub_socket1.close() 
        self.other_drone_zmq_sub_socket2.close()

        self.other_drone_zmq_sub_socket1 = None 
        self.other_drone_zmq_sub_socket2 = None

        self.goal_sub_socket.close() 
        self.context.term() 
        self.poller.unregister(self.other_drone_zmq_sub_socket1)  # Unregister the socket
        self.poller.unregister(self.other_drone_zmq_sub_socket2)  # Unregister the socket
        self.poller.unregister(self.goal_sub_socket)  
        global_polling = False
        rospy.loginfo("Exiting!!!!")

if __name__ == '__main__':
    zmq_node = ZMQCommsSub()
    
    while global_polling:
        zmq_node.poll_zmq_messages()
