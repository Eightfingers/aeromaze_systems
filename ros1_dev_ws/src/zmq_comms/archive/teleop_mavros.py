#!/usr/bin/env python
import rospy

from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseWithCovarianceStamped
from mavros_msgs.msg import PositionTarget

import sys, select, termios, tty
import tf
import numpy as np
from std_msgs.msg import Header

msg = """
WASD based position controller!

---------------------------
Moving around:
        w     
    a   s    d
Yawing around:
q, e
q/e : Yaw anti-clockwise / Yaw clock wise
q/z : increase/decrease increment by 0.1
w/s : Forward/ backward by speed amount +/-(y) 
a/d : Left/right by speed amount only angular speed by 10% +/-(x) 
t/b : Go up or go down +/-(z) 
anything else : stop smoothly
CTRL-C to quit
"""

moveBindings = {
        'w':(1,0,0),
        's':(-1,0,0),
        'a':(0,1,0),
        'd':(0,-1,0),
        't':(0,0,1),
        'b':(0,0,-1),
           }

speedBindings={
        'p':(0.1),
        'l':(-0.1),
          }

yawBindings={
        'q':(1), # Positive yaw 
        'e':(-1), # Negative yaw
          }

uav1_input_topic = "/uav1/input_pose_stamped"
uav2_input_topic = "/uav2/input_pose_stamped"

def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def print_pos_speed(speed, x, y, z, yaw):
    # print("Speed:{speed}, X:{x} Y:{y} Z:{z}".format(speed, x, y, z))
    print("Speed:{}, x:{}, y:{}, z:{} yaw:{}".format(speed, x, y, z, yaw))

if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin)
    rospy.init_node('borealis_teleop')
    uav1_input_pub = rospy.Publisher(uav1_input_topic, PoseStamped, queue_size=5)
    uav2_input_pub = rospy.Publisher(uav2_input_topic, PoseStamped, queue_size=5)

    # Publishers
    setpoint_pub = rospy.Publisher("/mavros/setpoint_raw/local", PositionTarget, queue_size=10)



    position_msg = PositionTarget()
        # Initialize position setpoints msgs
    position_msg.header = Header()
    position_msg.header.frame_id ='drone_body'
    position_msg.coordinate_frame = PositionTarget.FRAME_LOCAL_NED
    # Type mask: Ignore everything except position and YAW
    position_msg.type_mask = (
        PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
        PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
        # PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
        PositionTarget.IGNORE_YAW_RATE | PositionTarget.IGNORE_YAW
    )
    position_msg.position.x = 0.0
    position_msg.position.y = 0.0
    position_msg.position.z = 1.0  # Take off height

    rate = rospy.Rate(20) 
    try:
        x = 0
        y = 0
        z = 0
        roll = 0
        pitch = 0
        yaw = 0
        status = 0
        count = 0
        speed = 0.1
        speed_scale_factor = 10 # used in yaw determination

        print(msg)
        print_pos_speed(x, y, z, speed, yaw)

        while(1):
            key = getKey()
            if key in moveBindings.keys():
                direction_x = moveBindings[key][0]
                direction_y = moveBindings[key][1]
                direction_z = moveBindings[key][2]

                x += speed * direction_x
                y += speed * direction_y
                z += speed * direction_z
                print_pos_speed(speed, x, y, z, yaw)

            elif key in speedBindings.keys():
                speed_increment = speedBindings[key]
                speed += speed_increment
                print_pos_speed(speed, x, y, z, yaw)

            elif key in yawBindings.keys():
                yaw_direciton = yawBindings[key]
                yaw += speed * yaw_direciton * speed_scale_factor
                if yaw == 0:
                    yaw = 360

                print_pos_speed(speed, x, y, z,yaw)
            else:
                if (key == '\x03'):
                    print("Stopping teleop!")
                    break

            position_msg.position.x = 0.0
            position_msg.position.y = -3.0
            position_msg.position.z = 1.0
            position_msg.velocity.x = 0.0
            position_msg.velocity.y = -0.1
            quaternion = tf.transformations.quaternion_from_euler(roll, pitch, np.deg2rad(yaw))
            setpoint_pub.publish(position_msg)

            rate.sleep()

    except Exception as e:
        print(e)

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)