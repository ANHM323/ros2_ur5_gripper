# Driver UR conectado a URSim (o robot real) mostrando el UR5 con gripper en RViz
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_ip = LaunchConfiguration('robot_ip')
    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution(
            [FindPackageShare('ur_robot_driver'), 'launch', 'ur_control.launch.py'])),
        launch_arguments={
            'ur_type': 'ur5',
            'robot_ip': robot_ip,
            'launch_rviz': 'true',
            'description_launchfile': PathJoinSubstitution(
                [FindPackageShare('ur5_pick_place'), 'launch', 'ur5_gripper_rsp.launch.py']),
        }.items(),
    )
    gripper = Node(package='ur5_pick_place', executable='gripper_tool_io', output='screen')
    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='192.168.56.101'),
        driver, gripper,
    ])
