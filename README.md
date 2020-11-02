The chicken coop has 3 control relays:
* heater: a water heater to keep the waterer from freezing and a radiant heat panel to warm the chickens
* light: optionally used to extend daylight during the winter or to inspect the birds at night
* door: a sliding door separates the run (an 8x8 area) and the chicken pen (a large 'free-range') area.
The chickens squawk every morning to get let out.

There are 3 software services that control the relays:
* python scripts that turn on/off the relays; these can be called directly via ssh or used by 
the following 2 services (alexa, cron)
* alexa-ctrl: responds to a custom Alexa skill commands sent to the Raspberry Pi via ngrok. 
Launched as a service on reboot.
* A python script (weather_api) which is invoked by cron to turn the heaters and 
light on based on the temperature forecast and sunrise

Python scripts
--
light.py is written to be invoked from the shell. 
It takes 0 or 1 as an argument to turn the relay on or off. 
light.py uses a function in gpio_control.py to do the real work of controlling the hardware. 
All hardware access is in gpio_control so if the API changes, only that module has to change.

The light script will report _success_ if the state is switched, or it will return _already on/off_ if the light is
in that state which can be used to confirm the current state.

In order to minimize code/maintenance, light.py is also used to control the heater relay using
a symbolic link (`ln -s light.py heat.py`);
light.py looks at argv[0] to determine if its been called with heat or light.

Controlling the door motor requires turning on the relay for around 15 seconds, and then turning the relay off.
The script `timed-gpio-activiation.py` when run without any arguments is used to operate the door. 
The Alexa service expects a response from the device (RPi in this case) within 10 seconds.
Therefore this script is run without waiting for it to complete before returning the response to Alexa.

An issue with the door is the current state (open/closed) is not known by the hardware.  The script just runs the
motor which will reverse the state.  Ideally you'd be able to say door open or close so that you would know what
the state is, since it's highly desirable not to leave the door open at night.

The `timed-gpio-activiation.py` script can also be used to turn on the lights momentarily (5 minutes) thereby
eliminating the need to turn them off, which can sometimes be forgotten.
And it can be used to turn on the heaters for a period, when called from the cron job.

Alexa files
--
Amazon's Alexa service sends json to the Raspberry Pi when a custom skill is invoked.
The full set of things/services needed for a custom skill are:
* A skill which is created on https://developer.amazon.com/alexa/
    * alexa-custom-skill.json can be pasted into your skill
    * the skill I created is invoked by saying "tell hen house lights on"
    * this phrase works with the Alexa App _and_ an Echo Dot _if you hold down the Action_ button.
* A web service (I used [ngrok](dashboard.ngrok.com/status/tunnels)) to get the json to the RPi which is behind a router.
In order to use the free ngrok, the endpoint address has to be reconfigured on ALexa developer webpage every
time the RPi reboots. 
* A python script (alexa-ctrl.py) which uses flask-ask to recieve the json from alexa/amazon

Here is a [tutorial](https://www.instructables.com/Control-Raspberry-Pi-GPIO-With-Amazon-Echo-and-Pyt/) that I used as a model.

Weather based control
--
There are 2 python scripts to control the heaters based on forecast temperatures.
Both of these scripts are invoked by cron.
* weather_api.py gets a weather forecast using the [OpenWeatherMap](https://rapidapi.com/blog/weather-api-python/)
service available at rapidapi.com
    * A rapidapi-key should be pasted into 'YourKeyHere' to run this script
    * The free-level service for this API is 500 a month.
    * The code is written assuming getting 8 3-hour forecasts once a day and write the forecast to a in-memory file, 
    but it could be done any number of ways.
    
* heater-control.py: 
    * is written to run every 3-hours (matches the forecast duration)
    * reads the forecast data from the in-memory file and 


Use `crontab -e` to add the following lines; refer to this [tutorial](https://ostechnix.com/a-beginners-guide-to-cron-jobs/):
```
# run weather_api once a day at 2 minutes before midnight for Oct through April
58 23 * 10,11,12,1,2,3,4 * /home/pi/coop/weather_api.py >> /home/pi/coop/cron.log 2>&1
#
# run heater-control 8 times a day at 3 hour intervals 
1 0,3,6,9,12,15,18,21 * 10,11,12,1,2,3,4 * /home/pi/coop/heater-control.py >> /home/pi/coop/cron.log 2>&1
```
According to this website: _Hens need at least 12 hours of daylight per day to lay eggs, whereas 14 to 16 hours
of sunlight per day will keep them performing at their full potential._

To have extended daylight in March & April then add the following lines to cron:
Note that cron is specified in GMT, which means that it doesn't need to changed
when daylight savings takes effect in mid March.
```
# turn on the light at 4:45AM (9:45 GMT)
45 8 * 3,4 * /home/pi/coop/light.py 1 >> /home/pi/coop/cron.log 2>&1
# turn the light off at 7AM  (7AM is noon GMT
0 12 * 3,4 * /home/pi/coop/light.py >> /home/pi/coop/cron.log 2>&1
#

```
