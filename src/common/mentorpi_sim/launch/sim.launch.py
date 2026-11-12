import os
 
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
 
 
def generate_launch_description():
    world = os.path.join(
        get_package_share_directory('mentorpi_sim'), 'worlds', 'practice.sdf')
 
    # Gazeboを起動（-r は起動と同時にシミュレーションを開始する指定）
    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', '-r', world],
        output='screen')
 
    # ROS 2 と Gazebo の間でデータを中継する
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/scan_raw@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
        ],
        output='screen')
 
    # ロボットの中心(base_link)から見たLiDAR(lidar_link)の位置：真上11cm
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0', '--z', '0.11',
                   '--frame-id', 'base_link', '--child-frame-id', 'lidar_link'],
        parameters=[{'use_sim_time': True}],
        output='screen')
 
    return LaunchDescription([gazebo, bridge, lidar_tf])