#!/usr/bin/env python3
from gpio_control import gpio_switch as switch

PIN_LIGHT_RELAY = 24

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Turn coop light on/off')
    parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1], default=0, help=': 0 for on; 1 for off')
    args = parser.parse_args()
    # print("on_off datatype: {}".format(type(args.on_off)))
    print("Result: {}".format(switch(PIN_LIGHT_RELAY, args.on_off)))

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
