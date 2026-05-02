# Robot Navigation Config

This folder keeps the project working files together.

```text
launch/start_robot.launch.py      Robot driver, lidar, robot_state_publisher, odom
launch/start_nav2.launch.py       Nav2 startup
config/nav2_params.yaml           Nav2 and AMCL parameters
maps/my_map.yaml                  Current map metadata
maps/my_map.pgm                   Current map image
urdf/my_4wd_robot.urdf            Robot model and lidar transform
scripts/odom_publisher.py         Odom publisher
rviz/robot_config.rviz            RViz display config
reference/ldlidar/ld19.launch.py  Original/reference lidar launch file
```

Start robot:

```bash
ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py
```

Start Nav2:

```bash
ros2 launch ~/1.Code/robot_nav_config/launch/start_nav2.launch.py
```
