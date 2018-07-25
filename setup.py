#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

setup(
    name='distance_locker',
    version='0.0.1',
    url='https://github.com/liormizr/linux_distance_locker',
    author='Lior Mizrahi',
    author_email='li.mizr@gmail.com',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'distance_locker = distance_locker.__main__:main',
    ]},
)
