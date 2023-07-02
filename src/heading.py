#!/bin/python3

import rospy
import math
import numpy as np

# High percision for UTM coords
from decimal import *
getcontext().prec = 12

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion, quaternion_from_euler

from dynamic_reconfigure.server import Server as DynamicReconfigureServer
from navsat_simple.cfg import NavsatSimpleHeadingConfig

class GpsNode:
	def __init__(self):
		rospy.init_node('navsat_simple_heading')

		# Add ROS params for atol and minimum_covariance
		self.min_velocity = rospy.get_param('~min_velocity', 0.5)
		self.min_covariance = rospy.get_param('~min_covariance', 10.0)

		self.pose_pub = rospy.Publisher('navsat_simple/heading', PoseWithCovarianceStamped, queue_size=10)
		self.gps_sub = rospy.Subscriber('odom/gps', Odometry, self.gps_callback)
		self.odom_sub = rospy.Subscriber('odom/wheels', Odometry, self.odom_callback)
		self.recent_odom = []

		self.reconfigure_server = DynamicReconfigureServer(NavsatSimpleHeadingConfig, self.dynamic_reconfigure_callback)
		rospy.loginfo("Navsat Heading Calculator Ready")

		self.reversing = False
		self.stopped = False


	def dynamic_reconfigure_callback(self, config, level):

		self.min_velocity = config.min_velocity
		self.min_covariance = config.min_covariance

		rospy.loginfo("Navsat Heading reconfigured.")

		return config
	
	def odom_callback(self, msg):
		self.reversing = msg.twist.twist.linear.x < 0
		self.stopped = math.fabs(msg.twist.twist.linear.x) < 0.2

	def gps_callback(self, msg):

		# Store recent odometry messages, maintaining a list of the last 10
		self.recent_odom.append(msg)
		if len(self.recent_odom) > 10:
			self.recent_odom.pop(0)

		heading = None
		if len(self.recent_odom) > 1 and not self.stopped:

			if self.reversing:
				delta_x = self.recent_odom[0].pose.pose.position.x - self.recent_odom[-1].pose.pose.position.x
				delta_y = self.recent_odom[0].pose.pose.position.y - self.recent_odom[-1].pose.pose.position.y
			else:
				delta_x = self.recent_odom[-1].pose.pose.position.x - self.recent_odom[0].pose.pose.position.x
				delta_y = self.recent_odom[-1].pose.pose.position.y - self.recent_odom[0].pose.pose.position.y

			if not (np.isclose(delta_x, 0.0, atol=self.min_velocity) and np.isclose(delta_y, 0.0, atol=self.min_velocity)):
				# Only calculate heading if the robot has moved sufficiently
				heading = np.arctan2(delta_y, delta_x)

		pose_msg = PoseWithCovarianceStamped()
		pose_msg.header.stamp = rospy.Time.now()
		pose_msg.header.frame_id = "world"

		# Use the position from the latest message
		pose_msg.pose.pose.position = self.recent_odom[-1].pose.pose.position

		if heading is not None and (msg.pose.covariance[0] + msg.pose.covariance[4])/2 < self.min_covariance:
			# Convert heading to quaternion
			quaternion = quaternion_from_euler(0, 0, heading)
			pose_msg.pose.pose.orientation.x = quaternion[0]
			pose_msg.pose.pose.orientation.y = quaternion[1]
			pose_msg.pose.pose.orientation.z = quaternion[2]
			pose_msg.pose.pose.orientation.w = quaternion[3]
		else:
			# Robot is stationary, set invalid quaternion
			pose_msg.pose.pose.orientation.x = 0.0
			pose_msg.pose.pose.orientation.y = 0.0
			pose_msg.pose.pose.orientation.z = 0.0
			pose_msg.pose.pose.orientation.w = 0.0

		# Use the position covariance from the incoming message
		pose_msg.pose.covariance = msg.pose.covariance

		self.pose_pub.publish(pose_msg)


gps_node = GpsNode()
rospy.spin()