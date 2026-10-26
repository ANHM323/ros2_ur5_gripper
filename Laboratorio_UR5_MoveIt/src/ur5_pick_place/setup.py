from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ur5_pick_place'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Daniel',
    maintainer_email='danymarjosu@gmail.com',
    description='Rutina pick and place simulada para UR5 con gripper',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'pick_place_node = ur5_pick_place.pick_place_node:main',
            'pick_place_ursim = ur5_pick_place.pick_place_ursim:main',
            'gripper_tool_io = ur5_pick_place.gripper_tool_io:main'
        ],
    },
)
