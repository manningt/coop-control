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

PIN_DOOR_RELAY = 23
#PIN_LIGHT_RELAY = 24
#PIN_HEATER_RELAY = 25

def operate_door(delay):
    logger.debug("operate_door thread started")
    from time import sleep
    import RPi.GPIO as GPIO

    pin = PIN_DOOR_RELAY
    # pin = PIN_HEATER_RELAY #AC relay pin for testing

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT, initial=0)
        GPIO.output(pin, 0)
        logger.debug("Initializing relay to 0 for 4 seconds.")
        sleep(4)

        GPIO.output(pin, 1)
        logger.info("operate_door thread: Setting relay to 1 for {} seconds.".format(delay))
        sleep(delay)

        GPIO.output(pin, 0)
        logger.debug("Final: turning off relay.")
    except Exception as e:
        logger.exception(e)
        logger.error("Exception in door relay control thread: {}".format(str(e)))


@ask.launch
def launch():
    speech_text = 'Hen house control is operational.'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)


@ask.intent('GpioIntent')
def GpioIntent(device, next_state):
    if next_state is None:
        logger.info("Slot_Device: {}  --- Slot_next_state is None".format(device))
    else:
        # logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, request.intent.slots.next_state.value))
        logger.info("Slot_Device: {} --- Slot_next_state: {}".format(device, next_state))

    if next_state in STATUSON:
        next_pin_state = 1
    elif next_state in STATUSOFF:
        next_pin_state = 0
    elif next_state is None:
        response = 'Sorry, need to specify {} on or off.'.format(device)
    else:
        response = 'Sorry, bogus requested state: {}.'.format(next_state)

    command = None
    if device in DEVICEDOOR:
        # spawn a thread to turn on door motor for 8 seconds and then turn it off
        door_oper_thread = threading.Thread(target=operate_door, args=(9, ))
        logger.debug("Starting door_oper_thread")
        door_oper_thread.start()
        return statement('Operating {}.'.format(device))
        #!! assumes thread terminates after operation
        # logger.debug("Main    : wait for the thread to finish")
        # x.join()
    elif device in DEVICELIGHT:
        command = "/home/pi/coop/light.py {}".format(next_pin_state)
    elif device in DEVICEHEAT:
        command = "/home/pi/coop/heat.py {}".format(next_pin_state)
    elif device in DEVICETEST:
        return statement('Hen house control is operational.')
    else:
        return statement('Unsupported requested device: {}.'.format(device))

    if command is not None:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        rc = p.returncode
        if err is not None:
            logger.error("error code: {} occurred on calling: {}".format(err, command))
        # print("rc: {}".format(rc))
        if rc == 0:
            return statement('turning {} {}'.format(next_state, device))
        else:
            result = out.decode("utf-8").split('\n')
            if result[0].startswith("already"):
                return statement('the {} is already {}'.format(device, next_state))
            else:
                return statement(result[0])
    else:
        logger.error("Unexpected condition: command is None")
        return statement('Unexpected condition: command is None')



@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.run(debug=True)
