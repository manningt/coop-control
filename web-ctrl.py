#!/usr/bin/env python3

#from flask import Flask, flash, redirect, render_template, request, session, abort
from flask import Flask, render_template, Response, request, redirect, url_for
import subprocess

IP_PORT = 44 # picked what is hopefully an unused port
DEFAULT_METHODS = ['POST', 'GET']
ACTION_MSG_DOOR = "Activating door..."
ACTION_MSG_LIGHTS_ON = "Turning on lights..."
ACTION_MSG_LIGHTS_OFF = "Turning off lights..."
MAIN_TEMPLATE = 'index.html'
SCRIPTS_DIRECTORY = '/home/pi/coop/'
COMMAND_LIGHTS_OFF = SCRIPTS_DIRECTORY + 'light.py'
COMMAND_LIGHTS_ON = [COMMAND_LIGHTS_OFF, '1']
COMMAND_ACTIVATE_DOOR = SCRIPTS_DIRECTORY + 'door.py'

app = Flask(__name__)

@app.route('/', methods=DEFAULT_METHODS)
def index():
   return render_template(MAIN_TEMPLATE)

@app.route("/lights_on/", methods=DEFAULT_METHODS)
def lights_on():
    subprocess.Popen(COMMAND_LIGHTS_ON, stdin=None, stdout=None, stderr=None, close_fds=True)
    return render_template(MAIN_TEMPLATE, action_message=ACTION_MSG_LIGHTS_ON);

@app.route("/lights_off/", methods=DEFAULT_METHODS)
def lights_off():
    subprocess.Popen(COMMAND_LIGHTS_OFF, stdin=None, stdout=None, stderr=None, close_fds=True)
    return render_template(MAIN_TEMPLATE, action_message=ACTION_MSG_LIGHTS_OFF);

@app.route("/door/", methods=DEFAULT_METHODS)
def door():
    return render_template(MAIN_TEMPLATE, action_message=ACTION_MSG_DOOR);

if __name__ == '__main__':
   app.run(host="0.0.0.0", port=IP_PORT, debug = True)
