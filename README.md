Overview
--
My chicken coop has 3 control relays:
* heater: a water heater to keep the waterer from freezing and a radiant heat panel to warm the chickens
* light: LED strips which can bet turned on to inspect the birds at night or optionally be used to extend daylight
 during the winter.
* door: a motorized sliding door which separates the run (an 8x8 area) and the chicken pen (a large 'free-range') area.
The chickens squawk every morning to get let out.

There are 4 interfaces to control the relays:
* manual control: a python script whcih turns on/off the relays; this can be called directly via ssh or used by 
the following 3 services (alexa, cron, web)
* alexa-ctrl: responds to a custom Alexa skill commands sent to the Raspberry Pi via ngrok. 
Launched as a service on reboot.
* weather-based: 2 python scripts which are invoked by cron to:
    * weather_api.py: & ) get the weather forecast for the next 24 hours and store it in an in-memory file
    * heater-control.py: turn the heaters based on the temperature forecast in the above mentioned file
* web-based: a webpage is served which has a few buttons to activate the relays so that one doesn't
have to login to the RPi or shout at Alexa.  This webpage is only available on the local WiFi network; one has to
use Alexa if controlling the coop devices remotely.  For some unknown reason, it takes 10 or more seconds
for this webpage to come up, even though it shouldn't be doing a DNS query.

Python scripts
--
light.py is written to be invoked from the shell:
* 0 or 1 as an argument will turn the relay on or off
* 2-7 as an argument will activate the relay for that many minutes. 
This eliminates the need to turn the device off.
* It reads a json file which associates gpio pins with names
* it optionally takes a gpio_pin argument to control a different gpio pin than the configured ones

light.py uses a function in gpio_control.py to do the real work of controlling the hardware. 
All hardware access is in gpio_control so if the GPIO API changes, only that module has to change.

The light script will report _success_ if the state is switched, or it will return _already on/off_ if the light is
in that state which can be used to confirm the current state.

In order to minimize code/maintenance, light.py is also used to control the heater and door relays using
a symbolic link (`ln -s light.py heat.py; ln -s light.py door.py`);
light.py looks at argv[0] to determine if its been called with heat, light or door.

Controlling the door motor requires turning on the relay for around 15 seconds, and then turning the relay off.
The json gpio_pin to name config file also supports specifying the duration the relay should be on.
 
The Alexa service expects a response from the device (RPi in this case) within 10 seconds.
Therefore if the script invoked by Alexa will execute sleep delays,
the script is run without waiting for it to complete before returning the response to Alexa.

An issue with the door is the current state (open/closed) is not known by the hardware.  The script just runs the
motor which will reverse the state.  Ideally you'd be able to say door open or close so that you would know what
the state is, since it's highly desirable not to leave the door open at night.

Alexa files
--
Amazon's Alexa service sends json to the Raspberry Pi when a custom skill is invoked.
Here is a [tutorial](https://www.instructables.com/Control-Raspberry-Pi-GPIO-With-Amazon-Echo-and-Pyt/) that I used as a model.

The full set of things/services needed for a custom skill are:
* A skill which is created on https://developer.amazon.com/alexa/
    * alexa-custom-skill.json can be pasted into your skill
    * the skill I created is invoked by saying "tell hen house lights on"
    * this phrase works with the Alexa App _and_ an Echo Dot _if you hold down the Action_ button.
* A web service (I used [ngrok](ngrok.com/doc)) to get the json to the RPi which is behind a router.
In order to use the free ngrok, the endpoint address has to be reconfigured on Alexa developer webpage every
time the RPi reboots.
    * The [dashboard.ngrok](https://dashboard.ngrok.com/status/tunnels) lists the endpoint
    address to plug into the alexa skill webpage
    * ```curl http://127.0.0.1:4040/api/tunnels``` on the RPi can also be used to get the tunnel ID
* A python script (alexa-ctrl.py) which uses flask-ask to recieve the json from alexa/amazon
    * to enable alexa-ctrl.py to run when the computer boots, it needs to be run as a service.
    Here are the [instructions](https://www.wikihow.com/Execute-a-Script-at-Startup-on-the-Raspberry-Pi) I followed.
    * ```sudo cp alexa-ctrl.service to /etc/systemd/system```
    * Use the following to control the service:
```
sudo systemctl start alexa-ctrl.service
sudo systemctl status alexa-ctrl.service
sudo systemctl stop alexa-ctrl.service
```

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
```
Web control
--
The python flask module was used to create a webserver tha runs on the RPi.

There are 3 items needed to enable the web server:
* web-ctrl.py is the server which has 3 POSTs (lights on, lights off, door)
* web-ctrl.service needs run as a service:
    * ```sudo cp web-ctrl.service to /etc/systemd/system```
    * ```sudo systemctl start alexa-ctrl.service```
* index.html is copied to the templates directory

The web-ctrl server uses port 44, but this can be changed.

To access on my network, I set the URL to http://10.0.1.100:44

Note this web page does not show whether the lights are on or off.  This would
require reading the state of the RPi GPIO pins, which requires knowing whether a GPIO 
is set to be an output or an input.  My understanding is the RPI.GPIO module does not support reading the Input/Output
configuration of a pin, so I didn't add this feature.  Since the web control
is only available on the local network, one can observe the state of the door
and lights.

I also didn't add heater control, figuring it was controlled by a cron job.

Hardware Description
--
* Raspberry Pi - I'm using a $10 Zero with no monitor/keyboard
* 12V supply for powering the door motor and LED strips
* [dual relay](https://smile.amazon.com/gp/product/B07PLRSSCV) for switching the 12V to the motor and LED strip
* [solid state relay](https://smile.amazon.com/gp/product/B01LYKLD1A) for turning on the heaters
* [12V door motor](https://smile.amazon.com/gp/product/B007IZJWNQ)
* [Radiant Heat Panel](https://smile.amazon.com/gp/product/B07PFYM4QG) for the coop (120V)
* A heated nipple chicken waterer following [this example](https://www.backyardchickens.com/articles/summer-winter-chicken-nipple-waterer.64236/).
    * I used a smaller oooler and a shorter run of pipe
    * These [nipples](https://smile.amazon.com/gp/product/B01NBZH4XV) figuring that horizontal ones were less likely to freeze
    * The main reason to go to this effort is to not have to clean out a waterer
    in the dead of winter.
    * That said, I will get the data on how reliable it works this year.
    * I have the old heated waterer as a backup.