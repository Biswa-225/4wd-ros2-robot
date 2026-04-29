#!/usr/bin/env python3
# =============================================
# Odometry Publisher
# Robot: 4WD Differential Drive
# Wheel diameter:  80mm  → radius = 0.04m
# Wheel base:      95mm  → 0.095m
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
        super().__init__('odom_publisher')
        self.x   = 0.0
        self.y   = 0.0
        self.yaw = 0.0
        self.raw_vx = 0.0
        self.raw_vz = 0.0
        self.cmd_vx = 0.0
        self.cmd_vz = 0.0
        self.imu_vz = 0.0
        self.last_vel_raw_time = None
        self.last_cmd_time     = None
        self.last_imu_time     = None
        self.last_time = self.get_clock().now()

        # =============================================
        # ROBOT PHYSICAL PARAMETERS (measured)
        # =============================================
        self.WHEEL_RADIUS = 0.040   # 80mm diameter → 40mm radius
        self.WHEEL_BASE   = 0.095   # 95mm between left and right wheels
        # =============================================

        self.declare_parameter('linear_source',  'cmd_vel')
        self.declare_parameter('linear_scale',   1.0)
        self.declare_parameter('angular_scale',  1.0)
        self.declare_parameter('angular_sign',  -1.0)
        self.declare_parameter('stale_timeout',  0.35)

        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        self.create_subscription(Twist, '/vel_raw',     self.vel_callback, 10)
        self.create_subscription(Twist, '/cmd_vel',     self.cmd_callback, 10)
        self.create_subscription(Imu,   '/imu/data_raw',self.imu_callback, 10)

        self.create_timer(0.05, self.publish_odom)
        self.get_logger().info(
            f'Odom publisher started | '
            f'wheel_radius={self.WHEEL_RADIUS}m | '
            f'wheel_base={self.WHEEL_BASE}m'
        )

    def vel_callback(self, msg):
        sign = self.get_parameter('angular_sign').value
        self.raw_vx = msg.linear.x
        self.raw_vz = sign * msg.angular.z
        self.last_vel_raw_time = self.get_clock().now()

    def cmd_callback(self, msg):
        sign = self.get_parameter('angular_sign').value
        self.cmd_vx = msg.linear.x
        self.cmd_vz = sign * msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def imu_callback(self, msg):
        sign = self.get_parameter('angular_sign').value
        self.imu_vz = sign * msg.angular_velocity.z
        self.last_imu_time = self.get_clock().now()

    def is_recent(self, stamp, now):
        if stamp is None:
            return False
        age = (now - stamp).nanoseconds / 1e9
        return age <= self.get_parameter('stale_timeout').value

    def choose_linear(self, now):
        src   = self.get_parameter('linear_source').value
        scale = self.get_parameter('linear_scale').value
        if src == 'vel_raw' and self.is_recent(self.last_vel_raw_time, now):
            return self.raw_vx * scale
        if self.is_recent(self.last_cmd_time, now):
            return self.cmd_vx * scale
        if self.is_recent(self.last_vel_raw_time, now):
            return self.raw_vx * scale
        return 0.0

    def choose_angular(self, now):
        scale = self.get_parameter('angular_scale').value
        if self.is_recent(self.last_vel_raw_time, now) and abs(self.raw_vz) > 0.001:
            return self.raw_vz * scale
        if self.is_recent(self.last_imu_time, now):
            return self.imu_vz * scale
        if self.is_recent(self.last_cmd_time, now):
            return self.cmd_vz * scale
        return 0.0

    def publish_odom(self):
        now = self.get_clock().now()
        dt  = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        vx = self.choose_linear(now)
        vz = self.choose_angular(now)

        self.yaw += vz * dt
        self.x   += vx * math.cos(self.yaw) * dt
        self.y   += vx * math.sin(self.yaw) * dt

        # Publish TF
        t = TransformStamped()
        t.header.stamp    = now.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id  = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z    = math.sin(self.yaw / 2)
        t.transform.rotation.w    = math.cos(self.yaw / 2)
        self.tf_broadcaster.sendTransform(t)

        # Publish Odometry
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
    rclpy.init()
    rclpy.spin(OdomPublisher())

if __name__ == '__main__':
    main()
