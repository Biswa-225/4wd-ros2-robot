#!/usr/bin/env python3
# =============================================
# Odometry Publisher — 4WD Differential Drive
# Wheel radius:  0.040m (80mm diameter)
# Wheel base:    0.095m (95mm) - MEASURED
# Encoder CPM:   8489 counts/meter (measured)
# Using vel_raw + IMU, with cmd_vel fallback
# =============================================
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist, TransformStamped
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster
import math

class OdomPublisher(Node):
    def __init__(self):
        # Node name appears in `ros2 node list` as /odom_publisher.
        super().__init__('odom_publisher')

        # Robot parameters (measured)
        # These values are documentation/calibration references in this script.
        # The current integration uses velocity topics rather than raw tick math.
        self.WHEEL_RADIUS = 0.040   # 80mm diameter
        self.WHEEL_BASE   = 0.095   # 95mm between wheels

        # Linear distance calibration:
        #   RAW_LINEAR_SCALE = actual_robot_distance / rviz_odom_distance
        # Example: real robot moved 1.0m, RViz odom moved 0.7m -> scale = 1.43
        # Example: real robot moved 1.0m, RViz odom moved 1.3m -> scale = 0.77
        # vel_raw comes from the motor board. cmd_vel is only a fallback.
        self.RAW_LINEAR_SCALE = 5.57
        # cmd_vel is not true measured motion, so keep this simple unless debugging fallback odom.
        self.CMD_LINEAR_SCALE = 1.0
        # IMU yaw rate correction. Increase/decrease only after testing 90/180 degree turns.
        self.ANGULAR_SCALE = 0.85
        # Ignore tiny gyro noise around zero when the robot is not meaningfully rotating.
        self.IMU_GYRO_DEADBAND = 0.01

        # Integrated robot pose in the odom frame.
        # x/y/yaw start at zero each time this node starts.
        # AMCL later connects odom to the saved map by publishing map -> odom.
        self.x   = 0.0
        self.y   = 0.0
        self.yaw = 0.0

        # Latest velocity readings from command, motor board, and IMU.
        self.cmd_vx = 0.0
        self.raw_vx = 0.0
        self.vz  = 0.0
        self.imu_vz = 0.0

        # Timestamps let us ignore stale sensor/command data.
        # Without this, the robot could keep "moving" in odom after messages stop.
        self.last_cmd_time = None
        self.last_raw_time = None
        self.last_imu_time = None
        self.last_time = self.get_clock().now()

        # TF publishes odom -> base_link. /odom publishes the same pose as a message.
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # /vel_raw is preferred for forward distance, /cmd_vel is fallback, IMU supplies yaw rate.
        # /cmd_vel: desired speed from Nav2/keyboard/joystick.
        # /vel_raw: board-reported speed, closer to actual movement.
        # /imu/data_raw: angular velocity used for heading changes.
        self.create_subscription(Twist, '/cmd_vel',      self.cmd_callback, 10)
        self.create_subscription(Twist, '/vel_raw',      self.vel_raw_callback, 10)
        self.create_subscription(Imu,   '/imu/data_raw', self.imu_callback, 10)

        # 20 Hz odometry update loop.
        self.create_timer(0.05, self.publish_odom)
        self.get_logger().info(
            f'Odom started | '
            f'wheel_base={self.WHEEL_BASE}m | '
            f'wheel_radius={self.WHEEL_RADIUS}m | '
            f'primary=/vel_raw fallback=/cmd_vel'
        )

    def cmd_callback(self, msg):
        # Save the commanded forward speed as a backup if board velocity stops updating.
        self.cmd_vx = msg.linear.x * self.CMD_LINEAR_SCALE
        self.last_cmd_time = self.get_clock().now()

    def vel_raw_callback(self, msg):
        # Use measured/board-reported forward velocity, corrected by calibration scale.
        self.raw_vx = msg.linear.x * self.RAW_LINEAR_SCALE
        self.last_raw_time = self.get_clock().now()

    def imu_callback(self, msg):
        # IMU gives the most reliable rotation; sign is inverted to match the robot frame.
        self.imu_vz = -msg.angular_velocity.z * self.ANGULAR_SCALE
        self.last_imu_time = self.get_clock().now()

    def is_recent(self, stamp, now, timeout=0.35):
        # Treat old data as invalid so odom does not drift after commands/sensors stop.
        if stamp is None:
            return False
        return (now - stamp).nanoseconds / 1e9 <= timeout

    def publish_odom(self):
        # Compute elapsed time since the last odom integration step.
        now = self.get_clock().now()
        dt  = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        # Prefer real board velocity. Fall back to command velocity if needed.
        # This keeps odom alive even if /vel_raw briefly disappears.
        raw_recent = self.is_recent(self.last_raw_time, now)
        cmd_recent = self.is_recent(self.last_cmd_time, now)

        if raw_recent:
            vx = self.raw_vx
        elif cmd_recent:
            vx = self.cmd_vx
        else:
            vx = 0.0

        # Angular from IMU only while the robot is moving or being commanded.
        if (raw_recent or cmd_recent) and self.is_recent(self.last_imu_time, now):
            vz = self.imu_vz
            if abs(vz) < self.IMU_GYRO_DEADBAND:
                vz = 0.0
        else:
            vz = 0.0

        # Integrate
        # Differential-drive approximation:
        #   yaw changes from angular velocity
        #   x/y advance in the current heading direction
        self.yaw += vz * dt
        self.x   += vx * math.cos(self.yaw) * dt
        self.y   += vx * math.sin(self.yaw) * dt

        # Publish TF
        # Nav2 requires the TF tree: map -> odom -> base_link -> base_laser.
        # This node owns only odom -> base_link.
        t = TransformStamped()
        t.header.stamp    = now.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id  = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        # For planar motion, roll=pitch=0, so quaternion only needs z and w from yaw.
        t.transform.rotation.z    = math.sin(self.yaw / 2)
        t.transform.rotation.w    = math.cos(self.yaw / 2)
        self.tf_broadcaster.sendTransform(t)

        # Publish Odometry
        # /odom is useful for RViz display and Nav2 state estimation/debugging.
        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_link'
        odom.pose.pose.position.x    = self.x
        odom.pose.pose.position.y    = self.y
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2)
        odom.twist.twist.linear.x    = vx
        odom.twist.twist.angular.z   = vz
        self.odom_pub.publish(odom)

def main():
    # Standard ROS 2 Python node startup.
    rclpy.init()
    rclpy.spin(OdomPublisher())

if __name__ == '__main__':
    main()
