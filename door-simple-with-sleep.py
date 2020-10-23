#!/usr/bin/env python3

from time import sleep
from gpio_control import gpio_switch as switch
import sys
import argparse

parser = argparse.ArgumentParser(description='Energizes relay for N seconds')
parser.add_argument(dest='relay_pin', type=int, nargs='?', default=23, help='GPIO pin used to activate relay')
parser.add_argument('-a', dest='activation_time', type=int, default=10, help='seconds to leave relay on')
args = parser.parse_args()

if __name__ == '__main__':
    result = switch(args.relay_pin, 1)
    if 'error' in result:
        print(result)
        sys.exit(1)

    sleep(args.activation_time)
    result = switch(args.relay_pin, 0)
    if 'error' in result:
        print(result)
        sys.exit(1)

    print("GPIO pin {} activated for {} seconds".format(args.relay_pin, args.activation_time))
    sys.exit(0)
