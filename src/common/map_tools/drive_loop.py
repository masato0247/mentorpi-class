#!/usr/bin/env python3
"""決まったルートを自動で走らせるプログラム（実験で毎回同じ走り方にするため）.
 
ロボットの位置（/odom）を見ながら、目標の点を順番にたどる（ピュアパシュート法）。
スタート地点から右の壁ぞいへ出て、障害物の外側を左回りに1周する。
使い方:
  python3 drive_loop.py --ros-args -p use_sim_time:=true
"""
import math
 
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
 
# 通る点 [m]（スタート地点が (0, 0)、ロボットは最初 +x の向き）
WAYPOINTS = [
    (0.0, 0.0),     # スタート
    (1.9, 0.0),     # 右の壁ぞいへ
    (1.9, 1.9),     # 右上の角
    (-1.9, 1.9),    # 左上の角
    (-1.9, -1.9),   # 左下の角
    (1.9, -1.9),    # 右下の角
    (1.9, 0.0),     # 1周して戻る
    (1.9, 0.5),     # 少し重ねて走ってから止まる
]
 
SPEED = 0.15        # 前に進む速さ [m/s]
LOOKAHEAD = 0.4     # どれだけ先の点をめざすか [m]
MIN_RADIUS = 0.3    # 曲がるときの最小の半径 [m]（実機の前輪が切れる角度に合わせる）
STEP = 0.02         # ルートを細かい点に分ける間隔 [m]
 
 
def make_path(points, step):
    """角の点の間を、細かい点でうめる."""
    path = [points[0]]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(1, n + 1):
            path.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n))
    return path
 
 
class DriveLoop(Node):
 
    def __init__(self):
        super().__init__('drive_loop')
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        self.path = make_path(WAYPOINTS, STEP)
        self.index = 0          # ルートのどこまで進んだか
        self.pose = None        # (x, y, 向き)
        self.finished = False
        self.last_log = None
        self.create_timer(0.05, self.loop)
 
    def on_odom(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (p.x, p.y, yaw)
 
    def loop(self):
        if self.finished:
            return
        if self.pose is None:
            return  # まだ /odom が届いていない
        x, y, yaw = self.pose
        now = self.get_clock().now().nanoseconds / 1e9
        if self.last_log is None:
            self.last_log = now
            self.get_logger().info('走行を開始します')
 
        # 今いちばん近いルート上の点（前にしか進まない）
        best = self.index
        best_d = float('inf')
        for i in range(self.index, min(self.index + 100, len(self.path))):
            d = math.hypot(self.path[i][0] - x, self.path[i][1] - y)
            if d < best_d:
                best, best_d = i, d
        self.index = best
 
        # ゴールに着いたら止まる
        last = len(self.path) - 1
        gx, gy = self.path[last]
        if self.index >= last - 2 or (self.index > last - 20 and math.hypot(gx - x, gy - y) < 0.1):
            self.pub.publish(Twist())
            self.get_logger().info('1周しました。止まります（Ctrl + C で終了）')
            self.finished = True
            return
 
        # LOOKAHEAD だけ先の点をめざす
        target = self.path[last]
        for i in range(self.index, len(self.path)):
            if math.hypot(self.path[i][0] - x, self.path[i][1] - y) >= LOOKAHEAD:
                target = self.path[i]
                break
        dx, dy = target[0] - x, target[1] - y
        dist = max(math.hypot(dx, dy), 1e-3)
        alpha = math.atan2(dy, dx) - yaw
        alpha = math.atan2(math.sin(alpha), math.cos(alpha))
        curvature = 2.0 * math.sin(alpha) / dist
        curvature = max(-1.0 / MIN_RADIUS, min(1.0 / MIN_RADIUS, curvature))
 
        msg = Twist()
        msg.linear.x = SPEED
        msg.angular.z = SPEED * curvature
        self.pub.publish(msg)
 
        if now - self.last_log >= 5.0:
            self.last_log = now
            self.get_logger().info('位置 x=%.2f y=%.2f  進み具合 %d%%' % (x, y, 100 * self.index // last))
 
 
def main():
    rclpy.init()
    node = DriveLoop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.pub.publish(Twist())
    node.destroy_node()
    rclpy.try_shutdown()
 
 
if __name__ == '__main__':
    main()