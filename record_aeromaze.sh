#!/bin/bash

AGENT_ID="${AGENT_ID}"

# Record topics using the variable
rosbag record \
  /agent${AGENT_ID}/detection_results \
  /agent${AGENT_ID}/detection_results_raw \
  /agent001/global_position/pose \
  /agent${AGENT_ID}/global_position/odom \
  /agent${AGENT_ID}/global_position/pose \
  /agent003/global_position/pose \
  /agent${AGENT_ID}/grid_map/occupancy \
  /agent${AGENT_ID}/grid_map/occupancy_highres \
  /agent${AGENT_ID}/plan_array \
  /agent${AGENT_ID}/string \
  /agent${AGENT_ID}/waypoint \
  /drone_self/offset_pose \
  /fastlio_odom \
  /camera/color/image_raw_throttled \
  /cpu_monitor/total_cpu \
  /livox/lidar \
  /livox/imu \
  /mavros/imu/data \ 
  /mavros/imu/data_raw \
  /realsense_lidar_detection_viz/detection_image \
  /veclocity_vector \
  /position_vector \
  /control_manager_state \
  /mavros/setpoint_raw/local \
  /mavros/local_position/pose \
  /mavros/vision_pose/pose \
  /mavros/local_position/velocity_local \
  /agent${AGENT_ID}/action \
  /agent${AGENT_ID}/pva_action \
  /agent${AGENT_ID}/linear_acceleration \
  /agent${AGENT_ID}/linear_velocity \
  /tf \
  /tf_static
