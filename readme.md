# ROS2 Robot Navigation Commands

Project files:

```text
~/1.Code/robot_nav_config/
```

Use `ROS_DOMAIN_ID=0` everywhere. On the laptop, use Fast DDS so it can see the Pi cleanly.

## How Pi And Laptop Communicate

The robot stack runs on the Pi. RViz runs on the laptop as a remote screen and control panel.

Both machines are connected to the same Wi-Fi/LAN and communicate using ROS 2 DDS discovery and messages.

Current network example:

```text
Pi:     192.168.1.53
Laptop: 192.168.1.48
```

Data flow:

```text
Pi publishes:
  /map
  /scan
  /odom
  /tf
  /amcl_pose
  /particle_cloud

Laptop RViz subscribes:
  shows map, robot, lidar, TF, paths, waypoints

Laptop RViz sends:
  /navigate_to_pose action
  /navigate_through_poses action
  /follow_waypoints action
  /initialpose

Pi Nav2 receives goals:
  plans path
  controls robot
  publishes /cmd_vel

Pi Yahboom driver receives:
  /cmd_vel
  moves motors
```

Both machines must use the same ROS network settings:

```bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

If RViz cannot see the Pi, check these first:

```bash
hostname -I
ping -c 3 192.168.1.53
ros2 multicast receive
ros2 multicast send
ros2 node list
ros2 topic list
```

## Requirements For A New System

This setup assumes:

```text
OS:        Ubuntu 22.04
ROS:       ROS 2 Humble
Network:   Pi and laptop on same Wi-Fi/LAN
DDS/RMW:   rmw_fastrtps_cpp
Domain:    ROS_DOMAIN_ID=0
```

### Pi Requirements

The Pi runs the real robot hardware, lidar, odometry, Nav2, and waypoint follower.

Install ROS packages:

```bash
sudo apt update
sudo apt install \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-nav2-waypoint-follower \
  ros-humble-slam-toolbox \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-xacro \
  ros-humble-joy \
  ros-humble-teleop-twist-joy \
  ros-humble-rmw-fastrtps-cpp \
  python3-colcon-common-extensions
```

Required source/workspace packages on the Pi:

```text
Yahboom driver/control:
  ~/1.Code/ROS2-Code/driver_ws
  packages: yahboomcar_bringup, yahboomcar_ctrl

LD19 lidar driver:
  ~/ldlidar_ws
  package: ldlidar_stl_ros2

Robot navigation config:
  ~/1.Code/robot_nav_config
```

The Pi shell must source ROS and the driver workspaces. Put these in `~/.bashrc` if they are not already there:

```bash
source /opt/ros/humble/setup.bash
source ~/1.Code/ROS2-Code/driver_ws/install/setup.bash
source ~/ldlidar_ws/install/setup.bash

export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Hardware/device requirements on the Pi:

```text
Motor driver available to yahboomcar_bringup
LD19 lidar available as /dev/lidar
IMU topic available as /imu/data_raw
Motor board velocity topic available as /vel_raw
```

Check important Pi packages:

```bash
ros2 pkg prefix yahboomcar_bringup
ros2 pkg prefix yahboomcar_ctrl
ros2 pkg prefix ldlidar_stl_ros2
ros2 pkg prefix nav2_bringup
ros2 pkg prefix nav2_waypoint_follower
```

### Laptop Requirements

The laptop only needs ROS/RViz tools. It does not need the Yahboom motor driver.

Install ROS packages:

```bash
sudo apt update
sudo apt install \
  ros-humble-rviz2 \
  ros-humble-nav2-rviz-plugins \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-rmw-fastrtps-cpp
```

Laptop shell setup:

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

Check laptop can see Nav2/RViz packages:

```bash
ros2 pkg prefix rviz2
ros2 pkg prefix nav2_rviz_plugins
ros2 pkg prefix rmw_fastrtps_cpp
```

The laptop copies the RViz config from the Pi:

```bash
scp biswa@192.168.1.53:/home/biswa/1.Code/robot_nav_config/rviz/robot_config.rviz ~/robot_config.rviz
```

If the Pi IP changes, update `192.168.1.53` in the `scp` command.

## Optional Clean Reset

Use this only if old robot/Nav2/RViz processes are stuck.

```bash
pkill -f rviz2
pkill -f yahboom_keyboard
pkill -f yahboom_joy
pkill -f diff_driver_X3
pkill -f ldlidar
pkill -f LD19
pkill -f odom_publisher.py
pkill -f robot_state_publisher
pkill -f slam_toolbox
pkill -f nav2
pkill -f lifecycle_manager
pkill -f waypoint_follower
pkill -f start_robot.launch.py
pkill -f start_nav2.launch.py
ros2 daemon stop
sleep 5
```

Check that nothing old is left:

```bash
ps aux | grep -E 'rviz2|yahboom|diff_driver|ldlidar|LD19|odom_publisher|robot_state_publisher|slam_toolbox|nav2|lifecycle_manager|waypoint|start_robot|start_nav2' | grep -v grep
```

Blank output means clean.

## Pi Terminal 1: Robot Base

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py
```

This starts the driver, lidar, odom publisher, and robot state publisher.

Current odometry mode:

```text
Linear distance: front-left + front-right encoders via /front_encoders
Rotation/yaw:    /imu/data_raw
Rear encoders:   intentionally unused for now
```

## Pi Terminal 2: Nav2

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 launch ~/1.Code/robot_nav_config/launch/start_nav2.launch.py
```

This starts map server, AMCL, planner, controller, behavior server, BT navigator, and lifecycle manager.

## Pi Terminal 3: Waypoint Follower

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 run nav2_waypoint_follower waypoint_follower --ros-args \
  -p use_sim_time:=false \
  -p loop_rate:=20 \
  -p stop_on_failure:=false \
  -p waypoint_task_executor_plugin:=wait_at_waypoint \
  -p wait_at_waypoint.plugin:=nav2_waypoint_follower::WaitAtWaypoint \
  -p wait_at_waypoint.enabled:=true \
  -p wait_at_waypoint.waypoint_pause_duration:=200
```

Keep this terminal open.

## Pi Terminal 4: Activate Waypoints

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 lifecycle set /waypoint_follower configure
ros2 lifecycle set /waypoint_follower activate

ros2 lifecycle get /waypoint_follower
ros2 action info /follow_waypoints
```
#Use this if above command is not giving the expected text. 

Expected:

```text
active [3]
Action servers: 1
    /waypoint_follower
```

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

ros2 node list | grep waypoint
ros2 lifecycle get /waypoint_follower

ros2 lifecycle set /waypoint_follower configure
sleep 2
ros2 lifecycle get /waypoint_follower

ros2 lifecycle set /waypoint_follower activate
sleep 2
ros2 lifecycle get /waypoint_follower

ros2 action info /follow_waypoints
```



## Laptop: RViz

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

scp biswa@192.168.1.53:/home/biswa/1.Code/robot_nav_config/rviz/robot_config.rviz ~/robot_config.rviz

ros2 daemon stop
ros2 daemon start

rviz2 -d ~/robot_config.rviz
```

In RViz:

1. Set **2D Pose Estimate** first.
2. Use **Nav2 Goal** for a single goal.
3. For multiple poses, click **Waypoint / Nav Through Poses Mode**.
4. Use **Nav2 Goal** to place each pose.
5. Click **Start Nav Through Poses** or **Start Waypoint Following**.

The RViz config includes:

```text
Map: /map
LaserScan: /scan
AMCL Pose: /amcl_pose
AMCL Particle Swarm: /particle_cloud
Global Plan: /plan
Local Plan: /local_plan
Waypoints MarkerArray: /waypoints
```

## Health Checks

Run on Pi or laptop:

```bash
ros2 node list
ros2 topic list
ros2 action info /navigate_to_pose
ros2 action info /navigate_through_poses
ros2 action info /follow_waypoints
ros2 lifecycle get /amcl
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /waypoint_follower
```

Laptop should receive:

```bash
ros2 topic echo /map --once
ros2 topic echo /scan --once
ros2 topic echo /odom --once
ros2 topic echo /tf --once
ros2 run tf2_ros tf2_echo map base_link
```

## Optional Keyboard Driving

Use only when Nav2 is not controlling the robot.

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
ros2 run yahboomcar_ctrl yahboom_keyboard
```

Do not run keyboard driving while using Nav2 goals or waypoints.

## Optional Joystick Driving

Use only when Nav2 is not controlling the robot.

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py joy:=true
```

## Mapping Mode

Use this only when creating a new map.

```bash
source ~/.bashrc
export ROS_DOMAIN_ID=0
ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py slam:=true
```

Do not run `start_nav2.launch.py` while `slam:=true`.

## Important Files

```text
~/1.Code/robot_nav_config/launch/start_robot.launch.py
~/1.Code/robot_nav_config/launch/start_nav2.launch.py
~/1.Code/robot_nav_config/config/nav2_params.yaml
~/1.Code/robot_nav_config/maps/my_map.yaml
~/1.Code/robot_nav_config/maps/my_map.pgm
~/1.Code/robot_nav_config/urdf/my_4wd_robot.urdf
~/1.Code/robot_nav_config/scripts/odom_publisher.py
~/1.Code/robot_nav_config/rviz/robot_config.rviz
~/1.Code/robot_nav_config/reference/ldlidar/ld19.launch.py
```

## USB Backup Command

USB path used on this Pi:

```text
/media/biswa/UBUNTU 22_0
```

Backup command.

The USB is FAT32, so use a `.tar.gz` archive. This preserves Linux filenames that FAT32 cannot store directly, such as names containing `:`.

```bash
USB="/media/biswa/UBUNTU 22_0"
STAMP="$(date +%F_%H-%M-%S)"
DEST="$USB/1.Code_backup_$STAMP"

mkdir -p "$DEST"
tar -C /home/biswa -czf "$DEST/1.Code_full_$STAMP.tar.gz" 1.Code

TMP="/tmp/robot_backup_essentials_$STAMP"
mkdir -p "$TMP"
cp ~/.bashrc "$TMP/bashrc"
cp -r /etc/udev/rules.d "$TMP/udev_rules.d"
tar -C /tmp -czf "$DEST/essential_configs_$STAMP.tar.gz" "robot_backup_essentials_$STAMP"
rm -rf "$TMP"

sync
```
