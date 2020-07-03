#!/usr/bin/env python3
from gpio_control import gpio_switch as switch
# PIN_HEAT_RELAY = 25

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Turn coop light on/off')
    parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1], default=0, help=': 0 for oFF; 1 for oN')
    args = parser.parse_args()
    print("Result: {}".format(switch(25, args.on_off)))
