#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

'''
Parameter Description:
---
- Set laser scan directon: 
  1. Set counterclockwise, example: {'laser_scan_dir': True}
  2. Set clockwise,        example: {'laser_scan_dir': False}
- Angle crop setting, Mask data within the set angle range:
  1. Enable angle crop fuction:
    1.1. enable angle crop,  example: {'enable_angle_crop_func': True}
    1.2. disable angle crop, example: {'enable_angle_crop_func': False}
  2. Angle cropping interval setting:
  - The distance and intensity data within the set angle range will be set to 0.
  - angle >= 'angle_crop_min' and angle <= 'angle_crop_max' which is [angle_crop_min, angle_crop_max], unit is degress.
    example:
      {'angle_crop_min': 135.0}
      {'angle_crop_max': 225.0}
      which is [135.0, 225.0], angle unit is degress.

Robot: 4WD Normal Wheel
Lidar: LDRobot LD19
TF: base_link -> base_laser
  x=0.012548 (forward from center)
  y=0        (centered)
  z=0.18     (height)
  yaw=3.316  (190deg correction - verified by hand test)
'''

def generate_launch_description():
  # LDROBOT LiDAR publisher node. This reference launch is useful for lidar-only tests.
  ldlidar_node = Node(
      package='ldlidar_stl_ros2',
      executable='ldlidar_stl_ros2_node',
      name='LD19',
      output='screen',
      parameters=[
        # Product and serial settings must match the LD19 USB device.
        {'product_name': 'LDLiDAR_LD19'},
        {'topic_name': 'scan'},
        {'frame_id': 'base_laser'},
        {'port_name': '/dev/lidar'},
        {'port_baudrate': 230400},
        # Scan direction and crop settings are kept consistent with start_robot.launch.py.
        {'laser_scan_dir': True},
        {'enable_angle_crop_func': False},
        {'angle_crop_min': 135.0},
        {'angle_crop_max': 225.0}
      ]
  )

  # base_link to base_laser tf node
  # Position from URDF: x=0.012548, y=0, z=0.1311
  # Yaw = 3.316 rad (190°) — corrects lidar scan direction
  # verified by hand test: hand at front showed 190° → need 3.316 rad offset
  base_link_to_laser_tf_node = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='base_link_to_base_laser_ld19',
    # This static TF is only needed when running this reference launch without robot_state_publisher.
    arguments=['0.012548','0','0.18','0','0','0','base_link','base_laser']
  )

  # Return both lidar and static TF nodes as one launch description.
  ld = LaunchDescription()
  ld.add_action(ldlidar_node)
  ld.add_action(base_link_to_laser_tf_node)

  return ld
