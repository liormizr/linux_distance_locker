#!/usr/bin/env python
from distutils.core import setup
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='distance_locker',
    version='0.0.2',
    url='https://github.com/liormizr/linux_distance_locker',
    author='Lior Mizrahi',
    author_email='li.mizr@gmail.com',
    packages=find_packages(),
    data_files=[('bin', ['bluetooth_distance_sensor.sh'])],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'distance_locker = distance_locker.__main__:main',
    ]},
)
