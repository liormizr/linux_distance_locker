import os
from typing import Union
from pathlib import Path
from collections import deque
from subprocess import run, Popen, STDOUT, PIPE

UNLOCK_STATE = 'UNLOCK'
LOCK_STATE = 'LOCK'
SENSOR_SCRIPT_PATH = Path('bluetooth_distance_sensor.sh')
DO_NOT_CARE_SENSOR_MESSAGES = [
    'Read RSSI failed: Input/output error',
    'Attempting connection...',
    'GONE!',
    'HERE!',
]
LOCKER_LOCK_COMMAND = os.getenv(
    'LOCKER_LOCK_COMMAND',
    'gnome-screensaver-command --lock')
LOCKER_UNLOCK_COMMAND = os.getenv(
    'LOCKER_UNLOCK_COMMAND',
    'gnome-screensaver-command --deactivate')
LOCKER_STATUS_COMMAND = os.getenv(
    'LOCKER_STATUS_COMMAND',
    'gnome-screensaver-command --query')
LOCKER_UNLOCK_SCREEN_SAVE_PREFIX = os.getenv(
    'LOCKER_UNLOCK_SCREEN_SAVE_PREFIX',
    'The screensaver is inactive')


def bluetooth_distance_locker(device_mac_address):
    commend = [str(SENSOR_SCRIPT_PATH), device_mac_address]
    queue = deque(maxlen=5)
    state = UNLOCK_STATE
    bluetooth_active = False

    def parse_line():
        """
        Parse the child process line
        * check if relevant
        * modify the queue
        """
        ...

    def print_state():
        """
        Print nice status to stdout
        """
        ...

    def check_screen_save_status() -> Union[UNLOCK_STATE, LOCK_STATE]:
        """
        Check status of the screen save
        """
        ...

    with Popen(commend,
               stderr=STDOUT, stdout=PIPE,
               bufsize=1, universal_newlines=True) as process:
        for line in iter(process.stdout.readline, ''):
            parse_line()
            state = check_screen_save_status()

            if state == UNLOCK_STATE and len(queue) == queue.maxlen:
                state = LOCK_STATE
                run(LOCKER_LOCK_COMMAND.split())
            elif state == LOCK_STATE and len(queue) < 4:
                state = UNLOCK_STATE
                run(LOCKER_UNLOCK_COMMAND.split())
            print_state()
