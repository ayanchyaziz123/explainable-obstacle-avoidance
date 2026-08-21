from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='explainable_nav',
            executable='perception_node',
            name='explainable_perception_node',
            output='screen',
        ),
    ])
