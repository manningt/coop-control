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

import logging

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename="command.log",
)
Logger = logging.getLogger(__name__)
Logger.setLevel(logging.INFO)

if __name__ == '__main__':
    GPIO_CFG_FILENAME = 'gpio-cfg.json'
    pin = None
    duration = None
    shell_rc = 1

    parser = argparse.ArgumentParser(description='Turn coop devices on/off')
    parser.add_argument('on_off', type=int, nargs='?', choices=range(0, 8), default=0, \
                        help=': 0 for off; 1 for on; 2..7 to turn on for that many minutes')
    parser.add_argument('-p', '--pin', dest='gpio_pin', type=int, nargs='?', help='GPIO pin used to activate relay')
    args = parser.parse_args()
    Logger.info("called with: {}".format(sys.argv[1:]))
    # print("on_off: {}  gpio_pin: {}".format(args.on_off, args.gpio_pin))

    if args.gpio_pin is None:
        # read config file to get pin number
        try:
            f = open(GPIO_CFG_FILENAME)
        except:
            Logger.error("Missing config file: {}".format(GPIO_CFG_FILENAME))
            sys.exit(shell_rc)

        try:
            relay_cfg_dict = json.load(f)
        except:
            Logger.error("Bad json format in config file: {}".format(GPIO_CFG_FILENAME))
            sys.exit(shell_rc)
        f.close()

        for (k, v) in relay_cfg_dict.items():
            if k in sys.argv[0]:
                device = k
                pin = v['relay']
                if 'duration' in v:
                    duration = v['duration']
    else:
        pin = args.gpio_pin

    if pin is None:
        Logger.error("unrecognized device: {}".format(sys.argv[0]))
        sys.exit(shell_rc)

    if duration is None and args.on_off > 1:
        # activation duration in seconds
        duration = args.on_off * 60

    if duration is None:
        result = switch(pin, args.on_off)
        if 'success' in result or 'already' in result:
            shell_rc = 0
            Logger.info(result)
        else:
            Logger.error(result)
        sys.exit(shell_rc)
    else:
        # switching off first, in case it was left on; this is important for the motor
        result = switch(pin, 0)
        sleep(1)
        if 'error' in result:
            Logger.error(result)
            sys.exit(1)
        result = switch(pin, 1)
        sleep(duration)
        switch(pin, 0)
        print("success: GPIO pin {} activated for {} seconds".format(pin, duration))
        sys.exit(0)
