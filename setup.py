#!/usr/bin/env python
from distutils.core import setup

setup(
    name='distance_locker',
    version='0.0.1',
    url='https://github.com/liormizr/linux_distance_locker',
    author='Lior Mizrahi',
    author_email='li.mizr@gmail.com',
    py_modules=['distance_locker'],
    scripts=['bluetooth_distance_sensor.sh'],
    entry_points={
        'console_scripts': [
            'distance_locker = distance_locker:main',
    ]},
)
