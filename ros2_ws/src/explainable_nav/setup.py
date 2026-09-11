from setuptools import find_packages, setup

package_name = 'explainable_nav'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/explainable_nav.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Azizur Rahman',
    maintainer_email='azizurusa22@gmail.com',
    description='Grad-CAM explainable perception overlay for TurtleBot3 obstacle avoidance',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'perception_node = explainable_nav.perception_node:main',
            'data_collector_node = explainable_nav.data_collector_node:main',
        ],
    },
)
