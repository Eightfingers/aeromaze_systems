# Aeromaze Systems Guide

Onboard computer: Jetson Orin NX 16GB on Ubuntu20.04 LTS

FCU: 

Aeromaze is a challenge that requires drones navigating in an unknown outdoor/indoor environment, with the goal of finding objects of interest / exploring the entire environment. More details could be found in the challenge booklet / briefing slides.

The Systems refers to a collection of ROS nodes that can be categorized as: 

- Core - MAVROS, Lidar Driver, FAST-LIO, , Data Manager.
- Dev - Communications and Flight Manage.

This division is based on the completeness of the module (i.e the likelihood of the module's code to change). This division is also reflected on their respective **Docker Images**: dev and core.

# Docker as a deployment mechanism

Since we are deploying on 10 drones, it was decided to use Docker as it helps with code deployment and code isolation amongst the different developers. As as side note this incurred some time costs in terms of development (Cross image Compilation and on the spot code adjustment is tricky).

# Systems-Core Image

Based on arm64v8 ros noetic image.

It consist of:

- MAVROS Noetic (ROS and FCU bridge for controls of the drone)
- Livox MID360 Lidar ROS driver (ROS drier for Livox MID 360 lidar)
- FAST-LIO (Drone Odometry source)
- Data Manager (Manually transforms the FAST-LIO Odom to ENU frame and also provides the TF tree)

They are grouped together as they are pretty much stable open source code, except for the Data Manager module which is developed internally. Therefore minimal changes is expected towards them.

# System-Dev Image

Based on arm64v8 ros noetic image.

It consist of:

- Comms (Responsible for sending positional data to other agents).
- Flight Manage (UAV state taking off, hovering and landing).

These modules are grouped together cause they are they are constantly being developed.

# Docker Folder

The Docker Folder contains all of the compose.yaml files. The core_configs folder contains all of the yaml files that is used by roslaunch to set rosparams. It also contains the MID360 lidar configuration.json file, which configures the mid360 lidar ip addresses.

# Core

The core_scripts contains all of the launch files for the core modules and bash scripts that is called by docker compose file. 

	<include file="/root/scripts/px4.launch"/> 
	<include file="/root/scripts/msg_MID360.launch"/>  
	<include file="/root/scripts/mapping_mid360.launch"/>
	<include file="/root/scripts/data_manager_start.launch"/>

The flows goes something like this.

core_compose.yaml -> bash scripts -> ros launch -> loads param files.

The env folder contains all of the environment files for each of the drones. 

# Dev 

The dev folder contains the data manager module, flight manage module and the zmq_comms module.

All of the modules are written in Python. 

The flight manage main control loop consist of the following steps:

1) Check conditional flags (i.e. check the timestamps of recent commands received by callbacks that was sent was recent enough and has a big enough magnitude.).
2) Reset bit mask to accept all other commands and ignore yaw rate.
3) Enter State Machine logic which checks for:
   1) Taking Off
   2) Hovering 
   3) Running
   4) Landing
4) The state machine logic is driven by the conditional flags (that is triggered by the command input callback) and agent state callback (controls taking off and landing).


The communications module is divided into zmq subscriber and zmq publisher modules.

The zmq subscriver listens to ROS Odom messages from other drones and republishes it as a ros topic.  It is listening at tcp port agent_ip:5555.  It has a main loop that polls the zmq poller for incoming data.

Agent index logic.

Offset logic.

Delayed Taking off logic.

A chance of the network not working if there is a high ping issue. 

  

The zmq publisher is  simpler in structure. It is callback driven. Everything a ROS msg comes in the callback, it forwards it to the ZMQ publisher socket, which would then forward it to all subscribers that are listening attached the socket. 

# On First Boot



