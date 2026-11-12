import os
 
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch_ros.actions import Node
 
 
def generate_launch_description():

    share = get_package_share_directory('mentorpi_sim')

    params = os.path.join(share, 'config', 'slam_params.yaml')

    rviz_config = os.path.join(share, 'rviz', 'slam.rviz')
 
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
 
    return LaunchDescription([slam, rviz])
 