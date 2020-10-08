#!/usr/bin/env python3
#import os
import subprocess
import argparse
import binascii

parser = argparse.ArgumentParser(description='Test os.system')
parser.add_argument('on_off', type=int, nargs='?', choices=[0, 1], default=0, help=': 0 for off; 1 for on')
args = parser.parse_args()

cmd = "/home/pi/coop/light.py {}".format(args.on_off)
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
out, err = p.communicate()
rc = p.returncode
if err is not None:
    print("error code: {} occurred on calling: {}".format(err,cmd))
# print("rc: {}".format(rc))
if rc > 0:
    print("script {} returned an non-zero return code: {}".format(cmd,rc))
result = out.decode("utf-8").split('\n')
print("output: " + result[0])
