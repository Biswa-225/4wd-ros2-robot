from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{'yaml_filename': '/home/biswa/my_map.yaml',
                        'use_sim_time': False}]
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=['/home/biswa/nav2_params.yaml']
        ),
        Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=['/home/biswa/nav2_params.yaml']
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=['/home/biswa/nav2_params.yaml']
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=['/home/biswa/nav2_params.yaml']
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=['/home/biswa/nav2_params.yaml']
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': False,
                        'autostart': True,
                        'node_names': [
                            'map_server',
                            'amcl',
                            'controller_server',
                            'planner_server',
                            'behavior_server',
                            'bt_navigator'
                        ]}]
        ),
    ])
