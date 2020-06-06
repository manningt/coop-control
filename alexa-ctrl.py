import logging
import os

from flask import Flask
from flask_ask import Ask, request, session, question, statement
import RPi.GPIO as GPIO

app = Flask(__name__)
ask = Ask(app, "/")
#logging.getLogger('flask_ask').setLevel(logging.DEBUG)
logging.getLogger('flask_ask').setLevel(logging.INFO)

STATUSON = ['on', 'high']
STATUSOFF = ['off', 'low']

PIN_LIGHT_RELAY = 23
# refer to this page for gpio_function returns

@ask.launch
def launch():
    speech_text = 'Welcome to Raspberry Pi Automation.'
    return question(speech_text).reprompt(speech_text).simple_card(speech_text)


@ask.intent('GpioIntent', mapping={'next_state': 'next_state'})
def GpioIntent(next_state):
    response = 'Sorry, bogus requested state: {}.'.format(next_state)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # if (GPIO.gpio_function(PIN_LIGHT_RELAY) != GPIO.OUT):
    GPIO.setup(PIN_LIGHT_RELAY, GPIO.OUT)
    curr_pin_state = GPIO.input(PIN_LIGHT_RELAY)
    # print("Received new state: {}".format(next_state))
    next_pin_state = None
    if next_state in STATUSON:
        next_pin_state = GPIO.HIGH
    if next_state in STATUSOFF:
        next_pin_state = GPIO.LOW
    print("Current state: {} -- Next state: {} ".format(curr_pin_state, next_pin_state))
    if curr_pin_state == next_pin_state:
        response = 'the light is already {}'.format(next_state)
        next_pin_state = None
    if next_pin_state is not None:
        response = 'turning {} light'.format(next_state)
        GPIO.output(PIN_LIGHT_RELAY, next_pin_state)
    return statement(response)
    # if next_state in STATUSON:
    #     GPIO.output(PIN_LIGHT_RELAY, GPIO.HIGH)
    #     return statement('turning {} light'.format(next_state))
    # elif next_state in STATUSOFF:
    #     GPIO.output(PIN_LIGHT_RELAY, GPIO.LOW)
    #     return statement('turning {} light'.format(next_state))
    # else:
    #     return statement('Sorry bogus requested state: {}.'.format(next_state))


@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'You can say hello to me!'
    return question(speech_text).reprompt(speech_text).simple_card('HelloWorld', speech_text)


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    if 'ASK_VERIFY_REQUESTS' in os.environ:
        verify = str(os.environ.get('ASK_VERIFY_REQUESTS', '')).lower()
        if verify == 'false':
            app.config['ASK_VERIFY_REQUESTS'] = False
    app.run(debug=True)
