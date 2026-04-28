<<<<<<< HEAD
# 🤖 4WD Differential Drive Robot — ROS2 Humble
**Board:** Yahboom YB-ERF01-V1.0 (STM32F103RCT6 + MPU9250 IMU)  
**SBC:** Raspberry Pi 4 (Ubuntu 22.04)  
**Lidar:** LDRobot LD19  
**ROS2:** Humble  

---

## 📋 Hardware Configuration

### Motor Wiring
| Board Port | Position | M+ | M- |
|---|---|---|---|
| M1 | Front Left | Red | Black |
| M2 | Front Right | Red | Black |
| M3 | Rear Left | Red | Black |
| M4 | Rear Right | Red | Black |

### Encoder Wiring
| Board Port | Motor | Yellow | Green |
|---|---|---|---|
| E1 | Front Left | VCC (3.3V) | Signal A |
| E2 | Front Right | VCC (3.3V) | Signal A |
| E3 | Rear Left | VCC (3.3V) | Signal A |
| E4 | Rear Right | VCC (3.3V) | Signal A |

### Verified Motor Directions
```
FL_FORWARD = +40 → set_motor = -speed
FR_FORWARD = +40 → set_motor = +speed
RL_FORWARD = -40 → set_motor = +speed
RR_FORWARD = -40 → set_motor = -speed

Forward:      FL=-speed, FR=+speed, RL=+speed, RR=-speed
Backward:     FL=+speed, FR=-speed, RL=-speed, RR=+speed
Rotate Left:  FL=+rot,   FR=+rot,   RL=-rot,   RR=-rot
Rotate Right: FL=-rot,   FR=-rot,   RL=+rot,   RR=+rot
```

### Encoder Corrections
```
FL_ENC = -1  (reversed)
FR_ENC = +1  (correct)
RL_ENC = +1  (correct)
RR_ENC = -1  (reversed)
```

### USB Devices
```
/dev/myserial → YB-ERF01 Board (CH340, 1a86:7523)
/dev/lidar    → LD19 Lidar (CP210x, 10c4:ea60)
```

### USB Cable
⚠️ Use **data-only USB cable** (red wire cut) to connect board to Pi.
This prevents voltage damage to Pi/laptop.

---

## 📁 File Locations

| File | Location | Purpose |
|---|---|---|
| Robot driver | `~/1.Code/ROS2-Code/driver_ws/src/yahboomcar_bringup/yahboomcar_bringup/diff_driver_X3.py` | Motor control |
| Odom publisher | `~/odom_publisher.py` | Odometry from IMU+cmd_vel |
| Robot URDF | `~/my_4wd_robot.urdf` | Robot model |
| Start robot | `~/start_robot.launch.py` | Launch robot nodes |
| Start Nav2 | `~/start_nav2.launch.py` | Launch navigation |
| Nav2 params | `~/nav2_params.yaml` | Navigation parameters |
| Map | `~/my_map.pgm` + `~/my_map.yaml` | Saved room map |
| RViz2 config | `~/robot_config.rviz` | RViz2 display settings |
| Lidar launch | `~/ldlidar_ws/src/ldlidar_stl_ros2/launch/ld19.launch.py` | Lidar node |
| udev rules | `/etc/udev/rules.d/myserial.rules` | USB board binding |
| udev rules | `/etc/udev/rules.d/lidar.rules` | USB lidar binding |

---

## ⚙️ PID Settings
```
P = 1.5
I = 0.05
D = 0.2
Saved permanently to board flash
```

---

## 🚀 Quick Start Commands

### Kill Everything
```bash
sudo pkill -9 -f "ros2|python3|ldlidar|slam|robot_state|static_transform|diff_driver|yahboom|nav2|map_server|amcl|controller|planner|bt_navigator|lifecycle"
sleep 2
ros2 daemon stop
ros2 daemon start
```

### MAPPING MODE
```bash
# Pi Terminal 1 — Start robot + SLAM
ros2 launch ~/start_robot.launch.py slam:=true

# Pi Terminal 2 — Keyboard control
ros2 run yahboomcar_ctrl yahboom_keyboard

# Pi Terminal 3 — Save map when done
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

### NAVIGATION MODE
```bash
# Pi Terminal 1 — Start robot (no SLAM)
ros2 launch ~/start_robot.launch.py slam:=false

# Pi Terminal 2 — Start Nav2
ros2 launch ~/start_nav2.launch.py

# Pi Terminal 3 — Optional keyboard
ros2 run yahboomcar_ctrl yahboom_keyboard
```

### Laptop RViz2
```bash
export ROS_DOMAIN_ID=0
scp biswa@192.168.1.53:/home/biswa/robot_config.rviz ~/robot_config.rviz
rviz2 -d ~/robot_config.rviz
```

---

## 🎮 Keyboard Controls
```
w = forward
x = backward
a = rotate left
d = rotate right
s = stop
q = speed up 10%
z = speed down 10%
Ctrl+C = quit
```

---

## 🗺️ RViz2 Navigation

### Set Initial Pose
1. Click **"Initial Pose Tool"** button
2. Click on map where robot is located
3. Drag to set facing direction

### Set Navigation Goal
1. Click **"Nav2 Goal"** button
2. Click on white (free) area of map
3. Robot navigates autonomously!

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `/dev/myserial` not found | Replug USB, run `sudo udevadm trigger` |
| `/dev/lidar` not found | Replug lidar USB |
| BRLTTY stealing port | `sudo apt remove -y brltty` |
| Board not detected | Check USB cable (data-only), try different USB port |
| Map distorted | Drive slower, use `z` key to reduce speed |
| Robot not moving in Nav2 | Set Initial Pose first in RViz2 |
| AMCL not localizing | Drive robot manually to help particles converge |
| Duplicate nodes | Kill all + restart daemon |
| Serial conflict | Only one node can use `/dev/myserial` at a time |

---

## 📊 Topic Reference

| Topic | Type | Purpose |
|---|---|---|
| `/cmd_vel` | Twist | Robot velocity command |
| `/odom` | Odometry | Robot odometry |
| `/scan` | LaserScan | Lidar scan data |
| `/map` | OccupancyGrid | SLAM/Nav2 map |
| `/imu/data_raw` | Imu | Raw IMU data |
| `/voltage` | Float32 | Battery voltage |
| `/vel_raw` | Twist | Raw velocity from board |
| `/amcl_pose` | PoseWithCovarianceStamped | AMCL localization |
| `/particle_cloud` | PoseArray | AMCL particles |
| `/plan` | Path | Nav2 global plan |

---

## 🔌 ROS2 Environment
```bash
# Add to ~/.bashrc
source /opt/ros/humble/setup.bash
source ~/1.Code/ROS2-Code/driver_ws/install/setup.bash
source ~/ldlidar_ws/install/setup.bash
export ROS_DOMAIN_ID=0
```

---

## 📐 Robot Physical Parameters

| Parameter | Value | Notes |
|---|---|---|
| Wheel radius | ~0.04m | 4cm (update after measurement) |
| Wheel base | ~0.20m | Distance between left/right wheels |
| Encoder CPR | ~1000 | Counts per revolution (update after measurement) |
| Robot radius | 0.11m | Used in Nav2 costmap |
| Max speed | 0.2 m/s | Nav2 limit |
| Battery | 11.1V (3S LiPo) | 7.4-12V supported |

---

## 📝 TODO / Pending

- [ ] Measure exact encoder counts per meter
- [ ] Update odom_publisher.py with real encoder data
- [ ] Remap room with encoder-based odometry
- [ ] Fine-tune Nav2 parameters for small room
- [ ] Test full autonomous navigation
- [ ] Add obstacle avoidance tuning
- [ ] Consider adding IMU filter (Madgwick) for better yaw

---

## 📅 Progress Log

| Date | Achievement |
|---|---|
| Day 1 | STM32 firmware flashed, motors verified |
| Day 2 | ROS2 workspace built, keyboard control working |
| Day 3 | Lidar connected, RViz2 working, PID tuned |
| Day 4 | SLAM mapping, map saved, Nav2 basic navigation |
| Day 5 | Nav2 improved, autonomous goal navigation working |

---

*Last updated: April 29, 2026*
=======
# 4wd-ros2-robot
4WD Differential Drive Robot with ROS2 Humble, SLAM and Nav2
>>>>>>> c6eeacf63af48de6cb29e3bea1b9d689c2c80263
