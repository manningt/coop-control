#!/usr/bin/env python3
""" writes a file with the temperature forecast
2020-10-26 05:55:10.659226
sunrise,430
temperatures,5,6,7,11,11,11,11,11,12,13
"""

from time import sleep
import requests
from datetime import datetime
import subprocess
import sys
import logging

logging.basicConfig(
    # filename='HISTORYlistener.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
Logger = logging.getLogger(__name__)

# Each temperature forecast is for a 3 hour interval
FORECAST_SAMPLES = 10

TEMPERATURE_FILENAME = '/dev/shm/todays-temperatures.txt'
SUNRISE_NAME = 'sunrise'
TEMPERATURES_NAME = 'temperatures'

headers = {
    'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
    'x-rapidapi-key': "YourKeyHere"
}


def get_conditions():
    temperature_array = []
    dt_txt_array = []
    minutes_sunrise = 0
    minutes_sunset = 0
    response = None
    for i in range(5):
        try:
            response = requests.get("https://community-open-weather-map.p.rapidapi.com/forecast", \
                                    headers=headers, params={"units": "metric", "zip": "01922,us"})
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
                # get integer temperature in celsius; strip off the fraction
                temperature_array.append(int(str(value['main']['temp']).split(".")[0]))
                dt_txt_array.append(value['dt_txt'])
                if (c >= (FORECAST_SAMPLES - 1)):
                    break
            Logger.debug("forecast timestamps: {}".format(dt_txt_array))

    return temperature_array, minutes_sunrise, minutes_sunset


if __name__ == '__main__':
    conditions = get_conditions()
    if len(conditions[0]) < FORECAST_SAMPLES - 1:
        Logger.error(" get_conditions failed - list of temperatures is short")
        sys.exit(1)

    now_datetime = datetime.now()
    try:
        f = open(TEMPERATURE_FILENAME, "w")
        f.write("{}\n".format(now_datetime))
        f.write("{},{}\n".format(SUNRISE_NAME, conditions[1]))
        temperatures_str = "{},{}\n".format(TEMPERATURES_NAME, str(conditions[0])[1:-1]).replace(" ", "")
        f.write(temperatures_str)
        f.close()
    except IOError:
        Logger.error("Could not open file for writing: {}".format(TEMPERATURE_FILENAME))
