#!/usr/bin/env python3
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
        self.vx     = 0.0
        self.vz     = 0.0
        self.imu_yaw = None
        self.last_vel_raw_time = None
        self.last_cmd_time = None
        self.last_imu_time = None
        self.last_time = self.get_clock().now()

        self.declare_parameter('linear_source', 'cmd_vel')
        self.declare_parameter('linear_scale', 1.0)
        self.declare_parameter('angular_scale', 1.0)
        self.declare_parameter('angular_sign', -1.0)
        self.declare_parameter('stale_timeout', 0.35)

        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        self.create_subscription(Twist, '/vel_raw', self.vel_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.create_subscription(Imu, '/imu/data_raw', self.imu_callback, 10)

        self.create_timer(0.05, self.publish_odom)
        self.get_logger().info('Odom publisher started (cmd_vel linear + measured/IMU angular)!')

    def vel_callback(self, msg):
        angular_sign = self.get_parameter('angular_sign').value
        self.raw_vx = msg.linear.x
        self.raw_vz = angular_sign * msg.angular.z
        self.last_vel_raw_time = self.get_clock().now()

    def cmd_callback(self, msg):
        angular_sign = self.get_parameter('angular_sign').value
        self.cmd_vx = msg.linear.x
        self.cmd_vz = angular_sign * msg.angular.z
        self.last_cmd_time = self.get_clock().now()

    def imu_callback(self, msg):
        angular_sign = self.get_parameter('angular_sign').value
        self.imu_vz = angular_sign * msg.angular_velocity.z
        self.last_imu_time = self.get_clock().now()

    def is_recent(self, stamp, now):
        if stamp is None:
            return False
        stale_timeout = self.get_parameter('stale_timeout').value
        age = (now - stamp).nanoseconds / 1e9
        return age <= stale_timeout

    def choose_linear_velocity(self, now):
        linear_source = self.get_parameter('linear_source').value
        linear_scale = self.get_parameter('linear_scale').value

        if linear_source == 'vel_raw' and self.is_recent(self.last_vel_raw_time, now):
            return self.raw_vx * linear_scale
        if self.is_recent(self.last_cmd_time, now):
            return self.cmd_vx * linear_scale
        if self.is_recent(self.last_vel_raw_time, now):
            return self.raw_vx * linear_scale
        return 0.0

    def choose_angular_velocity(self, now):
        angular_scale = self.get_parameter('angular_scale').value

        if self.is_recent(self.last_vel_raw_time, now) and abs(self.raw_vz) > 0.001:
            return self.raw_vz * angular_scale
        if self.is_recent(self.last_imu_time, now):
            return self.imu_vz * angular_scale
        if self.is_recent(self.last_cmd_time, now):
            return self.cmd_vz * angular_scale
        return 0.0

    def publish_odom(self):
        now = self.get_clock().now()
        dt  = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now

        self.vx = self.choose_linear_velocity(now)
        self.vz = self.choose_angular_velocity(now)

        # Integrate planar robot motion.
        self.yaw += self.vz * dt
        self.x   += self.vx * math.cos(self.yaw) * dt
        self.y   += self.vx * math.sin(self.yaw) * dt

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

        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_link'
        odom.pose.pose.position.x    = self.x
        odom.pose.pose.position.y    = self.y
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2)
        odom.twist.twist.linear.x    = self.vx
        odom.twist.twist.angular.z   = self.vz
        self.odom_pub.publish(odom)

def main():
    rclpy.init()
    rclpy.spin(OdomPublisher())

if __name__ == '__main__':
    main()
