#!/usr/bin/env python3
import sys
from gpio_control import gpio_switch as switch

if __name__ == '__main__':
    shell_rc = 1 #default to error
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
        print("Invalid device: {}".format(sys.argv[0]))
        sys.exit(shell_rc)
    parser = argparse.ArgumentParser(description='Turn coop {} on/off'.format(device))
    parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1], default=0, help=': 0 for off; 1 for on')
    args = parser.parse_args()
    result = switch(pin, args.on_off)
    print(result)
    if 'success' in result:
        shell_rc = 0
    sys.exit(shell_rc)
