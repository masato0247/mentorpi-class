import os

import tempfile
 
import yaml

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription

from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo, OpaqueFunction

from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node
 
 
def make_world(context):

    """選んだLiDARの設定をワールドファイルに書き込み、Gazeboを起動する."""

    share = get_package_share_directory('mentorpi_sim')

    lidar = LaunchConfiguration('lidar').perform(context)
 
    with open(os.path.join(share, 'config', 'lidar_profiles.yaml')) as f:

        profiles = yaml.safe_load(f)

    if lidar not in profiles:

        raise RuntimeError(

            'LiDARの設定 "' + lidar + '" がありません。使えるのは ' + str(list(profiles)) + ' です')

    p = profiles[lidar]
 
    with open(os.path.join(share, 'worlds', 'practice.sdf')) as f:

        text = f.read()

    values = {

        'LIDAR_SAMPLES': p['samples'],

        'LIDAR_RANGE_MIN': p['range_min'],

        'LIDAR_RANGE_MAX': p['range_max'],

        'LIDAR_NOISE_STDDEV': p['noise_stddev'],

    }

    for key, value in values.items():

        text = text.replace('{{' + key + '}}', str(value))
 
    world = os.path.join(tempfile.gettempdir(), 'mentorpi_practice_' + lidar + '.sdf')

    with open(world, 'w') as f:

        f.write(text)
 
    return [

        LogInfo(msg='LiDARの設定: ' + lidar + ' ' + str(p)),

        ExecuteProcess(cmd=['ign', 'gazebo', '-r', world], output='screen'),

    ]
 
 
def generate_launch_description():

    # 起動するときに lidar:=A か lidar:=B を選ぶ（指定しなければ A）

    lidar_arg = DeclareLaunchArgument(

        'lidar', default_value='A',

        description='LiDARの設定（config/lidar_profiles.yaml の名前）')
 
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
 
    return LaunchDescription([

        lidar_arg,

        OpaqueFunction(function=make_world),

        bridge,

        lidar_tf,

    ])
 