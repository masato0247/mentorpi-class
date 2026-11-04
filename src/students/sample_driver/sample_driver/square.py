import rclpy

from rclpy.node import Node

from geometry_msgs.msg import Twist
 
class Square(Node):

    def __init__(self):

        super().__init__('square')

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

        self.count = 0

        self.create_timer(0.1, self.loop)   # 0.1秒ごとに loop を実行
 
    def loop(self):

        msg = Twist()

        step = self.count % 30              # 30回（3秒）で1サイクル

        if step < 20:

            msg.linear.x = 0.3              # 最初の2秒はまっすぐ進む

        else:

            msg.angular.z = 1.57            # 残りの1秒で90度回る

        self.pub.publish(msg)

        self.count += 1
 
def main():

    rclpy.init()

    rclpy.spin(Square())
 
if __name__ == '__main__':

    main()
 