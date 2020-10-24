#!/usr/bin/env python3

import logging
import subprocess

from flask import Flask
from flask_ask import Ask, request, session, question, statement
import threading
import RPi.GPIO as GPIO

app = Flask(__name__)
ask = Ask(app, "/")
# logger.getLogger('flask_ask').setLevel(logger.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('coop_ctrl.log')
formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

STATUSON = ['on', 'high']
STATUSOFF = ['off', 'low']
DEVICELIGHT = ['light', 'lights']
DEVICEHEAT = ['heat', 'heater']
DEVICEDOOR = ['door']
DEVICETEST = ['test']


@ask.launch
def launch():
    speech_text = 'Hen house control is operational.'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)


@ask.intent('GpioIntent')
def GpioIntent(device, next_state):
    if next_state is None:
        logger.info("Slot_Device: {}  --- Slot_next_state is None".format(device))
        response = 'Sorry, need to specify {} on or off.'.format(device)
    else:
        # logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, request.intent.slots.next_state.value))
        logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, next_state))
        if next_state in STATUSON:
            next_pin_state = 1
        elif next_state in STATUSOFF:
            next_pin_state = 0
        else:
            next_pin_state = None
            response = 'Sorry, unknown requested state: {} for {}.'.format(next_state, device)

    command = None
    wait_for_command_complete = True
    if device in DEVICEDOOR:
        command = "/home/pi/coop/door.py"
        wait_for_command_complete = False
    elif device in DEVICELIGHT:
        command = "/home/pi/coop/light.py"
    elif device in DEVICEHEAT:
        command = "/home/pi/coop/heat.py"
    elif device in DEVICETEST:
        return statement('Hen house control is operational.')
    else:
        return statement('Unsupported requested device: {}.'.format(device))

    if command is not None:
        if wait_for_command_complete:
            # execution blocks until the subprocess completes, so the scripts have to complete within 10 seconds
            result = subprocess.run([command, str(next_pin_state)], capture_output=True)
            if result.returncode > 0:
                err_string = "error code: {} occurred on calling: {}".format(result.returncode, command)
                logger.error(err_string)
                return statement(err_string)
            result_str = result.stdout.decode("utf-8").split('\n')[0]
            if result_str.startswith("success"):
                return statement('turning {} {}'.format(next_state, device))
            if result_str.startswith("already"):
                return statement('the {} is already {}'.format(device, next_state))
            else:
                return statement(result_str)
        else:
            p = subprocess.Popen(command, shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            return statement("Operating Door")
    else:
        err_string = "Unexpected condition: command is None"
        logger.error(err_string)
        return statement(err_string)


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.run(debug=True)
