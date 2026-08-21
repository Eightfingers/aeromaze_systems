alias tmuxes='tmux new-session \; set -g mouse on \; split-window -h \; split-window -v \; select-pane -t 0 \; split-window -v \; select-pane -t 2 \; split-window -v \; select-pane -t 4 \; split-window -v \; select-layout tiled'
 
alias brc='source ~/.bashrc'
alias reboot_px4='rosrun mavros mavcmd long 246 1 0 0 0 0 0 0'
alias rosbaglivoxcamcalib='rosbag record /livox/lidar /livox/imu /cloud_registered_body /camera/color/camera_info /camera/color/image_raw'
alias rosbagrecordaeromaze='bash /home/emnavi/Aeromaze/record_aeromaze.sh'
 
#systems stuff
alias cdsyscompose='cd /home/emnavi/Aeromaze/Autonomy/Systems/ros1_ws'
alias up_sys_core='docker compose -f /home/emnavi/Aeromaze/Autonomy/Systems/ros1_ws/Docker/core_compose.yaml up'
alias up_sys_dev='docker compose -f /home/emnavi/Aeromaze/Autonomy/Systems/ros1_ws/Docker/dev_compose.yaml up'
alias src.="source ~/.bashrc"
alias echo_local='rostopic echo /mavros/local_position/pose'
alias echo_vision='rostopic echo /mavros/vision_pose/pose'
 
# signpost detection stuffs
alias signpost_docker_clean='docker ps -a --filter ancestor=signpostdetection:d2 -q | xargs -r docker rm' 
alias signpost_detect='docker run -it --rm --runtime nvidia --net=host --pid=host -e AGENT_ID=agent002 -e INFERENCE_RATE_LIDAR=5.0 -e INFERENCE_RATE=5.0 docker.io/hikashi1988/jetson-signpost-detection:apr03_ver'

