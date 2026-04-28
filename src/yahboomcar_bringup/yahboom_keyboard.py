#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import tty
import termios

msg = """
---------------------------
Yahboom 4WD Robot Keyboard Control
---------------------------
        w
   a    s    d
        x

w : forward
x : backward
a : rotate left
d : rotate right
s : stop

q/z : increase/decrease all speeds 10%
CTRL-C to quit
---------------------------
"""

moveBindings = {
    'w': (1,  0),
    'x': (-1, 0),
    'a': (0,  1),
    'd': (0, -1),
    's': (0,  0),
}

speedBindings = {
    'q': 1.1,
    'z': 0.9,
}

def getKey(settings):
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    rclpy.init()
    node = rclpy.create_node('yahboom_keyboard')
    pub = node.create_publisher(Twist, 'cmd_vel', 1)

    settings = termios.tcgetattr(sys.stdin)
    speed = 0.3
    turn  = 1.5

    print(msg)
    print(f"Speed: {speed:.2f}  Turn: {turn:.2f}")

    try:
        while True:
            key = getKey(settings)
            twist = Twist()

            if key in moveBindings:
                x, th = moveBindings[key]
                twist.linear.x  = speed * x
                twist.angular.z = turn  * th
            elif key in speedBindings:
                speed = speed * speedBindings[key]
                turn  = turn  * speedBindings[key]
                print(f"Speed: {speed:.2f}  Turn: {turn:.2f}")
                continue
            elif key == '\x03':  # CTRL+C
                break
            else:
                twist.linear.x  = 0.0
                twist.angular.z = 0.0

            pub.publish(twist)

    except Exception as e:
        print(e)
    finally:
        # Stop robot on exit
        twist = Twist()
        pub.publish(twist)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
