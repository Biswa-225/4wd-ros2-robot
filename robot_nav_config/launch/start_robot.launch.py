from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

# All paths are fixed for this robot project on the Pi.
# If this folder is moved, update PROJECT_DIR first before changing any launch logic.
PROJECT_DIR = '/home/biswa/1.Code/robot_nav_config'

def generate_launch_description():
    # robot_state_publisher needs the URDF text as a parameter.
    # The URDF contains the robot frame tree: base_link, wheels, lidar frame, etc.
    # Loading it here keeps the launch file independent from a packaged ROS install.
    with open(f'{PROJECT_DIR}/urdf/my_4wd_robot.urdf', 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        # Enable SLAM only when creating/updating a map.
        # Normal navigation should keep this false because Nav2 uses the saved map instead.
        # Example mapping command:
        #   ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py slam:=true
        DeclareLaunchArgument(
            'slam',
            default_value='false',
            description='Start slam_toolbox only when creating a new map'
        ),
        # Joystick is optional and should stay off while Nav2 controls /cmd_vel.
        # If joy:=true and Nav2 are both active, both may try to command the motors.
        DeclareLaunchArgument(
            'joy',
            default_value='false',
            description='Start joystick teleop. Keep false when running Nav2.'
        ),
        # Lidar can be disabled if LD19 is launched manually for debugging.
        # Example:
        #   ros2 launch ... start_robot.launch.py lidar:=false
        DeclareLaunchArgument(
            'lidar',
            default_value='true',
            description='Start LD19 lidar. Set false if running lidar manually.'
        ),
        # Yahboom base driver subscribes to /cmd_vel and talks to the motor board.
        # This node is the final motor command receiver during Nav2, keyboard, or joystick driving.
        # angular_limit limits turning rate inside the Yahboom driver, not inside Nav2.
        Node(
            package='yahboomcar_bringup',
            executable='diff_driver_X3',
            name='driver_node',
            output='screen',
            parameters=[{
                'angular_limit': 1.5,
            }]
        ),
        # LD19 publishes LaserScan on /scan using the base_laser frame from the URDF.
        # Nav2 costmaps and AMCL both depend on this /scan topic.
        Node(
            package='ldlidar_stl_ros2',
            executable='ldlidar_stl_ros2_node',
            name='LD19',
            output='screen',
            condition=IfCondition(LaunchConfiguration('lidar')),
            parameters=[
                # Driver product mode for the LD19 lidar.
                {'product_name': 'LDLiDAR_LD19'},
                # Published as /scan because nav2_params.yaml and AMCL expect this name.
                {'topic_name': 'scan'},
                # This frame must match the lidar frame in the URDF.
                {'frame_id': 'base_laser'},
                # /dev/lidar should be provided by a udev rule for stable USB naming.
                {'port_name': '/dev/lidar'},
                # LD19 serial baud rate.
                {'port_baudrate': 230400},
                # True/False flips scan angle direction if the scan appears mirrored.
                {'laser_scan_dir': True},
                # False keeps full 360 degree data. Enable only if you need to mask robot body hits.
                {'enable_angle_crop_func': False},
            ]
        ),
        # Publishes static/dynamic transforms from the URDF, including base_link -> base_laser.
        # This makes TF available for RViz, AMCL, costmaps, and laser projection.
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),
        # Custom odom node fuses /vel_raw forward motion with IMU yaw rate.
        # It publishes both /odom and TF odom -> base_link.
        # Nav2 needs this odom transform continuously.
        ExecuteProcess(
            cmd=['python3', f'{PROJECT_DIR}/scripts/odom_publisher.py'],
            output='screen'
        ),
        # Optional joystick input device node.
        # It reads /dev/input/js0 and publishes joystick messages for the Yahboom teleop node.
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            condition=IfCondition(LaunchConfiguration('joy')),
            parameters=[{
                # Change this if the joystick appears at a different Linux device path.
                'dev': '/dev/input/js0',
                # Ignore tiny stick movement near center.
                'deadzone': 0.1,
                # Keep publishing at 20 Hz while the stick is held.
                'autorepeat_rate': 20.0,
            }]
        ),
        # Converts joystick messages to Yahboom robot velocity commands.
        # This node publishes /cmd_vel, so keep joy:=false when Nav2 is driving.
        Node(
            package='yahboomcar_ctrl',
            executable='yahboom_joy_X3',
            name='yahboom_joy_X3',
            output='screen',
            condition=IfCondition(LaunchConfiguration('joy'))
        ),

        # --- SLAM TOOLBOX (for mapping a new room only) ---
        # Use: ros2 launch ~/1.Code/robot_nav_config/launch/start_robot.launch.py slam:=true
        # Keep slam:=false when running start_nav2.launch.py.
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            condition=IfCondition(LaunchConfiguration('slam')),
            parameters=[{
                # Frame names must match odom_publisher.py and the robot URDF.
                # use_sim_time is false because this is a real robot, not Gazebo.
                'use_sim_time': False,
                # odom_frame comes from odom_publisher.py.
                'odom_frame': 'odom',
                # map_frame is created by SLAM while mapping.
                'map_frame': 'map',
                # base_frame is the robot body frame from the URDF.
                'base_frame': 'base_link',
                # SLAM uses the same laser scan topic as Nav2.
                'scan_topic': '/scan',
                # These settings favor small indoor maps and frequent scan matching.
                # Publish map -> odom often so RViz and TF stay responsive.
                'transform_publish_period': 0.02,
                # Short transform timeout helps reveal TF problems quickly.
                'transform_timeout': 0.5,
                # Keep enough TF history for scan matching and loop closure.
                'tf_buffer_duration': 30.0,
                # How often the map is updated while driving.
                'map_update_interval': 2.0,
                # 5 cm grid cells match the saved Nav2 map resolution.
                'resolution': 0.05,
                # Minimum movement before SLAM considers adding a new scan update.
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.2,
                'minimum_time_interval': 0.2,
                # Scan matching improves map quality when odom is not perfect.
                'use_scan_matching': True,
                'use_scan_barycenter': True,
                # Loop closing helps correct drift after driving around the room.
                'link_match_minimum_response_fine': 0.1,
                'link_scan_maximum_distance': 1.5,
                'do_loop_closing': True,
            }]
        ),
        # --- END SLAM TOOLBOX ---
    ])
