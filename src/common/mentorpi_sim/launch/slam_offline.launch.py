import os
 
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch.actions import DeclareLaunchArgument

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node

from launch_ros.parameter_descriptions import ParameterValue
 
 
def generate_launch_description():

    share = get_package_share_directory('mentorpi_sim')

    params = os.path.join(share, 'config', 'slam_params.yaml')

    rviz_config = os.path.join(share, 'rviz', 'slam.rviz')
 
    # 起動するときに resolution:=0.02 のように地図の細かさを選べる（指定しなければ 0.05）

    resolution_arg = DeclareLaunchArgument(

        'resolution', default_value='0.05',

        description='地図の1マスの大きさ[m]')

    resolution = ParameterValue(LaunchConfiguration('resolution'), value_type=float)
 
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

        parameters=[params, {'use_sim_time': True, 'resolution': resolution}],

        output='screen')
 
    # 地図を表示する画面（RViz）

    rviz = Node(

        package='rviz2',

        executable='rviz2',

        arguments=['-d', rviz_config],

        parameters=[{'use_sim_time': True}],

        output='screen')
 
    return LaunchDescription([resolution_arg, lidar_tf, slam, rviz])
 