#!/usr/bin/env python3

from time import sleep
import RPi.GPIO as GPIO
pin = 25
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin, GPIO.OUT)

turn_on = (GPIO.input(pin) ^ 1) & 1
print("setting relay to: {}".format(turn_on))
GPIO.output(pin, turn_on)

sleep(10)
turn_off = (GPIO.input(pin) ^ 1) & 1
print("setting relay to: {}".format(turn_off))
GPIO.output(pin, turn_off)

