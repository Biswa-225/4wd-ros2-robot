from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    with open('/home/biswa/my_4wd_robot.urdf', 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        DeclareLaunchArgument(
            'slam',
            default_value='false',
            description='Start slam_toolbox only when creating a new map'
        ),
        Node(
            package='yahboomcar_bringup',
            executable='diff_driver_X3',
            name='driver_node',
            output='screen'
        ),
        Node(
            package='ldlidar_stl_ros2',
            executable='ldlidar_stl_ros2_node',
            name='LD19',
            output='screen',
            parameters=[
                {'product_name': 'LDLiDAR_LD19'},
                {'topic_name': 'scan'},
                {'frame_id': 'base_laser'},
                {'port_name': '/dev/lidar'},
                {'port_baudrate': 230400},
                {'laser_scan_dir': True},
                {'enable_angle_crop_func': False},
            ]
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_base_laser',
            arguments=[
                '--x', '0.055',
                '--y', '0',
                '--z', '0.130',
                '--roll', '0',
                '--pitch', '0',
                '--yaw', '0',
                '--frame-id', 'base_link',
                '--child-frame-id', 'base_laser'
            ]
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}]
        ),
        ExecuteProcess(
            cmd=['python3', '/home/biswa/odom_publisher.py'],
            output='screen'
        ),
        Node(
            package='joy',
            executable='joy_node',
            name='joy_node',
            output='screen',
            parameters=[{
                'dev': '/dev/input/js0',
                'deadzone': 0.1,
                'autorepeat_rate': 20.0,
            }]
        ),
        Node(
            package='yahboomcar_ctrl',
            executable='yahboom_joy_X3',
            name='yahboom_joy_X3',
            output='screen'
        ),

        # --- SLAM TOOLBOX (for mapping a new room only) ---
        # Use: ros2 launch ~/start_robot.launch.py slam:=true
        # Keep slam:=false when running start_nav2.launch.py.
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            condition=IfCondition(LaunchConfiguration('slam')),
            parameters=[{
                'use_sim_time': False,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/scan',
                'transform_publish_period': 0.02,
                'transform_timeout': 0.5,
                'tf_buffer_duration': 30.0,
                'map_update_interval': 2.0,
                'resolution': 0.05,
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.2,
                'minimum_time_interval': 0.2,
                'use_scan_matching': True,
                'use_scan_barycenter': True,
                'link_match_minimum_response_fine': 0.1,
                'link_scan_maximum_distance': 1.5,
                'do_loop_closing': True,
            }]
        ),
        # --- END SLAM TOOLBOX ---
    ])
