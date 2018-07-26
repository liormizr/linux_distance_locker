"""
This is from an interesting blog:
https://www.raspberrypi.org/forums/viewtopic.php?t=47466
"""
import os
import sys
from pathlib import Path
from itertools import cycle
from collections import deque
from subprocess import Popen, run, PIPE, STDOUT

PROGRESS = cycle(['-', '\\', '|', '/'])
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
        nonlocal line, bluetooth_active
        line = line.strip()
        if line in DO_NOT_CARE_SENSOR_MESSAGES:
            return
        if line == 'Not connected.':
            if bluetooth_active:
                queue.appendleft(-255)
            return
        bluetooth_active = True
        value = int(line.replace('Device connected. RSSI: ', ''))
        if value < -1:
            queue.appendleft(value)
            return
        if queue:
            queue.pop()
            return

    def print_state():
        if index:
            # move cursor one line up, delete till end of line
            sys.stdout.write('\033[1A\033[K' * 4)
        sys.stdout.write(
            f'{next(PROGRESS)}\n'
            f'Bluetooth Distance Sensor output:>{line}\n'
            f'Current Queue size:>{queue_size}\n'
            f'Status:>{state}\n'
        )

    def check_screen_save_status():
        screen_saver_status_output = run(
            LOCKER_STATUS_COMMAND.split(),
            universal_newlines=True,
            stdout=PIPE).stdout
        if screen_saver_status_output.startswith(LOCKER_UNLOCK_SCREEN_SAVE_PREFIX):
            return UNLOCK_STATE
        return LOCK_STATE

    with Popen(commend, stderr=STDOUT, stdout=PIPE, universal_newlines=True) as process:
        for index, line in enumerate(iter(process.stdout.readline, '')):
            parse_line()
            queue_size = len(queue)
            state = check_screen_save_status()
            if state == UNLOCK_STATE and queue_size == queue.maxlen:
                state = LOCK_STATE
                run(LOCKER_LOCK_COMMAND.split())
            elif state == LOCK_STATE and queue_size < 4:
                state = UNLOCK_STATE
                run(LOCKER_UNLOCK_COMMAND.split())
            print_state()
