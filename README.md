# Aeromaze Systems 

The base Aeromaze systems consist of two docker images that provides basic autonomy functionalities of the X280 drone: This includes, localization, comms, flight management, visualization and bridging nodes. 

# Quick Start

2 bash aliases has been set up on the drone to provide a quick one way command to start the docker compose files. To run everything simply type the following commands (:

1) `roscore` (Start roscore first, to specifically pin roscore to a terminal)
2) `up_sys_core` (Start the core of the system)
3) `up_sys_dev` (Start the development part of the system)

# Install

To install simply do a docker image pull: 

1) for the core image: `docker image pull eightfingers123/aeromaze_systems_core:arm64 `
2) for the dev image : `docker image pull eightfingers123/aeromaze_systems_dev:arm64`

 The `arm64` tag is used to indicate its the `arm64` build, which is deployable on the arm64 architecture jetson based drone. There is a `latest` tag, which is using the conventional x86 cpu architecture such that the images can be run on a conventional desktop setup.

# First time set up 

You can use Ansible to help you out (?) or you can just yolo and install the stuff one by one

# Overview

## Hardware 

Onboard computer: Jetson Orin NX 16GB on Ubuntu20.04 LTS with PX4. 

FCU: Pixhawk 6C (drone 1, 4 5 6 ). NXTpx4v2 for 2 3. Check Master list

Sensors: Livox-Mid-360,  RealSense D455

 username and password: ask the guys 

comms: Using onboard Wifi-chip , switched to IBSS mode.

## Bash scripts

- bash_aliases: A file containing bash aliases to easily run the docker images stuff.
- ibss-batman-setup.sh: Switch to IBSS networking and start BATMAN networking routing. This will disconnect itself from the current Wifi network.
- ibss-batman-teardown.sh: Stop IBSS and BATMAN and start back normal networking services
- ibss-setup.sh: Start up IBSS networking only. This will disconnect itself from the current Wifi network.
- launch_realsense.sh: Quick bash script to launch real-sense with a specific config. 

## Docker as a deployment mechanism

Since we expected to deploy on 10 drones, it was decided to use Docker as it helps with code deployment and code isolation amongst the different developers. As as side note this incurred some time costs in terms of development (Cross image Compilation and on the spot code adjustment is tricky).

## Docker images

The core and dev division refers to the state development work of the code. Core refers to using publicly available standard ROS based open source code, while dev refers to development work that was done in house. This is also based on the completeness of the module (i.e the likelihood of the module's code to change). There are 6 containers: 

- Core - MAVROS, Lidar Driver, FAST-LIO

- Dev - Communications, Data Manager, Flight Manage.

## Updating

To update, simply `git pull` to get the latest script / config folder from github. To update the images simply `docker pull <image name>` .  

## Systems Core Image

Based on arm64v8 ros noetic image. They are grouped together as they are pretty much stable open source code, therefore minimal changes is expected towards them. Check the Dockerfile for more information about the git-hub links to the github opensource codes / apt install instructions to build the image. 

It consist of:

- MAVROS Noetic (ROS and FCU bridge for controls of the drone)
- Livox MID360 Lidar ROS driver (ROS drier for Livox MID 360 lidar)
- FAST-LIO (Drone Odometry source)
- ros1_core_ws (A ros workspace, you can **ignore** the contents inside src its basically archive / placeholder and unused). Only take note of the Docker folder underneath it which contains all of the necessary scripts and configs of the core system.

### Core Mounted Docker folder and call hierarchy.

Running `up_sys_core` is pretty much an alias for the docker compose command. This will mount two the folders, core_configs and core_scripts, from the ros1_core_ws. The call hierarchy is as follows: 

`docker compose up --> entrypoint.sh (bash script) --> core.launch (roslaunch) --> mapping_mid360.launch, msg_MID360.launch (roslaunch the rest of the nodes)`

`entrypoint.sh`  might be removed in the future and instead replaced with a direct bash `roslaunch` command to called from docker compose yaml file.

## Systems-Dev image

Also based on arm64v8 ros:noetic image.

It consist of:

- Comms (Responsible for sending positional data to other agents).
- Flight Manage (UAV state taking off, hovering and landing).
- Data manager (Responsible for transforming fast-lio odom frame into )

These modules are grouped together cause they are they are developed in house unlike core modules which consist of mainly stable open source code.

https://community.intel.com/t5/Wireless/Frequent-Scan-fails-during-IBSS-mode-on-Ubuntu-20-04-and-Wi-Fi-6/m-p/1746639

https://forums.developer.nvidia.com/t/nvidia-orin-nx-boot-stuck-at-i-tc-secondary-cpu-11-switching-to-normal-world-boot/363126

https://forum.modalai.com/topic/3953/setting-up-voxl2-microdds-communication-with-px4/8
