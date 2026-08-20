#include <ros/ros.h>
#include <ros/master.h>

#include <sensor_msgs/PointCloud2.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/common/transforms.h>

#include "Eigen/Dense"
#include "Eigen/Geometry"
#include <geometry_msgs/PoseStamped.h>
#include <nav_msgs/Odometry.h>

#include <iostream>
#include <string>
#include <cstdlib>
#include <tf2_ros/transform_broadcaster.h>
#include <geometry_msgs/TransformStamped.h>

using namespace Eigen;
Eigen::Matrix4d extrinsic = Eigen::Matrix4d::Identity();

ros::Subscriber sub_uav_odom, sub_uav_pc;
ros::Publisher pub_odom_mavros, pub_global_world_pc;
bool odom_enabled=false;

Eigen::Quaterniond initial_bias;
std::unique_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster;

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

    // Obtain initial bias
    if (!odom_enabled){
        ROS_INFO("Fast-lio_odom online!");
        initial_bias = q;
        odom_enabled = true;
    }

    // Re-orientate and publish to mavros
    Eigen::Isometry3d T = Eigen::Isometry3d::Identity();
    T.linear() = initial_bias.toRotationMatrix();

    Eigen::Isometry3d T_odom = Eigen::Isometry3d::Identity();
    T_odom.linear() = q.toRotationMatrix();
    T_odom.translation() = Eigen::Vector3d(odom_msg->pose.pose.position.x, odom_msg->pose.pose.position.y, odom_msg->pose.pose.position.z);

    Eigen::Isometry3d T_new = T.inverse() * T_odom;

    geometry_msgs::PoseStamped posestamp;
    posestamp.header.stamp = ros::Time::now();
    posestamp.header.frame_id = "map";
    posestamp.pose.position.x = T_new.translation().x();
    posestamp.pose.position.y = T_new.translation().y();
    posestamp.pose.position.z = T_new.translation().z();

    Eigen::Quaterniond q_new(T_new.linear());
    posestamp.pose.orientation.x = q_new.x();
    posestamp.pose.orientation.y = q_new.y();
    posestamp.pose.orientation.z = q_new.z();
    posestamp.pose.orientation.w = q_new.w();

    // posestamp.header.stamp = ros::Time::now();
    // posestamp.header.frame_id = "odom";
    // posestamp.pose = odom_msg->pose.pose;
    // posestamp.pose.position.y = -odom_msg->pose.pose.position.y;
    // posestamp.pose.position.x = -odom_msg->pose.pose.position.x;
    // Now remove the initial bias
    // Eigen::Quaterniond q_new = initial_bias.inverse() * q;
    // Eigen::Quaterniond q_new =  q;
    // posestamp.pose.orientation.x = q_new.x();
    // posestamp.pose.orientation.y = q_new.y();
    // posestamp.pose.orientation.z = q_new.z();
    // posestamp.pose.orientation.w = q_new.w();

    pub_odom_mavros.publish(posestamp);

    // Publish TF base link
    // geometry_msgs::TransformStamped tf_msg;
    // tf_msg.header.stamp = posestamp.header.stamp;
    // tf_msg.header.frame_id = "odom";
    // tf_msg.child_frame_id = "base_link";

    // tf_msg.transform.translation.x = posestamp.pose.position.x;
    // tf_msg.transform.translation.y = posestamp.pose.position.y;
    // tf_msg.transform.translation.z = posestamp.pose.position.z;

    // tf_msg.transform.rotation.x = q_new.x();
    // tf_msg.transform.rotation.y = q_new.y();
    // tf_msg.transform.rotation.z = q_new.z();
    // tf_msg.transform.rotation.w = q_new.w();
    
    // tf_broadcaster->sendTransform(tf_msg);
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
    output_msg.header.frame_id = "odom";
    pub_global_world_pc.publish(output_msg);
}

ros::Time begin_time;
int main(int argc, char** argv)
{   
    ros::init(argc, argv, "data_manager");
    ros::NodeHandle nh;

    tf_broadcaster = std::make_unique<tf2_ros::TransformBroadcaster>();

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
