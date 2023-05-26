# Navsat Simple

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simpler alternative to robot_localization that publishes a transform between the world, map and odom frame based on low pass filtered NavSatFix and high pass filtered Odometry data. 

Note that this package only handles the translational offset, so the `odom` frame should already be fused with an IMU and giving absolute world rotation.

## Subscribed Topics

 - `/odom/wheels` (Odometry), the odometry data, presumed fused with IMU or other
 - `/odom/gps` (Odometry), the metric GPS odometry data, provided by gps_common
 - `/gnss/fix` (NavSatFix), the GNSS fix data for determining the origin

## Published Topics

 - `/tf` (TFMessage): This is the `world->map` and `map->odom` frames.
 - `/navsat_simple/origin_fix` (NavSatFix): This topic publishes the origin of the GNSS fix.
 - `/navsat_simple/raw_pose` (NavSatFix): This topic publishes the raw pose of received GNSS fixes as they arrive, plus the rotation from /odom/wheels for debugging comparison.
 - `/navsat_simple/heading` (PoseWithCovarianceStamped): This topic publishes the calculated heading based on GNSS data. **If the receiver isn't moving, the orientation will be a zero quaternion.**

## Services

- `/navsat_simple/reset` (Empty), resets the node completely

## Dynamic Reconfigure Config

 - `gps_low_pass_filter` (double_t, 0-1.0): This is the low pass filter multiplier for GNSS data. Default is 0.998.
 - `odom_high_pass_filter` (double_t, 0-1.0): This is the high pass filter multiplier for odometry. Default is 0.9985.
 - `min_velocity` (double_t, 0.1-1.0): This parameter adjusts the minimum velocity required to calculate heading. Default is 0.5.
 - `min_covariance` (double_t, 2.0-100.0): This parameter adjusts the minimum acceptable covariance value for heading calculation. Default is 10.0.
