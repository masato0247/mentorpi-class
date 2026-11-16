import os
 
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
 
 
def generate_launch_description():
    share = get_package_share_directory('mentorpi_sim')
    params = os.path.join(share, 'config', 'slam_params.yaml')
    rviz_config = os.path.join(share, 'rviz', 'slam.rviz')
 
    # LiDARの取り付け位置（記録には入れず、地図を作るときにここで与える）
    lidar_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0', '--z', '0.11',
                   '--frame-id', 'base_link', '--child-frame-id', 'lidar_link'],
        parameters=[{'use_sim_time': True}],
        output='screen')
 
    # 地図作成（slam_toolbox）
    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[params, {'use_sim_time': True}],
        output='screen')
 
    # 地図を表示する画面（RViz）
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen')
 
    return LaunchDescription([lidar_tf, slam, rviz])