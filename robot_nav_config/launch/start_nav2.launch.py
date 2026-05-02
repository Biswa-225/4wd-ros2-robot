from launch import LaunchDescription
from launch_ros.actions import Node

# Shared project paths for Nav2 parameters and the saved map.
# This is a direct-file launch, so absolute paths are used instead of package lookup.
PROJECT_DIR = '/home/biswa/1.Code/robot_nav_config'
NAV2_PARAMS = f'{PROJECT_DIR}/config/nav2_params.yaml'
MAP_YAML = f'{PROJECT_DIR}/maps/my_map.yaml'

def generate_launch_description():
    return LaunchDescription([
        # Loads the saved occupancy grid from maps/my_map.yaml and publishes /map.
        # AMCL and the global costmap both depend on this map.
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{'yaml_filename': MAP_YAML,
                        'use_sim_time': False}]
        ),
        # AMCL localizes the robot on the saved map using /scan and odom -> base_link TF.
        # This publishes map -> odom, which connects the saved map to live odometry.
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[NAV2_PARAMS]
        ),
        # Controller follows planned paths and publishes /cmd_vel to the Yahboom driver.
        # Most movement tuning happens in nav2_params.yaml under controller_server/FollowPath.
        Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=[NAV2_PARAMS]
        ),
        # Planner creates global paths on the map/costmap.
        # It answers Nav2 requests like "find a path from robot pose to goal pose".
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[NAV2_PARAMS]
        ),
        # Behavior server runs recovery actions such as spin, backup, and wait.
        # These are used when the robot is blocked, stuck, or needs a recovery action.
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[NAV2_PARAMS]
        ),
        # BT navigator receives NavigateToPose/NavigateThroughPoses action goals.
        # RViz Nav2 Goal and waypoint/nav-through-poses mode talk to this action server.
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[NAV2_PARAMS]
        ),
        # Lifecycle manager configures and activates the Nav2 lifecycle nodes above.
        # autostart=True means you should not need to manually configure AMCL/controller/planner.
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': False,
                        'autostart': True,
                        'node_names': [
                            # Order matters: map/localization first, then planning/control.
                            'map_server',
                            'amcl',
                            'controller_server',
                            'planner_server',
                            'behavior_server',
                            # waypoint_follower is started separately for now.
                            'bt_navigator'
                        ]}]
        ),
    ])
