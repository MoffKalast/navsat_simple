# Navsat Simple

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simpler alternative to robot_localization that publishes a transform from the map frame to the odom frame based on GNSS, IMU, and odometry data. 

Absolute rotation is taken directly from the IMU, metric GNSS data is zeroed with a starting origin and low pass filtered.

The node publishes a local map TF frame between odom and world.

## Subscribed Topics

 - `/tf` (TFMessage), the transform messages
 - `/imu/data` (Imu), the IMU data, only yaw is considered
 - `/odom` (Odometry), the odometry data
 - `/odom/gps` (Odometry), the metric GPS odometry data, provided by gps_common
 - `/gnss/fix` (NavSatFix), the GNSS fix data for determining the origin

## Published Topics

 - `/tf` (TFMessage), the world->map and map->odom frames
- `/odom/gps/origin` (Odometry), publishes the origin of the GPS odometry
- `/navsat_simple/origin_fix` (NavSatFix), publishes the origin of the GNSS fix

## Services

- `/navsat_simple/reset` (Empty), resets the node completely

## Dynamic Reconfigure Config

 - `low_pass_filter` (double_t), GPS low pass filtering multiplier, should be between 0.0 and 1.0, where 0.0 means zero filtering and 1.0 means new data has no effect