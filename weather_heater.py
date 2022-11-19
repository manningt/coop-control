#!/usr/bin/env python3
""" fetches the current temperature and turns the heater on or off
"""

from time import sleep
import requests
# from datetime import datetime
import subprocess
import sys
import logging
import os
from enum import Enum


logging.basicConfig(
    # filename='HISTORYlistener.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
Logger = logging.getLogger(__name__)

# The following didn't work - not sure why the params weren't getting sent or were not formatted:
    # LATITUDE=42.771
    # LONGITUDE=-70.948
    # weather_params ={'lat': LATITUDE, 'lon': LONGITUDE, 'units': 'imperial', 'apiid': API_ID}
    # response = requests.get(url=base_url, params=weather_params)


def get_conditions(zip_code, api_id):
    current_temperature = None

    base_url = "https://api.openweathermap.org/data/2.5/weather" 
    query_url = f"{base_url}?appid={api_id}&zip={zip_code}&units=imperial"

    for i in range(4):
        try:
            response = requests.get(query_url)
        except requests.exceptions.Timeout:
            if i > 3:
                Logger.warning("Weather request had {} timeouts.".format(i + 1))
            sleep(4)
        except requests.exceptions.RequestException as e:
            Logger.error("  error on request to weather service: {}".format(e))
            break
        if response:
            break

    if not response:
        Logger.warning("Weather request failed after {} retries".format(i + 1))
    else:
        try:
            weather_dict = response.json()
            # Logger.info(f"response: {weather_dict}")
            # Logger.info(f"parse: {weather_dict['main']['temp']}")
            current_temperature= int(weather_dict['main']['temp'])
        except:
            Logger.error(f" json error in response: {response}")

    return current_temperature


def switch(state):
    HEATER_EXECUTABLE = "./heat.py"
    result = subprocess.run([HEATER_EXECUTABLE, str(state)], capture_output=True)
    if result.returncode > 0:
        err_string = "error code: {} when calling '{}' - {}".\
            format(result.returncode, HEATER_EXECUTABLE, result.stdout)
        Logger.error(err_string)


if __name__ == '__main__':
    MY_ZIP= "01922,us"

    os.chdir('/home/pi/coop')
    with open("openweather_api_key.txt") as f:
        content = f.read().splitlines()

    current_temperature = get_conditions(zip_code=MY_ZIP, api_id=content[0])
    if current_temperature is None:
        Logger.error(" get_conditions failed")
        sys.exit(1)

    Logger.info(f"current_temperature: {current_temperature}")

    class Threshold(Enum):
        LO = 0
        HI = 1
    TEMPERATURES = [29, 32]
    # TEMPERATURES = [50, 60]

    if (current_temperature <= TEMPERATURES[Threshold.LO.value]):
        switch(1)
    if (current_temperature >= TEMPERATURES[Threshold.HI.value]):
        switch(0)
