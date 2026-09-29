#!/usr/bin/env python
import rospy
import tf2_ros
from geometry_msgs.msg import TransformStamped, PoseStamped
from tf.transformations import quaternion_from_euler

class MavrosTFBroadcaster:
    def __init__(self):
        rospy.init_node('mavros_tf_broadcaster')

        # Frame name parameters
        self.map_frame = rospy.get_param('~map_frame', 'map')
        self.base_frame = rospy.get_param('~base_frame', 'base_link')
        self.livox_frame = rospy.get_param('~livox_frame', 'livox_frame')

        # Initialize Broadcasters
        self.dynamic_broadcaster = tf2_ros.TransformBroadcaster()
        self.static_broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Publish static transform: base_link -> livox_frame
        self.publish_static_livox_transform()

        # Subscribe to MAVROS local pose for dynamic transform: map -> base_link
        self.pose_sub = rospy.Subscriber(
            '/mavros/local_position/pose',
            PoseStamped,
            self.pose_callback,
            queue_size=10
        )

        rospy.loginfo("TF Broadcaster running: [%s -> %s] (Dynamic) & [%s -> %s] (Static)",
                      self.map_frame, self.base_frame, self.base_frame, self.livox_frame)

    def publish_static_livox_transform(self):
        static_tf = TransformStamped()
        
        static_tf.header.stamp = rospy.Time.now()
        static_tf.header.frame_id = self.base_frame
        static_tf.child_frame_id = self.livox_frame

        # Translation: x=0, y=0, z=0.11
        static_tf.transform.translation.x = 0.0
        static_tf.transform.translation.y = 0.0
        static_tf.transform.translation.z = 0.11

        # Rotation: yaw=3.141593, pitch=-0.365, roll=-0.024 (in radians)
        yaw = 3.141593
        pitch = -0.365
        roll = -0.024
        
        # Convert Euler angles (RPY) to Quaternion [x, y, z, w]
        q = quaternion_from_euler(roll, pitch, yaw)
        static_tf.transform.rotation.x = q[0]
        static_tf.transform.rotation.y = q[1]
        static_tf.transform.rotation.z = q[2]
        static_tf.transform.rotation.w = q[3]

        # Send latching static transform
        self.static_broadcaster.sendTransform(static_tf)

    def pose_callback(self, msg):
        dynamic_tf = TransformStamped()

        dynamic_tf.header.stamp = msg.header.stamp
        dynamic_tf.header.frame_id = self.map_frame
        dynamic_tf.child_frame_id = self.base_frame

        # Translation from MAVROS pose
        dynamic_tf.transform.translation.x = msg.pose.position.x
        dynamic_tf.transform.translation.y = msg.pose.position.y
        dynamic_tf.transform.translation.z = msg.pose.position.z

        # Orientation from MAVROS pose
        dynamic_tf.transform.rotation = msg.pose.orientation

        # Publish dynamic frame transform
        self.dynamic_broadcaster.sendTransform(dynamic_tf)

if __name__ == '__main__':
    try:
        broadcaster = MavrosTFBroadcaster()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
