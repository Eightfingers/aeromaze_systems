#include <ros/ros.h>
#include <ros/master.h>

#include <sensor_msgs/PointCloud2.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/common/transforms.h>

#include "Eigen/Dense"
#include "Eigen/Geometry"
#include <Eigen/StdVector>
#include <pcl/io/io.h>
#include <signal.h>

#include "tf/transform_datatypes.h"

#include <nav_msgs/Odometry.h>

#include <iostream>
#include <string>
#include <cstdlib>

// Use manual transformations found in imu2lidar config. This script is the cut down version from the original data_manager.cpp 
// found in the original X280 package.

using namespace Eigen;
Eigen::Matrix4d extrinsic = Eigen::Matrix4d::Identity();

ros::Subscriber sub_uav_odom, sub_uav_pc;
ros::Publisher pub_odom_mavros, pub_global_world_pc;
bool odom_enabled=false;

bool topicExists(const std::string& topic_name)
{
    ros::master::V_TopicInfo master_topics;
    ros::master::getTopics(master_topics);
    for (auto& t : master_topics) {
        if (t.name == topic_name) return true;
    }
    return false;
}

void fastlioCallback(const nav_msgs::Odometry::ConstPtr& odom_msg)
{
    // 从里程计获取位姿
    Eigen::Quaterniond q(
        odom_msg->pose.pose.orientation.w,
        odom_msg->pose.pose.orientation.x,
        odom_msg->pose.pose.orientation.y,
        odom_msg->pose.pose.orientation.z
    );
    Eigen::Matrix3d rot = q.toRotationMatrix();
    Eigen::Vector3d trans(
        odom_msg->pose.pose.position.x,
        odom_msg->pose.pose.position.y,
        odom_msg->pose.pose.position.z
    );

    // 构造4x4变换矩阵
    Eigen::Matrix4d odom_transform = Eigen::Matrix4d::Identity();
    odom_transform.block<3,3>(0,0) = rot;
    odom_transform.block<3,1>(0,3) = trans;

    // 应用外参变换
    Eigen::Matrix4d odom_in_uav_world = extrinsic * odom_transform * extrinsic.inverse();

    // 提取变换后的旋转和平移
    Eigen::Matrix3d rot_new = odom_in_uav_world.block<3,3>(0,0);
    Eigen::Vector3d trans_new = odom_in_uav_world.block<3,1>(0,3);
    Eigen::Quaterniond q_new(rot_new);

    // 创建一个PoseStamped消息,用来输入 mavros 的 vision_pose 话题
    geometry_msgs::PoseStamped posestamp;
    posestamp.header.stamp = ros::Time::now();
    posestamp.header.frame_id = "uav_world";
    posestamp.pose.position.x =  trans_new.x();
    posestamp.pose.position.y =  trans_new.y();
    posestamp.pose.position.z =  trans_new.z();
    posestamp.pose.orientation.x =  q_new.x();
    posestamp.pose.orientation.y =  q_new.y();
    posestamp.pose.orientation.z =  q_new.z();
    posestamp.pose.orientation.w =  q_new.w();
    pub_odom_mavros.publish(posestamp);

    odom_enabled = true;
}

void cloudToUavWorldCallback(const sensor_msgs::PointCloud2::ConstPtr& input_msg)
{
    Eigen::Matrix4d transform = extrinsic;

    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*input_msg, *cloud);

    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud_transformed(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::transformPointCloud(*cloud, *cloud_transformed, transform);

    sensor_msgs::PointCloud2 output_msg;
    pcl::toROSMsg(*cloud_transformed, output_msg);
    output_msg.header = input_msg->header;
    output_msg.header.frame_id = "map";
    pub_global_world_pc.publish(output_msg);
}

ros::Time begin_time;
int main(int argc, char** argv)
{   
    ros::init(argc, argv, "data_manager");
    ros::NodeHandle nh;

    sub_uav_odom = nh.subscribe<nav_msgs::Odometry>("/fastlio_odometry", 10, fastlioCallback);
    sub_uav_pc = nh.subscribe<sensor_msgs::PointCloud2>("/cloud_registered", 10, cloudToUavWorldCallback);

    pub_global_world_pc = nh.advertise<sensor_msgs::PointCloud2>("/global_fastlio_pointcloud", 1000);
    pub_odom_mavros = nh.advertise<geometry_msgs::PoseStamped>("odom_mavros", 1000);
    begin_time=ros::Time::now(); 
    ros::Rate rate(10);

    // Get extrinsic_R and extrinsic_T
    std::vector<double> extrinsic_R, extrinsic_T;
    if (nh.getParam("imu2lidar/extrinsic_R", extrinsic_R) && nh.getParam("imu2lidar/extrinsic_T", extrinsic_T)) {
        if (extrinsic_R.size() == 9 && extrinsic_T.size() == 3) {
            Eigen::Matrix3d R;
            R << extrinsic_R[0], extrinsic_R[1], extrinsic_R[2],
                 extrinsic_R[3], extrinsic_R[4], extrinsic_R[5],
                 extrinsic_R[6], extrinsic_R[7], extrinsic_R[8];
            Eigen::Vector3d T(extrinsic_T[0], extrinsic_T[1], extrinsic_T[2]);
            extrinsic.setIdentity();
            extrinsic.block<3,3>(0,0) = R;
            extrinsic.block<3,1>(0,3) = T;
            ROS_INFO_STREAM("Loaded extrinsic:\n" << extrinsic);
        } else {
            ROS_WARN("imu2lidar/extrinsic_R or extrinsic_T size error");
        }
    } else {
        ROS_WARN("Cannot load imu2lidar/extrinsic_R or extrinsic_T from parameter server, using identity.");
    }

    // Wait for Mid360 to be online
    ROS_INFO("WAIT mid360 online...");
    while (ros::ok())
    {
        std::string full_topic = nh.resolveName("livox/lidar"); // Automatically complete namespaces, such as /x280_1/livox/lidar
        if (topicExists(full_topic)) {
            ROS_INFO("Mid360 online!");
            break;
        }

        ros::spinOnce(); 
        rate.sleep();
    }

    // Wait for fast-lio odom to be online
    ROS_INFO("WAIT fast-lio_odom");
    while(ros::ok())
    {
        if(odom_enabled==true){
            ROS_INFO("Fast-lio_odom online!");
            break;
        }

        ros::spinOnce(); 
        rate.sleep();
    }

    // All systems functional, let ros run
    ros::spin();
    return 0;
}
