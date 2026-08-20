cmake_minimum_required(VERSION 3.0.2)
project(data_manager)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Release)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  std_msgs
  geometry_msgs
  nav_msgs
  tf
  tf2_ros
  tf2_sensor_msgs
  tf2_geometry_msgs
  pcl_ros
  pcl_conversions
  # livox_ros_driver2
  cv_bridge
)
find_package(OpenCV REQUIRED)
find_package(PCL REQUIRED)

include_directories(
  include
  ${catkin_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
  ${PCL_INCLUDE_DIRS}
)
link_directories(${PCL_LIBRARY_DIRS})
add_definitions(${PCL_DEFINITIONS})

generate_messages(
  DEPENDENCIES
  std_msgs
  # livox_ros_driver2
)

catkin_package(
  CATKIN_DEPENDS roscpp std_msgs cv_bridge
)

add_executable(data_manager src/data_manager.cpp)
target_link_libraries(data_manager ${catkin_LIBRARIES} ${PCL_LIBRARIES} )
