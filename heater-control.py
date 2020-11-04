#!/usr/bin/env python3
""" reads a file with the temperature forecast in the following format:
2020-10-26 05:55:10.659226
sunrise,430
temperatures,5,6,7,11,11,11,11,11

The temperature array are for 3-hour periods
If below a temperature threshold for the current or next period, then activate a relay that turns on the heaters.
Which forecast temperature to use is calculated by subtracting the date-time stamp of the file against the now datetime.

The relay switching gets run only on linux (RaspberryPi), so this can be run on macos

Note: if using a shared memory file in /dev/shm, you'll need to do the following:
Edit /etc/systemd/logind.conf, uncomment the line RemoveIPC=yes, change it to RemoveIPC=no, save, and reboot the system
refer to: https://superuser.com/questions/1117764/why-are-the-contents-of-dev-shm-is-being-removed-automatically#1179962
"""

from datetime import datetime
import sys
import subprocess
import logging
from platform import system as os_name
import os

logging.basicConfig(
    level=logging.INFO,
    # level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
Logger = logging.getLogger(__name__)

TEMPERATURE_FILENAME = '/dev/shm/todays-temperatures.txt'
if os_name() == 'Darwin':
    TEMPERATURE_FILENAME = '/tmp/todays-temperatures.txt'
SUNRISE_NAME = 'sunrise'
TEMPERATURES_NAME = 'temperatures'
TEMPERATURES_LIST_LENGTH = 9
TEMPERATURE_THRESHOLD = 1  # celsius

USE_SUNRISE = False
FORECAST_DURATION_SECONDS = 3 * 60 * 60  # 3 hours in seconds
# add the following to deal with some variability in cron job actual runtimes
FUDGE_SECONDS = 5 * 60
# file datetime can be 24 hours ago, but may have fetched early plus add fudge
MAX_DATETIME_DELTA = (24 * 60 * 60) + FUDGE_SECONDS

os.chdir('/home/pi/coop')
HEATER_EXECUTABLE = "./heat.py"

now_datetime = datetime.now()

def switch(state):
    if os_name() == 'Linux':
        result = subprocess.run([HEATER_EXECUTABLE, str(state)], capture_output=True)
        if result.returncode > 0:
            err_string = "error code: {} when calling '{}' - {}".\
                format(result.returncode, HEATER_EXECUTABLE, result.stdout)
            Logger.error(err_string)


def file_error_exit():
    if datetime.month in [11, 12, 1, 2, 3]:
        Logger.warning("Turning on heat because a problem with the weather forecast file")
        result = subprocess.run([HEATER_EXECUTABLE, 1])
    sys.exit(1)


if __name__ == '__main__':
    try:
        f = open(TEMPERATURE_FILENAME, "r")
    except IOError:
        Logger.error("Could not open file: {}".format(TEMPERATURE_FILENAME))
        file_error_exit()

    try:
        file_datetime = datetime.strptime(f.readline().replace("\n", ""), '%Y-%m-%d %H:%M:%S.%f')
    except:
        Logger.error("Could not read 1st line in file: {}".format(TEMPERATURE_FILENAME))
        file_error_exit()

    time_delta = now_datetime - file_datetime
    Logger.debug("time_now: {};  time_in_file: {};  time_now minus time_in_file: {}".format(now_datetime, file_datetime,
                                                                                            time_delta))

    if time_delta.total_seconds() > MAX_DATETIME_DELTA:
        Logger.error(
            "file '{}' has datestamp '{}' which is more than 24 hours ago".format(TEMPERATURE_FILENAME, file_datetime))
        file_error_exit()

    try:
        sunrise_line = f.readline().replace("\n", "").split(",")
    except:
        Logger.error("Could not read 2nd line (sunrise) in file: {}".format(TEMPERATURE_FILENAME))
        file_error_exit()
    if USE_SUNRISE:
        if sunrise_line.pop(0) != SUNRISE_NAME:
            Logger.error("file '{}' missing time of {} on 2nd line".format(TEMPERATURE_FILENAME, SUNRISE_NAME))
        sunrise = int(sunrise_line[0])
        Logger.debug("{}: {:2.2f}".format(SUNRISE_NAME, sunrise / 60))

    try:
        temperatures = f.readline().replace("\n", "").split(",")
    except:
        Logger.error("Could not read 3rd line (temperatures) in file: {}".format(TEMPERATURE_FILENAME))
        file_error_exit()
    if temperatures.pop(0) != TEMPERATURES_NAME:
        Logger.error("file '{}' missing temperature forecasts on 3rd line".format(TEMPERATURE_FILENAME))
        file_error_exit()

    f.close()
    temp_list_len = len(temperatures)
    if temp_list_len < TEMPERATURES_LIST_LENGTH:
        Logger.error("file '{}' only has {} temperature forecasts".format(TEMPERATURE_FILENAME, temp_list_len))
        file_error_exit()
    # convert strings to integers in list:
    temperatures = [int(i) for i in temperatures]

    # calculate the index of the temperature forecast; there are 8 3-hour forecasts
    mid_interval_of_now_minus_midnight_seconds = time_delta.seconds + (FORECAST_DURATION_SECONDS >> 1)
    temperature_forecast_index = int(mid_interval_of_now_minus_midnight_seconds / FORECAST_DURATION_SECONDS)

    if temperature_forecast_index == 0:
        Logger.info("time_in_file: {};  forecast: {}".format(file_datetime, temperatures))

    if (temperatures[temperature_forecast_index] <= TEMPERATURE_THRESHOLD ) or \
        (temperatures[temperature_forecast_index+1] <= TEMPERATURE_THRESHOLD):
        message_re_heat_control = "Turning on heaters"
        switch(1)
    else:
        message_re_heat_control = "Turning off heaters"
        switch(0)

    message_re_temperature = "Forecast temperatures: {} & {}C -> {}  (index: {})". \
        format(temperatures[temperature_forecast_index], temperatures[temperature_forecast_index+1], \
               message_re_heat_control, temperature_forecast_index)
    Logger.info(message_re_temperature)
