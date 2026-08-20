#!/usr/bin/env python3

import json
import rospy
from std_msgs.msg import String

rospy.init_node('fake_detection_pub', anonymous=True)

sample = {
    "from_agent": 1,
    "type": "person3",
    "confidence": 0.91,
    "global_pose": {"x": 1, "y": 2, "z": 3}
}
sample_json = json.dumps(sample, indent=2)

pub = rospy.Publisher('/detections', String, queue_size=10)
rate = rospy.Rate(1)  # 1 Hz

rospy.loginfo("Publishing fake detection JSON to /detections...")
while not rospy.is_shutdown():
    pub.publish(String(data=sample_json))
    rospy.loginfo("Published:\n" + sample_json)
    rate.sleep()
