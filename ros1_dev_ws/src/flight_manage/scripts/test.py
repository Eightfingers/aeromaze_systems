#!/usr/bin/env python

# Script to takes in NUS velocity and yaw setpoints
# And outputs them to mavros commands

import rospy
from mavros_msgs.msg import PositionTarget
from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, CommandBoolRequest, SetMode, SetModeRequest
from geometry_msgs.msg import TwistStamped
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Vector3
from std_msgs.msg import String, Int32
from quadrotor_msgs.msg import PositionCommand

from std_msgs.msg import Header
import math
import os, sys

## Parameters
TAKEOFF_HEIGHT = 1.2
SMALL_VEL_MAGNITUDE = 0.02
SMALL_VEL_AXIS = 0.15
POSITION_GAIN = 0.20

class AGENT_STATES:
    INIT = 1
    TAKING_OFF = 2
    HOVERING = 3
    LANDED = 4
    RUNNING = 5
    LANDING_TRIGGERED = 6
    LANDING = 7

class AgentStateManager:

    def __init__(self):
        self.input_commands = PositionTarget()
        self.hover_position_msg = PositionTarget()
        self.agent_pose = PoseStamped()
        self.yaw = 0.0
        self.agent_state = AGENT_STATES.INIT 
        self.px4_current_state = State()
        self.agent_id = int(os.environ['AGENT_ID'])
        self.velocity_action = Vector3()
        self.position_action = Vector3()
        self.publisher_ = self.create_publisher(Int32, '/my_topic', 10)

        print("Loading offsets from environment variables...")
        try:
            self.x_offset = float(os.environ['X_OFFSET'])
            self.y_offset = float(os.environ['Y_OFFSET'])
            self.z_offset = float(os.environ['Z_OFFSET'])
        except (ValueError, KeyError) as e:
            print("Invalid environment variables detected! Ensure that the .env file is loaded and contains valid float values!")
            sys.exit(1)

        # Flags
        self.px4_request_available_flag = False 
        self.recent_command_flag = False
        self.small_vel = False
        self.small_x_vel = False
        self.small_y_vel = False

        rospy.loginfo("Initializing control manager node...")
        rospy.init_node("agent_state_manager", anonymous=True)

        # Publishers
        self.setpoint_pub = rospy.Publisher("/mavros/setpoint_raw/local", PositionTarget, queue_size=10)

        # Subscribers
        self.action_sub_topic = "/agent00{}/action".format(self.agent_id) if self.agent_id < 10 else "/agent0{}/action".format(self.agent_id)
        self.action_sub = rospy.Subscriber(self.action_sub_topic, PositionCommand, self.command_callback)
        self.agent_state_sub = rospy.Subscriber("/drone_self/state", String, self.agent_state_callback)
        self.pose_sub = rospy.Subscriber("/mavros/local_position/pose", PoseStamped, self.pose_callback)
        self.state_sub = rospy.Subscriber("mavros/state", State, self.px4_state_cb)
        self.vel_vec3 = rospy.Publisher("veclocity_vector", Vector3, queue_size=10)
        self.pos_vec3 = rospy.Publisher("position_vector", Vector3, queue_size=10)

        # rospy.loginfo("Waiting for mavros services")
        # rospy.wait_for_service("/mavros/cmd/arming")
        self.arming_client = rospy.ServiceProxy("mavros/cmd/arming", CommandBool)

        # rospy.wait_for_service("/mavros/set_mode")
        self.set_mode_client = rospy.ServiceProxy("mavros/set_mode", SetMode)

        # Initialize velocity yaw PositionTarget msgs
        self.input_commands.header = Header()
        self.input_commands.header.frame_id ='drone_body'
        self.input_commands.coordinate_frame = PositionTarget.FRAME_LOCAL_NED
        # Type mask: Ignore everything except Velocity and YAW
        self.input_commands.type_mask = (
            PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
            # PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
            PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
            PositionTarget.IGNORE_YAW_RATE
        )
        self.input_commands.velocity.x = 0.0
        self.input_commands.velocity.y = 0.0
        self.input_commands.velocity.z = 0.0 
        self.input_commands.yaw = 0

        # Initialize position raw target msgs
        self.hover_position_msg.header = Header()
        self.hover_position_msg.header.frame_id ='drone_body'
        self.hover_position_msg.coordinate_frame = PositionTarget.FRAME_LOCAL_NED
        # Type mask: Ignore everything except position and YAW
        self.hover_position_msg.type_mask = (
            # PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
            PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
            PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
            PositionTarget.IGNORE_YAW_RATE
        )
        self.hover_position_msg.position.x = 0.0
        self.hover_position_msg.position.y = 0.0
        self.hover_position_msg.position.z = TAKEOFF_HEIGHT

        self.offb_set_mode = SetModeRequest()
        self.offb_set_mode.custom_mode = 'OFFBOARD'

        self.land_set_mode = SetModeRequest()
        self.land_set_mode.custom_mode = 'AUTO.LAND'

        self.arm_cmd = CommandBoolRequest()
        self.arm_cmd.value = True

        self.last_req = rospy.Time.now()
        self.land_timer = rospy.Time.now()
        self.last_valid_cmd = rospy.Time.now()

        # Loop Rate
        self.loop_rate = 40
        self.log_period = 50
        self.log_ticker = 0
        ros_rate = rospy.Rate(self.loop_rate)

        # START OF INIT CODE
        rospy.loginfo("Sending dummy setpoints before arming")
        for i in range(100):
            if(rospy.is_shutdown()):
                break
            self.setpoint_pub.publish(self.hover_position_msg)
            ros_rate.sleep()
        rospy.loginfo("Finished sending dummy setpoings")
        rospy.loginfo("Initiaizing Finished")

        # Enter Main Control Loop
        while not rospy.is_shutdown():
            self.check_conditional_flags()
            self.print_stats()

            # Reset mask to velocity by default
            self.input_commands.type_mask = (
                PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
                # PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
                PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
                PositionTarget.IGNORE_YAW_RATE
            )

            # State Machine
            if (self.agent_state == AGENT_STATES.TAKING_OFF):
                if(self.px4_current_state.mode != "OFFBOARD" and self.px4_request_available_flag):
                    if(self.set_mode_client.call(self.offb_set_mode).mode_sent == True):
                        rospy.loginfo("OFFBOARD enabled")
                        self.last_req = rospy.Time.now()
                    else:
                        rospy.logwarn("OFFBOARD enable failed!!!")

                elif(self.px4_current_state.mode == "OFFBOARD" and not self.px4_current_state.armed and self.px4_request_available_flag):
                    if(self.arming_client.call(self.arm_cmd).success == True):
                        rospy.loginfo("Vehicle armed")
                        self.last_req = rospy.Time.now()
                    else:
                        rospy.logwarn("Vehicle arming failed!!!")

                self.hover_position_msg.position.x = self.agent_pose.pose.position.x
                self.hover_position_msg.position.y = self.agent_pose.pose.position.y
                self.hover_position_msg.position.z = TAKEOFF_HEIGHT
                self.setpoint_pub.publish(self.hover_position_msg)
                if self.check_takeoff_finished():
                    rospy.loginfo("Takeoff finished detected!")
                    self.agent_state = AGENT_STATES.HOVERING

            elif (self.agent_state == AGENT_STATES.HOVERING):
                self.hover_position_msg.yaw = self.input_commands.yaw
                self.setpoint_pub.publish(self.hover_position_msg)
                if  (self.recent_command_flag and not self.small_vel ):
                    rospy.loginfo("Recieved a RECENT ENOUGH and VALID velocity command, switching to RUNNING state")
                    self.agent_state = AGENT_STATES.RUNNING
                else:
                    pass
                    # rospy.loginfo("Waiting for VALID or RECENT ENOUGH velocity commands to switch to RUNNING state")

            elif (self.agent_state == AGENT_STATES.RUNNING):
                self.update_hover_position()

                if (self.small_y_vel):
                    # Enable Velocity Pos Mode to compensate for small y velocity
                    # rospy.loginfo("Small Y Velocity detected! ")
                    self.input_commands.type_mask = ( 
                        # PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
                        # PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
                        PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
                        PositionTarget.IGNORE_YAW_RATE
                    )
                    self.input_commands.position.y = self.input_commands.position.y + POSITION_GAIN * self.input_commands.velocity.y 

                elif (self.small_x_vel):
                    # Enable Velocity Pos Mode to compensate for small x velocity
                    # rospy.loginfo("Small X Velocity detected!")
                    self.input_commands.type_mask = ( 
                        # PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
                        # PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
                        PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
                        PositionTarget.IGNORE_YAW_RATE
                    )
                    self.input_commands.position.x = self.input_commands.position.x + POSITION_GAIN * self.input_commands.velocity.x 

                if (self.small_y_vel and self.small_x_vel):
                    # Enable Velocity Pos Mode to compensate for small x and y velocity
                    self.input_commands.type_mask = ( 
                        # PositionTarget.IGNORE_PX | PositionTarget.IGNORE_PY | PositionTarget.IGNORE_PZ |
                        # PositionTarget.IGNORE_VX | PositionTarget.IGNORE_VY | PositionTarget.IGNORE_VZ |
                        PositionTarget.IGNORE_AFX | PositionTarget.IGNORE_AFY | PositionTarget.IGNORE_AFZ |
                        PositionTarget.IGNORE_YAW_RATE
                    )
                    self.input_commands.position.x = self.input_commands.position.x + (POSITION_GAIN/2) * self.input_commands.velocity.x 
                    self.input_commands.position.y = self.input_commands.position.y + (POSITION_GAIN/2) * self.input_commands.velocity.y 

                # rospy.loginfo("Velocity, X: {}, Y: {}, Z: {} -- Yaw: {}".format(self.input_commands.velocity.x, self.input_commands.velocity.y, self.input_commands.velocity.z, self.input_commands.yaw))
                if (self.recent_command_flag):
                    self.input_commands.position.z = TAKEOFF_HEIGHT
                    self.setpoint_pub.publish(self.input_commands)
                else:
                    self.agent_state = AGENT_STATES.HOVERING 
                    rospy.loginfo("Going back to Hovering state- No valid velocity commands received recently")
            elif (self.agent_state == AGENT_STATES.LANDING_TRIGGERED):
                if(self.set_mode_client.call(self.land_set_mode).mode_sent == True):
                    rospy.loginfo("LANDING_TRIGGERED mode called")
                    self.agent_state = AGENT_STATES.LANDING
                else:
                    rospy.loginfo("THIS SHOULD NOT HAPPEN-- FAILED TO CALL PX4 AUTO.LAND!!!")
            elif (self.agent_state == AGENT_STATES.LANDING):
                # Do nothing- PX4 handles the landing
                pass
            ros_rate.sleep()

    def command_callback(self, data):
        self.input_commands.velocity.x = data.velocity.x
        self.input_commands.velocity.y = data.velocity.y
        self.input_commands.velocity.z = data.velocity.z

        self.input_commands.position.x = data.position.x - self.x_offset
        self.input_commands.position.y = data.position.y - self.y_offset
        self.input_commands.position.z = data.position.z - self.z_offset

        self.input_commands.yaw = data.yaw
        self.last_valid_cmd = data.header.stamp

        self.velocity_action.x = data.velocity.x
        self.velocity_action.y = data.velocity.y
        self.velocity_action.z = data.velocity.z

        self.position_action.x = data.position.x
        self.position_action.y = data.position.y
        self.position_action.z = data.position.z
        rospy.loginfo("Velocity action.x {}".format(self.velocity_action.x))
        self.vel_vec3.publish(self.velocity_action)
        self.pos_vec3.publish(self.position_action)

    def pose_callback(self, data):
        self.agent_pose = data

    def px4_state_cb(self, data):
        self.px4_current_state = data

    def agent_state_callback(self, data):
        self.agent_state = int(data.data) 
        rospy.loginfo("Agent state callback triggered: {}".format(self.agent_state))

    def check_conditional_flags(self):
            # Ensure enough time has passed between subsequent PX4 requests
            self.px4_request_available_flag = (rospy.Time.now() - self.last_req) > rospy.Duration(5.0)
            # Ensure that command to be sent is recent enough
            self.recent_command_flag = rospy.Time.now() - self.last_valid_cmd < rospy.Duration(1.0)

            # Check for small vel
            vx = self.input_commands.velocity.x
            vy = self.input_commands.velocity.y
            vz = self.input_commands.velocity.z
            # Calculate magnitude
            magnitude = math.sqrt(vx**2 + vy**2 + vz**2)
            if (magnitude < SMALL_VEL_MAGNITUDE and self.agent_state == AGENT_STATES.RUNNING):
                self.agent_state = AGENT_STATES.HOVERING
                self.small_vel = True
            else:
                self.small_vel = False

            # Check which axis has smaller velocities
            if (vx < SMALL_VEL_AXIS):
                self.small_x_vel = True
            else:
                self.small_x_vel = False
            if (vy < SMALL_VEL_AXIS):
                self.small_y_vel = True
            else:
                self.small_y_vel = False

    def print_stats(self):
        self.log_ticker += 1
        if (self.log_ticker == self.log_period): 
            self.log_ticker = 0
            rospy.loginfo("PX4_STATE: {}, ARMED_STATE: {}, AGENT_STATE: {}".format(self.px4_current_state.mode, self.px4_current_state.armed, self.agent_state))
            rospy.loginfo("Velocity, X: {}, Y: {}, Z: {} -- Yaw: {}".format(self.input_commands.velocity.x, self.input_commands.velocity.y, self.input_commands.velocity.z, self.input_commands.yaw))
            if (self.small_y_vel):
                rospy.loginfo("Small Y Velocity detected! ")
            if (self.small_x_vel):
                rospy.loginfo("Small X Velocity detected!")
            if (not self.recent_command_flag and not self.small_vel and self.agent_state == AGENT_STATES.HOVERING):
                rospy.loginfo("Hovering... Waiting for VALID or RECENT ENOUGH velocity commands to switch to RUNNING state")
        self.publisher_.publish(self.agent_state)
    
    def check_takeoff_finished(self):
        return self.agent_pose.pose.position.z >= 0.90 * TAKEOFF_HEIGHT

    def update_hover_position(self):
        self.hover_position_msg.position.x = self.agent_pose.pose.position.x
        self.hover_position_msg.position.y = self.agent_pose.pose.position.y
        self.hover_position_msg.position.z = self.agent_pose.pose.position.z

if __name__ == "__main__":
    try:
        AgentStateManager()
    except rospy.ROSInterruptException:
        print("ROS Interrupt Exception caught- This should not happen!!! ")
        pass

