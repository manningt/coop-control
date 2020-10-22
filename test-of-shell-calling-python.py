#!/usr/bin/env python3
import subprocess
import argparse

parser = argparse.ArgumentParser(description='Test subprocess.run (wait for process to finish) and .Popen (dont wait)')
parser.add_argument(dest='on_off', type=int, nargs='?', choices=[0, 1], default=0, help='0 for off; 1 for on')
parser.add_argument('-d', '--dont_wait', dest='dont_wait', action='store_true', help='run process without waiting for the process to complete')
args = parser.parse_args()

SCRIPT = "/home/pi/coop/light.py"

if args.dont_wait:
    p = subprocess.Popen([SCRIPT, str(args.on_off)], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
    print("called {} without waiting for output.".format(SCRIPT))
else:
    result = subprocess.run([SCRIPT, str(args.on_off)], capture_output=True)
    if result.returncode > 0:
         print("{} returned an non-zero return code: {}".format(SCRIPT, result.returncode))
    print("{} output: {}".format(SCRIPT, result.stdout.decode("utf-8").split('\n')[0]))
