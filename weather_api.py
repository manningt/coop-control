#!/usr/bin/env python3
"""
program should be run before LIGHT_TURN_ON_HOUR (5AM)
the program gets the sunrise time and 8 forecasted temperarure over the next 24 hours
if temperature is below a threshold at least twice, then turn on heat; else turn off heat
if the month is in LIGHT_ON_MONTHS then turn on light at 5, sleep for until sunrise+30 and turn off
  - turning the light on in the morning is intended to lengthen the day
"""

from time import sleep
import requests
from datetime import datetime
import subprocess
import logging

logging.basicConfig(
    # filename='HISTORYlistener.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
Logger = logging.getLogger(__name__)

THRESHOLD = 1  # temperature threshold (in Celsius) where if the temp is going to be below, the heaters will turn on
# THRESHOLD = 21 # used for testing
THRESHOLDCOUNT = 2
LIGHT_ON_MONTHS = [3, 4]
LIGHT_TURN_ON_HOUR = 5
LIGHT_TURN_ON_MINUTE = 0
FORECAST_SAMPLES = 24 / 3  # every 3 hours in 24 hours

headers = {
    'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
    'x-rapidapi-key': "YourKeyHere"
}

def switch(thing, state):
    cmd = "/home/pi/coop/{}.py {}".format(thing, state)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    rc = p.returncode
    if err is not None:
        Logger.error("error code: {} occurred on calling: {}".format(err, cmd))
    if rc > 0:
        Logger.warning("script {} returned an non-zero return code: {}".format(cmd, rc))


def get_conditions():
    temperature_array = []
    minutes_sunrise = 0
    minutes_sunset = 0
    response = None
    for i in range(5):
        try:
            response = requests.get("https://community-open-weather-map.p.rapidapi.com/forecast", \
                                    headers=headers, params={"units": "metric", "q": "Newburyport,us"})
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
        except:
            Logger.error("  error in response from weather service: json error")

        if 'city' not in weather_dict:
            Logger.error("  error in response from weather service: city not present")
        else:
            ts_sunrise = weather_dict['city']['sunrise'] + weather_dict['city']['timezone']
            ts_sunset = weather_dict['city']['sunset'] + weather_dict['city']['timezone']
            minutes_sunrise = (int(datetime.utcfromtimestamp(ts_sunrise).strftime('%H'))) * 60 + \
                              int(datetime.utcfromtimestamp(ts_sunrise).strftime('%M'))
            minutes_sunset = (int(datetime.utcfromtimestamp(ts_sunset).strftime('%H'))) * 60 + \
                             int(datetime.utcfromtimestamp(ts_sunset).strftime('%M'))
            Logger.debug("Sunrise: {}  -- Sunset: {}".format(minutes_sunrise, minutes_sunset))

            for c, value in enumerate(weather_dict['list']):
                # the weather_dict has a list of emperatures at 3 hour intervals, so 8 intervals looks ahead 24 hours
                # Logger.debug("Temp: {} at {}".format(value['main']['temp'], value['dt_txt']))
                temperature_array.append(int(str(value['main']['temp']).split(".")[0]))
                if (c >= (FORECAST_SAMPLES - 1)):
                    break

    return temperature_array, minutes_sunrise, minutes_sunset


if __name__ == '__main__':
    HEATERS_NAME = "heat"
    LIGHTS_NAME = "light"
    below_thold_count = 0
    conditions = get_conditions()
    if len(conditions[0]) < FORECAST_SAMPLES - 1:
        Logger.error(" get_conditions failed - list of temperatures is short")
    else:
        # turn heat on/off based on temperature threshold; the heat will stay on/off until the next time the script runs
        for value in conditions[0]:
            if value < THRESHOLD:
                below_thold_count += 1
        if below_thold_count >= THRESHOLDCOUNT:
            compared_to_threshold = "below"
            message_re_heat_control = "Turning on heat"
            switch(HEATERS_NAME, 1)
        else:
            compared_to_threshold = "above"
            message_re_heat_control = "Turning off heat"
            switch(HEATERS_NAME, 0)
        message_re_temperature = "Temperature will be {} {} celsius: {}".format(compared_to_threshold, THRESHOLD,
                                                                                str(conditions[0])[1:-1])

        # Logger.info("Temperature will be {} {} celsius: {}".format(compared_to_threshold, THRESHOLD, str(conditions[0])[1:-1]))
        # Logger.info("Sunrise: {}  -- Sunset: {}".format(conditions[1], conditions[2]))

        # turn on light based on month
        lightOnSeconds = 0
        currentMonth = datetime.now().month
        if (currentMonth in LIGHT_ON_MONTHS):
            now = datetime.now()
            lightTurnOnTime = now.replace(hour=LIGHT_TURN_ON_HOUR, minute=LIGHT_TURN_ON_MINUTE, second=0, microsecond=0)
            secondsUntilTurnOn = (lightTurnOnTime - now).seconds
            if secondsUntilTurnOn < 0:
                secondsUntilTurnOn = 0
            # sunrise is conditions[1] and is in minutes past midnight
            lightOnSeconds = (conditions[1] * 60) - secondsUntilTurnOn

        if lightOnSeconds > 0:
            sleep(secondsUntilTurnOn)
            message_re_light_control = "Turning light on for {} minutes".format(int(lightOnSeconds / 60))
            switch(LIGHTS_NAME, 1)
        else:
            message_re_light_control = "Not operating lights"

        Logger.info("{}; Sunrise: {}; {}; {}".format(message_re_light_control, conditions[1], \
                                                     message_re_heat_control, message_re_temperature))
        if lightOnSeconds > 0:
            sleep(lightOnSeconds)
            switch(LIGHTS_NAME, 0)
