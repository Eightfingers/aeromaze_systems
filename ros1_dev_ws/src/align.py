#!/usr/bin/env python3

import rospy
import numpy as np

from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import PoseStamped
from scipy.spatial.transform import Rotation as R

class GravityAlignNode:
    def __init__(self):
        self.imu_topic = "/livox/imu"
        self.odom_topic = "/fastlio_odom"
        self.output_topic = "/gravity_aligned_odom"
        self.accu_pitch = 0
        self.accu_roll = 0
        self.imu_sample_count = 0
        self.avg_roll, self.avg_pitch = 0, 0

        # Number of IMU samples used for initialization
        # /livox/imu is at 200hz, so 50 hz will be completed in 0.25 seconds
        self.init_samples = rospy.get_param("~init_samples", 50)
        self.align_pose = PoseStamped()

        # Ignore acceleration samples whose magnitude is too far
        # from gravity. This helps reject motion during startup.
        self.gravity = rospy.get_param("~gravity",9.81)

        self.gravity_tolerance = rospy.get_param("~gravity_tolerance",1.5)

        # ---------------------------------------------------------
        # State
        # ---------------------------------------------------------
        self.latest_odom = None
        self.accel_samples = []
        self.gravity_alignment_ready = False

        # Rotation which converts original odom frame
        # into gravity-aligned frame.
        #
        # p_aligned = R_align * p_odom
        self.R_align = np.eye(3)

        self.odom_sub = rospy.Subscriber(
            self.odom_topic,
            Odometry,
            self.odom_callback,
            queue_size=10
        )

        self.imu_sub = rospy.Subscriber(
            self.imu_topic,
            Imu,
            self.imu_callback,
            queue_size=100
        )

        self.odom_pub = rospy.Publisher(
            self.output_topic,
            Odometry,
            queue_size=10
        )

        self.pose_pub = rospy.Publisher(
            "axis_pose",
            PoseStamped,
            queue_size=1
        )

        self.corrected_pose = rospy.Publisher(
            "corrected_pose",
            PoseStamped,
            queue_size=1
        )

        self.odom_pose = rospy.Publisher(
            "odom_pose",
            PoseStamped,
            queue_size=1
        )

        rospy.loginfo("Gravity alignment node started")
        rospy.loginfo("Odometry: %s", self.odom_topic)
        rospy.loginfo("IMU:      %s", self.imu_topic)
        rospy.loginfo("Output:   %s", self.output_topic)

    # =============================================================
    # IMU callback
    # =============================================================
    def imu_callback(self, msg):
        
        if self.gravity_alignment_ready:
            self.pose_pub.publish(self.align_pose)
            return

        a = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ])

        accel_norm = np.linalg.norm(a)
        # Prevent division by zero if the IMU reads zero acceleration
        if accel_norm < 1e-6:
            return
        
        # if abs(accel_norm - self.gravity) > self.gravity_tolerance:
        #     print(accel_norm)
        #     print("gravity",self.gravity)
        #     return  # Skip this sample, robot is moving

        a_normalized = a / accel_norm
        ax, ay, az = a_normalized[0], a_normalized[1], a_normalized[2]
        # Calculate pitch and roll in radians
        # Pitch: rotation around Y-axis (tilt forward/backward)
        pitch = np.arctan2(-ax, np.sqrt(ay**2 + az**2))
        # Roll: rotation around X-axis (tilt side-to-side)
        roll = np.arctan2(ay, az)
        self.accu_pitch += pitch
        self.accu_roll += roll
        self.imu_sample_count += 1

        # self.accel_samples.append(a_normalized)

        if self.imu_sample_count >= self.init_samples:
            self.avg_pitch = self.accu_pitch / self.imu_sample_count
            self.avg_roll = self.accu_roll / self.imu_sample_count

            print(
                "Average pitch: {:.2f} degrees, Average roll: {:.2f} degrees".format(
                    np.degrees(self.avg_pitch), np.degrees(self.avg_roll)
                )
            )

            # Convert average pitch and roll to radians
            yaw = np.radians(180)
            # tf expects angles in radians
            # quaternion_from_euler returns [x, y, z, w]
            # rotation = R.from_euler('xyz', [self.avg_roll, self.avg_pitch, yaw])
            rotation = R.from_euler('xyz', [0, 0, yaw])
            q_2 = rotation.as_quat()  # Returns [x, y, z, w]
            self.gravity_alignment_ready = True
            self.align_pose.header.stamp = rospy.Time.now()
            self.align_pose.header.frame_id = "map"
            self.align_pose.pose.orientation.x = q_2[0]
            self.align_pose.pose.orientation.y = q_2[1]
            self.align_pose.pose.orientation.z = q_2[2]
            self.align_pose.pose.orientation.w = q_2[3]
            self.pose_pub.publish(self.align_pose) # for debugging purposes
            rospy.loginfo("Gravity alignment completed.")

    # =============================================================
    # Odometry callback
    # =============================================================
    def odom_callback(self, msg):
        self.latest_odom = msg

        if not self.gravity_alignment_ready:
            return

        # Apply the rotation to the odometry position and orientation.
        # Angles must be in radians (matching imu_callback).
        axis_rotation = R.from_euler(
            'xyz', [self.avg_roll, self.avg_pitch, np.radians(180)]
        )

        # Extract original position and orientation from incoming odometry
        position = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z
        ])
        
        current_rotation = R.from_quat([
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w
        ])

        # Apply alignment rotation
        rotated_position = axis_rotation.apply(position)
        new_rotation = axis_rotation * current_rotation
        q = new_rotation.as_quat()

        # Debug PoseStamped topics for RViz visualization
        corrected = PoseStamped()
        corrected.header.stamp = rospy.Time.now()
        corrected.header.frame_id = "map"
        corrected.pose.position.x = rotated_position[0]
        corrected.pose.position.y = rotated_position[1]
        corrected.pose.position.z = rotated_position[2]
        corrected.pose.orientation.x = q[0]
        corrected.pose.orientation.x = q[1]
        corrected.pose.orientation.x = q[2]
        corrected.pose.orientation.x = q[3]

        self.corrected_pose.publish(corrected)

def main():
    rospy.init_node(
        "gravity_alignment",
        anonymous=False
    )

    GravityAlignNode()

    rospy.spin()


if __name__ == "__main__":
    main()