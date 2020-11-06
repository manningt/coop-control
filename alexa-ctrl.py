#!/usr/bin/env python3

import logging
import subprocess
from flask import Flask
from flask_ask import Ask, request, session, question, statement
import RPi.GPIO as GPIO
import json
import os

app = Flask(__name__)
ask = Ask(app, "/")
# logger.getLogger('flask_ask').setLevel(logger.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('coop_ctrl.log')
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

STATUSON = ['on', 'high']
STATUSOFF = ['off', 'low']
SHORT_ACTIVATION_MINUTES = 5


@ask.launch
def launch():
    speech_text = 'Hen house control has launched.'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)


@ask.intent('GpioIntent')
def GpioIntent(device, next_state):
    # logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, request.intent.slots.next_state.value))
    logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, next_state))
    if 'test' in device:
        return statement('Hen house control is operational.')

    # read config file to get device options
    os.chdir('/home/pi/coop')
    GPIO_CFG_FILENAME = 'gpio-cfg.json'
    try:
        f = open(GPIO_CFG_FILENAME)
    except:
        return statement("Missing config file: {}".format(GPIO_CFG_FILENAME))

    try:
        relay_cfg_dict = json.load(f)
    except:
        return statement("Bad json format in config file: {}".format(GPIO_CFG_FILENAME))

    f.close()

    command = None
    wait_for_command_complete = True
    for (k, v) in relay_cfg_dict.items():
        if k in device:
            command = "./{}.py".format(k)
            if 'duration' in v:
                wait_for_command_complete = False

    ''' the following could only happen if the device slot in the Alexa-skill has more items for the device slot
        than the config file '''
    if command is None:
        return statement('Unsupported device: {}.'.format(device))

    # next_pin_state is an integer passed as an argument when the python script is called; its translated from on/off
    next_pin_state = None
    if next_state in STATUSON:
        next_pin_state = 1
    elif next_state in STATUSOFF:
        next_pin_state = 0
    elif next_state == 'short':
        next_pin_state = SHORT_ACTIVATION_MINUTES
        wait_for_command_complete = False

    if next_pin_state is None:
        verbal_state = 'off'
    else:
        verbal_state = next_state
        command = [command]
        command.append(str(next_pin_state))

    # logger.info("command: {}".format(command))
    if wait_for_command_complete:
        # execution blocks until the subprocess completes, so the scripts have to complete within 10 seconds
        result = subprocess.run(command, capture_output=True)
        if result.returncode > 0:
            err_string = "error code: {} occurred on calling: {}".format(result.returncode, command)
            logger.error(err_string)
            return statement(err_string)
        result_str = result.stdout.decode("utf-8").split('\n')[0]
        if result_str.startswith("success"):
            return statement('turning {} {}'.format(verbal_state, device))
        elif result_str.startswith("already"):
            return statement('the {} is already {}'.format(device, verbal_state))
        else:
            return statement(result_str)
    else:
        # don't set shell=True; it mucks up the arguments sent to the process.
        p = subprocess.Popen(command, stdin=None, stdout=None, stderr=None, close_fds=True)
        return statement("Activating {}".format(device))


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.run(debug=True)
