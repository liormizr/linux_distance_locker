import sys
import argparse
from distance_locker import bluetooth_distance_locker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--address',
        required=True,
        help='Your phone or another bluetooth device MAC Address')
    options = parser.parse_args()
    return bluetooth_distance_locker(options.address)

if __name__ == '__main__':
    sys.exit(main())
