#!/usr/bin/env python3
"""
program runs at midnight
turn off heat & light
if temp below threshold, then turn on heat
if month = 11,12 3,4 then turn on light at 5, sleep for until sunrise+30 and turn off

"""

from time import sleep
import requests
from datetime import datetime

import logging
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)
Logger = logging.getLogger(__name__)
# Logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('/home/pi/coop/coop_ctrl_conditions_test.log')
formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)
Logger.addHandler(file_handler)

THRESHOLD = 1 # temperature threshold (in Celsius) where if the temp is going to be below, the heaters will turn on
THRESHOLD = 21
THRESHOLDCOUNT = 2

headers = {
    'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
    'x-rapidapi-key': "955e325a50msh43e8a03a92ee695p1954f3jsn1327e8efa375"
}

def get_conditions(threshold=THRESHOLD):
    below_thold_count = -1
    minutes_sunrise = 0
    minutes_sunset = 0
    response = None
    for i in range(5):
        try:
            response=requests.get("https://community-open-weather-map.p.rapidapi.com/forecast", \
                                  headers=headers, params={"units": "metric", "q": "Newburyport,us"})
        except requests.exceptions.Timeout:
            if i > 3:
                Logger.warning("Weather request had {} timeouts.".format(i+1))
            sleep(4)
        except requests.exceptions.RequestException as e:
            Logger.error("  error on request to weather service: {}".format(e))
            break
            # raise SystemExit(e)
        if response:
            break

    if not response:
        Logger.warning("Weather request failed after {} retries".format(i+1))
    else:
        weather_dict = response.json()
        if 'city' in weather_dict:
            ts_sunrise = weather_dict['city']['sunrise'] + weather_dict['city']['timezone']
            ts_sunset = weather_dict['city']['sunset'] + weather_dict['city']['timezone']
            minutes_sunrise = (int(datetime.utcfromtimestamp(ts_sunrise).strftime('%H'))) * 60 + \
                           int(datetime.utcfromtimestamp(ts_sunrise).strftime('%M'))
            minutes_sunset = (int(datetime.utcfromtimestamp(ts_sunset).strftime('%H'))) * 60 + \
                           int(datetime.utcfromtimestamp(ts_sunset).strftime('%M'))
            Logger.debug("Sunrise: {}  -- Sunset: {}".format(minutes_sunrise, minutes_sunset))

            for c, value in enumerate(weather_dict['list']):
                # the weather_dict has a list of temperatures at 3 hour intervals, so 8 intervals looks ahead 24 hours
                Logger.debug("Temp: {} at {}".format(value['main']['temp'], value['dt_txt']))
                if int(value['main']['temp']) < THRESHOLD:
                    below_thold_count += 1
                if (c >= 7):
                    break

    return below_thold_count, minutes_sunrise, minutes_sunset


if __name__ == '__main__':
    conditions = get_conditions()
    if conditions[0] < 0:
        Logger.info(" get_coditions failed")
    elif conditions[0] >= THRESHOLDCOUNT:
        Logger.info("Temperature will be below threshold")
    else:
        Logger.info("Temperature will be above threshold")
    # Logger.info("Sunrise: {}  -- Sunset: {}".format(conditions[1], conditions[2]))
