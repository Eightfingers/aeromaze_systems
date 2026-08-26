alias tmuxes='tmux new-session \; set -g mouse on \; split-window -h \; split-window -v \; select-pane -t 0 \; split-window -v \; select-pane -t 2 \; split-window -v \; select-pane -t 4 \; split-window -v \; select-layout tiled'
 
alias brc='source ~/.bashrc'
alias reboot_px4='rosrun mavros mavcmd long 246 1 0 0 0 0 0 0'
alias rosbagrecordaeromaze='bash /home/emnavi/Aeromaze/Autonomy/aeromaze_systems.sh'
alias rosbaglivoxcamcalib='rosbag record /livox/lidar /livox/imu /cloud_registered_body /camera/color/camera_info /camera/color/image_raw'
 
#systems stuff
alias cdsys='cd /home/emnavi/Aeromaze/Autonomy/aeromaze_systems/'
alias up_sys_core='docker compose -f ~/Aeromaze/Autonomy/aeromaze_systems/ros1_core_ws/Docker/core_compose.yaml up'
alias up_sys_dev='docker compose -f ~/Aeromaze/Autonomy/aeromaze_systems/ros1_dev_ws/Docker/dev_compose.yaml up'
alias src.="source ~/.bashrc"
alias echo_local='rostopic echo /mavros/local_position/pose'
alias echo_vision='rostopic echo /mavros/vision_pose/pose'
 
