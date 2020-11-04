#!/usr/bin/env python3

"""
uses gpio_control on Raspberry Pi to turn on/off a GPIO pin, where the pins controls a relay
 the string put in stdout:
    - if the GPIO pin is already in the requested state, gpio_control returns 'already 0 (or 1)'
    - if the pin is successfully switched, then gpio_control returns 'success'
  return code is set to 1 only if gpio_control returns something other than already 1 or success
"""
import sys
import json
import argparse
from time import sleep
from gpio_control import gpio_switch as switch

if __name__ == '__main__':
    GPIO_CFG_FILENAME = 'gpio-cfg.json'
    SHORT_ACTIVATION_MINUTES = 2
    pin = None
    duration = None
    shell_rc = 1

    try:
        f = open(GPIO_CFG_FILENAME)
    except:
        print("Missing config file: {}".format(GPIO_CFG_FILENAME))
        sys.exit(1)

    try:
        relay_cfg_dict = json.load(f)
    except:
        print("Bad json format in config file: {}".format(GPIO_CFG_FILENAME))
        sys.exit(1)
    f.close()

    parser = argparse.ArgumentParser(description='Turn coop devices on/off')
    parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1, SHORT_ACTIVATION_MINUTES], default=0, \
                        help=': 0 for off; 1 for on; 7 turn on for 7 minutes')
    args = parser.parse_args()
    # print("called with {}: ".format(sys.argv[0]))

    for (k, v) in relay_cfg_dict.items():
        if k in sys.argv[0]:
            device = k
            pin = v['relay']
            if 'duration' in v:
                duration = v['duration']

    if duration is None and args.on_off > 1:
        # activation duration in seconds
        duration = SHORT_ACTIVATION_MINUTES * 60
    if pin is not None:
        if duration is None:
            if args.on_off > 1:
                print("Error: on_off arg '{}' should be 0 or 1 when activation duration is not set".format(args.on_off))
                sys.exit(1)
            result = switch(pin, args.on_off)
            print(result)
            if 'success' in result or 'already' in result:
                shell_rc = 0
            sys.exit(shell_rc)
        else:
            # switching off first, in case it was left on; this is important for the motor
            result = switch(pin, 0)
            sleep(1)
            if 'error' in result:
                print(result)
                sys.exit(1)
            result = switch(pin, 1)
            sleep(duration)
            switch(pin, 0)
            sys.exit(0)
    else:
        print("unrecognized device: {}".format(sys.argv[0]))
        sys.exit(shell_rc)
