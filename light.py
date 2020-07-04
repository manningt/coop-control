#!/usr/bin/env python3
import sys
from gpio_control import gpio_switch as switch

if __name__ == '__main__':
    import argparse
    # print("called with {}: ".format(sys.argv[0]))
    device = None
    if sys.argv[0].endswith("light.py"):
        device = "lights"
        pin = 24
    elif sys.argv[0].endswith("heat.py"):
        device = "heaters"
        pin = 25
    else:
        sys.exit(6)
    parser = argparse.ArgumentParser(description='Turn coop {} on/off'.format(device))
    parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1], default=0, help=': 0 for off; 1 for on')
    args = parser.parse_args()
    result = switch(pin, args.on_off)
    sys.exit(result)
'''
old routine that toggled the light state for 10 seconds.

from time import sleep
import RPi.GPIO as GPIO
pin = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

turn_on = (GPIO.input(pin) ^ 1) & 1
print("setting relay to: {}".format(turn_on))
GPIO.output(pin, turn_on)

sleep(10)
turn_off = (GPIO.input(pin) ^ 1) & 1
print("setting relay to: {}".format(turn_off))
GPIO.output(pin, turn_off)
'''
