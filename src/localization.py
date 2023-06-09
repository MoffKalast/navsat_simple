#!/bin/python3

import rospy
import tf2_ros
import tf
import math
import tf2_ros

# High percision for UTM coords
from decimal import *
getcontext().prec = 12

from std_srvs.srv import Empty
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from dynamic_reconfigure.server import Server as DynamicReconfigureServer
from navsat_simple.cfg import NavsatSimpleConfig

class TFPublisher:

	def __init__(self):
		rospy.init_node('gps_tf_publisher', anonymous=False)

		self.gps_low_pass_filter = rospy.get_param('~gps_low_pass_filter', 0.99)
		self.odom_high_pass_filter = rospy.get_param('~odom_high_pass_filter', 0.995)

		self.tf_buffer = tf2_ros.Buffer()
		self.listener = tf2_ros.TransformListener(self.tf_buffer)

		self.tf_static_pub = tf2_ros.StaticTransformBroadcaster()
		self.tf_pub = tf2_ros.TransformBroadcaster()

		self.init({})

		self.odom_sub = rospy.Subscriber("odom/wheels", Odometry, self.odom_callback)
		self.gps_sub = rospy.Subscriber("odom/gps", Odometry, self.gps_callback)
		self.fix_sub = rospy.Subscriber("gnss/fix", NavSatFix, self.fix_callback)

		self.fix_origin_pub = rospy.Publisher("navsat_simple/origin_fix", NavSatFix, queue_size=1, latch=True)
		self.reset_srv = rospy.Service('navsat_simple/reset', Empty, self.init)

		self.reconfigure_server = DynamicReconfigureServer(NavsatSimpleConfig, self.dynamic_reconfigure_callback)
		rospy.loginfo("Navsat Simple Ready")


	def dynamic_reconfigure_callback(self, config, level):

		self.gps_low_pass_filter = config.gps_low_pass_filter
		self.odom_high_pass_filter = config.odom_high_pass_filter

		rospy.loginfo("Navsat Simple reconfigured.")

		return config

	def init(self, msg):

		self.odom_delayed_x = 0
		self.odom_delayed_y = 0
		self.odom_msg_latest = None
		self.odom_msg = None

		self.gps_msg = None

		self.origin_fix = None
		self.origin_x = None
		self.origin_y = None

		self.gps_raw_x = 0
		self.gps_raw_y = 0

		self.gps_x = 0
		self.gps_y = 0


	def fix_callback(self, msg):
		if self.origin_fix is None and msg.status.status != -1:
			msg.header.frame_id = "map"
			self.origin_fix = msg
			self.fix_origin_pub.publish(msg)

	def gps_callback(self, msg):
		if math.isnan(msg.pose.pose.position.x) or math.isnan(msg.pose.pose.position.y):
			rospy.logwarn("GPS has no fix!")
			return

		self.gps_last_received_stamp = rospy.Time.now()
		self.gps_msg = msg

		self.odom_msg = self.odom_msg_latest

		# define starting origin
		if self.origin_x is None:
			self.origin_x = Decimal(self.gps_msg.pose.pose.position.x)
			self.origin_y = Decimal(self.gps_msg.pose.pose.position.y)

			world_map = TransformStamped()
			world_map.header.stamp = rospy.Time.now()
			world_map.header.frame_id = "world"
			world_map.child_frame_id = "map"
			world_map.transform.translation.x = float(self.origin_x)
			world_map.transform.translation.y = float(self.origin_y)
			world_map.transform.translation.z = 0.0
			world_map.transform.rotation.x = 0.0
			world_map.transform.rotation.y = 0.0
			world_map.transform.rotation.z = 0.0
			world_map.transform.rotation.w = 1.0
			self.tf_static_pub.sendTransform(world_map)

		self.gps_raw_x = float(Decimal(msg.pose.pose.position.x) - self.origin_x)
		self.gps_raw_y = float(Decimal(msg.pose.pose.position.y) - self.origin_y)


	def odom_callback(self, msg):
		if math.isnan(msg.pose.pose.position.x) or math.isnan(msg.pose.pose.position.y):
			rospy.logwarn("Odom is NaN!?")
			return

		self.odom_msg_latest = msg

	def update(self):

		# low pass filtering for the GNSS location
		self.gps_x = self.gps_x * self.gps_low_pass_filter + (1.0 - self.gps_low_pass_filter) * self.gps_raw_x
		self.gps_y = self.gps_y * self.gps_low_pass_filter + (1.0 - self.gps_low_pass_filter) * self.gps_raw_y

		if self.odom_msg is None or self.gps_msg is None:
			logmsg = "Waiting for: "

			if self.odom_msg is None:
				logmsg += "ODOM "
			if self.gps_msg is None:
				logmsg += "GPS "

			logmsg += "messages..."
			rospy.logwarn(logmsg)
			rospy.sleep(0.2)
			return

		# delayed response for zeroing out odom position relative to GNSS 
		self.odom_delayed_x = self.odom_delayed_x * self.odom_high_pass_filter + (1.0 - self.odom_high_pass_filter) * self.odom_msg.pose.pose.position.x
		self.odom_delayed_y = self.odom_delayed_y * self.odom_high_pass_filter + (1.0 - self.odom_high_pass_filter) * self.odom_msg.pose.pose.position.y

		if math.isnan(self.odom_delayed_x) or math.isnan(self.odom_delayed_y) or math.isnan(self.gps_x) or math.isnan(self.gps_y):
			# This shouldn't ever happen, but better reset than leave the robot stranded in case it does ever happen, for world waypoints it won't matter anyway
			rospy.logwarn("Something has gone terribly wrong, location is NaN. Resetting!")
			self.init(None)
			return

		map_odom = TransformStamped()
		map_odom.header.stamp = rospy.Time.now()
		map_odom.header.frame_id = "map"
		map_odom.child_frame_id = "odom"
		map_odom.transform.translation.x = self.gps_x - self.odom_delayed_x
		map_odom.transform.translation.y = self.gps_y - self.odom_delayed_y
		map_odom.transform.translation.z = 0.0
		map_odom.transform.rotation.x = 0
		map_odom.transform.rotation.y = 0
		map_odom.transform.rotation.z = 0
		map_odom.transform.rotation.w = 1.0
		self.tf_pub.sendTransform(map_odom)

try:
	tf = TFPublisher()
	rate = rospy.Rate(30)
	while not rospy.is_shutdown():
		tf.update()
		rate.sleep()
except rospy.ROSInterruptException:
	print("Script interrupted")