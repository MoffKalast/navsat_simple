# Navsat Simple

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simpler alternative to robot_localization that publishes a transform between the world, map and odom frame based on low pass filtered NavSatFix and high pass filtered Odometry data. 

Note that this package only handles the translational offset, so the `odom` frame should already be fused with an IMU and giving absolute world rotation.

## Subscribed Topics

 - `/odom/wheels` (Odometry), the odometry data, presumed fused with IMU or other
 - `/odom/gps` (Odometry), the metric GPS odometry data, provided by gps_common
 - `/gnss/fix` (NavSatFix), the GNSS fix data for determining the origin

## Published Topics

 - `/tf` (TFMessage), the `world->map` and `map->odom` frames
- `/navsat_simple/origin_fix` (NavSatFix), publishes the origin of the GNSS fix
- `/navsat_simple/raw_pose` (NavSatFix), publishes the raw pose of received GNSS fixes as they arrive, plus the rotation from /odom/wheels for debug comparison

## Services

- `/navsat_simple/reset` (Empty), resets the node completely

## Dynamic Reconfigure Config

 - `low_pass_filter` (double_t), GPS low pass filtering multiplier, should be between 0.0 and 1.0, where 0.0 means zero filtering and 1.0 means new data has no effect