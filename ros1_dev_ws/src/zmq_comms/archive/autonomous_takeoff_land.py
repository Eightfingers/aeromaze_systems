"""
 * File: offb_node.py
 * Stack and tested in Gazebo Classic 9 SITL
"""

#! /usr/bin/env python

# Autonomous take off and land script using MAVROS offboard mode
# Taken from https://github.com/TareqAlqutami/px4_offboard_ros/blob/master/scripts/offboard_test_node.py
# https://docs.px4.io/main/en/ros/mavros_offboard_python 

# Drone needs to ARM, OFFBOARD, TAKEOFF , HOKVER, RUNNING (TAKING IN INPUT FROM NUS VELOCITY COMMANDS), LAND

import rospy
from geometry_msgs.msg import PoseStamped
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandBoolRequest, SetMode, SetModeRequest

class AGENT_STATES:
    INIT = 1
    LANDED = 2 
    TAKING_OFF = 3 
    HOVERING = 4 
    FLYING = 5
    LANDING = 6

px4_current_state = State()

def state_cb(msg):
    global px4_current_state
    px4_current_state = msg
    rospy.loginfo("PX4_STATE: {}".format(px4_current_state.mode))

if __name__ == "__main__":
    land = False
    current_agent_state = AGENT_STATES.INIT

    rospy.init_node("offb_node_py")

    state_sub = rospy.Subscriber("mavros/state", State, callback = state_cb)

    local_pos_pub = rospy.Publisher("mavros/setpoint_position/local", PoseStamped, queue_size=10)

    rospy.wait_for_service("/mavros/cmd/arming")
    arming_client = rospy.ServiceProxy("mavros/cmd/arming", CommandBool)

    rospy.wait_for_service("/mavros/set_mode")
    set_mode_client = rospy.ServiceProxy("mavros/set_mode", SetMode)

    # Setpoint publishing MUST be faster than 2Hz
    rate = rospy.Rate(50)

    # Wait for Flight Controller connection
    rospy.loginfo("Waiting for FCU connection...")
    while(not rospy.is_shutdown() and not px4_current_state.connected):
        rate.sleep()

    rospy.loginfo("FCU connection established")

    pose = PoseStamped()

    pose.pose.position.x = 0
    pose.pose.position.y = 0
    pose.pose.position.z = 2

    # Send a few setpoints before starting
    rospy.loginfo("Sending dummy setpoints")
    for i in range(100):
        if(rospy.is_shutdown()):
            break
        local_pos_pub.publish(pose)
        rate.sleep()

    rospy.loginfo("Finished sending dummy setpoints")

    offb_set_mode = SetModeRequest()
    offb_set_mode.custom_mode = 'OFFBOARD'

    land_set_mode = SetModeRequest()
    land_set_mode.custom_mode = 'AUTO.LAND'

    arm_cmd = CommandBoolRequest()
    arm_cmd.value = True

    last_req = rospy.Time.now()
    land_timer = rospy.Time.now()

    while(not rospy.is_shutdown()):
        request_available_flag = (rospy.Time.now() - last_req) > rospy.Duration(5.0)

        if (not land):
            if(px4_current_state.mode != "OFFBOARD" and request_available_flag):
                if(set_mode_client.call(offb_set_mode).mode_sent == True):
                    rospy.loginfo("OFFBOARD enabled")
                last_req = rospy.Time.now()
            elif(px4_current_state.mode == "OFFBOARD" and not px4_current_state.armed and request_available_flag):
                    if(arming_client.call(arm_cmd).success == True):
                        rospy.loginfo("Vehicle armed")
                    last_req = rospy.Time.now()

            if(px4_current_state.mode == "OFFBOARD" and (rospy.Time.now() - land_timer) > rospy.Duration(30.0)):
                land = True
                if(set_mode_client.call(land_set_mode).mode_sent == True):
                    rospy.loginfo("LANDING mode called")

            local_pos_pub.publish(pose)
        else: 
            if ((rospy.Time.now() - land_timer) > rospy.Duration(60.0)):
                break 

        rate.sleep()