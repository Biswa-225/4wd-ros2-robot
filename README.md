# 🤖 4WD Differential Drive Robot — ROS2 Humble

<div align="center">

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue?style=for-the-badge&logo=ros)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204-red?style=for-the-badge&logo=raspberry-pi)
![OS](https://img.shields.io/badge/OS-Ubuntu%2022.04-orange?style=for-the-badge&logo=ubuntu)
![Python](https://img.shields.io/badge/Python-3.10-yellow?style=for-the-badge&logo=python)
![STM32](https://img.shields.io/badge/MCU-STM32F103-blue?style=for-the-badge)
![Lidar](https://img.shields.io/badge/Lidar-LD19-purple?style=for-the-badge)
![Nav2](https://img.shields.io/badge/Nav2-Navigation-brightgreen?style=for-the-badge)
![SLAM](https://img.shields.io/badge/SLAM-slam__toolbox-yellow?style=for-the-badge)
![YAML](https://img.shields.io/badge/YAML-Config-lightgrey?style=for-the-badge&logo=yaml)
![URDF](https://img.shields.io/badge/URDF-Robot%20Model-orange?style=for-the-badge)
![C++](https://img.shields.io/badge/C++-STM32%20Firmware-blue?style=for-the-badge&logo=cplusplus)
![CMake](https://img.shields.io/badge/CMake-Build-red?style=for-the-badge&logo=cmake)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A fully autonomous 4WD differential drive robot built with ROS2 Humble, featuring SLAM mapping, AMCL localization and Nav2 autonomous navigation.**

</div>

---

## ✨ Features

- 🚗 **4WD Differential Drive** with verified motor directions
- 🗺️ **SLAM Mapping** using slam_toolbox
- 📍 **AMCL Localization** on saved maps
- 🧭 **Autonomous Navigation** with Nav2
- 📡 **LD19 Lidar** for obstacle detection
- 🧠 **IMU-based Odometry** (MPU9250)
- 🎮 **Keyboard & Joystick Control**
- 📊 **Real-time RViz2 Visualization**

---

## 🔧 Hardware

| Component | Model |
|---|---|
| **Control Board** | Yahboom YB-ERF01-V1.0 (STM32F103RCT6) |
| **IMU** | MPU9250 (9-axis) |
| **SBC** | Raspberry Pi 4 (Ubuntu 22.04) |
| **Lidar** | LDRobot LD19 |
| **Motors** | 4× DC Motors with Encoders |
| **Battery** | 11.1V 3S LiPo (7.4–12V supported) |

---

## 📁 Repository Structure

```
4wd-ros2-robot/
├── README.md                    # This file
├── start_robot.launch.py        # Main robot launch (mapping + navigation)
├── start_nav2.launch.py         # Nav2 autonomous navigation launch
├── odom_publisher.py            # Odometry publisher (IMU + cmd_vel)
├── nav2_params.yaml             # Nav2 configuration parameters
├── my_4wd_robot.urdf            # Robot URDF model
├── launch/
│   └── ld19.launch.py           # LD19 Lidar launch file
├── map/
│   ├── my_map.pgm               # Saved room map image
│   └── my_map.yaml              # Map metadata
└── src/
    └── yahboomcar_bringup/
        ├── diff_driver_X3.py    # 4WD differential drive driver
        └── yahboom_keyboard.py  # Keyboard teleoperation
```

---

## ⚡ Quick Start

### Prerequisites
```bash
source /opt/ros/humble/setup.bash
source ~/1.Code/ROS2-Code/driver_ws/install/setup.bash
source ~/ldlidar_ws/install/setup.bash
export ROS_DOMAIN_ID=0
```

### 🗺️ Mapping Mode
```bash
# Terminal 1 — Start robot + SLAM
ros2 launch ~/start_robot.launch.py slam:=true

# Terminal 2 — Keyboard control
ros2 run yahboomcar_ctrl yahboom_keyboard

# Terminal 3 — Save map when done
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

### 🧭 Navigation Mode
```bash
# Terminal 1 — Start robot
ros2 launch ~/start_robot.launch.py slam:=false

# Terminal 2 — Start Nav2
ros2 launch ~/start_nav2.launch.py
```

### 💻 RViz2 on Laptop
```bash
export ROS_DOMAIN_ID=0
scp biswa@192.168.1.53:/home/biswa/robot_config.rviz ~/robot_config.rviz
rviz2 -d ~/robot_config.rviz
```

---

## 🎮 Controls

### Keyboard
| Key | Action |
|---|---|
| `w` | Forward |
| `x` | Backward |
| `a` | Rotate Left |
| `d` | Rotate Right |
| `s` | Stop |
| `q` / `z` | Speed Up / Down |

### RViz2 Navigation
1. Click **Initial Pose Tool** → click robot position on map → drag to set direction
2. Click **Nav2 Goal** → click destination on map → robot navigates autonomously!

---

## 🔌 Hardware Wiring

### Motor Connections
| Port | Position | M+ | M− |
|---|---|---|---|
| M1 | Front Left | Red | Black |
| M2 | Front Right | Red | Black |
| M3 | Rear Left | Red | Black |
| M4 | Rear Right | Red | Black |

### Verified Motor Directions
```
Forward:      FL=-speed  FR=+speed  RL=+speed  RR=-speed
Backward:     FL=+speed  FR=-speed  RL=-speed  RR=+speed
Rotate Left:  FL=+rot    FR=+rot    RL=-rot    RR=-rot
Rotate Right: FL=-rot    FR=-rot    RL=+rot    RR=+rot
```

### USB Port Mapping
```
/dev/myserial  →  YB-ERF01 Board  (CH340,  1a86:7523)
/dev/lidar     →  LD19 Lidar      (CP210x, 10c4:ea60)
```

> ⚠️ Use a **data-only USB cable** (red wire cut) between board and Pi to prevent voltage damage.

---

## ⚙️ Configuration

### PID Settings (saved to board flash)
```
P = 1.5  |  I = 0.05  |  D = 0.2
```

### Robot Parameters
| Parameter | Value |
|---|---|
| Wheel Radius | ~0.04 m |
| Wheel Base | ~0.20 m |
| Robot Radius | 0.11 m |
| Max Speed | 0.2 m/s |
| Lidar Range | 0.1 – 3.5 m |

### Nav2 Costmap (tuned for small room)
```
Inflation Radius:   0.10 m
Cost Scaling:       8.0
Local Costmap:      2×2 m
```

---

## 📊 ROS2 Topics

| Topic | Type | Description |
|---|---|---|
| `/cmd_vel` | Twist | Velocity commands |
| `/odom` | Odometry | Robot odometry |
| `/scan` | LaserScan | Lidar data |
| `/map` | OccupancyGrid | Environment map |
| `/imu/data_raw` | Imu | Raw IMU data |
| `/amcl_pose` | PoseWithCovarianceStamped | Robot localization |
| `/particle_cloud` | PoseArray | AMCL particles |
| `/plan` | Path | Navigation path |
| `/voltage` | Float32 | Battery voltage |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `/dev/myserial` missing | Replug USB → `sudo udevadm trigger` |
| `/dev/lidar` missing | Replug lidar USB |
| BRLTTY stealing port | `sudo apt remove -y brltty` |
| Board not detected | Use data-only USB cable, try different port |
| Map distorted | Drive slower, press `z` multiple times |
| Robot not moving in Nav2 | Set Initial Pose in RViz2 first |
| AMCL not converging | Drive robot manually to help localize |
| Duplicate ROS2 nodes | Kill all → restart daemon |

### Kill All Nodes
```bash
sudo pkill -9 -f "ros2|python3|ldlidar|slam|robot_state|static_transform|diff_driver|yahboom|nav2|map_server|amcl|controller|planner|bt_navigator|lifecycle"
sleep 2 && ros2 daemon stop && ros2 daemon start
```

---

## 📸 Demo

> Robot mapping a room using SLAM toolbox and navigating autonomously with Nav2.

---

## 🙏 Acknowledgements

- [Yahboom](https://www.yahboom.net) — YB-ERF01 ROS Driver Board
- [LDRobot](https://www.ldrobot.com) — LD19 Lidar
- [ROS2 Navigation2](https://navigation.ros.org) — Nav2 Framework
- [slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) — SLAM

---

<div align="center">
Made with ❤️ by <a href="https://github.com/Biswa-225">Biswa-225</a>
</div>
