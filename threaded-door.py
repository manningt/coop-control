#!/usr/bin/env python3

import threading
import logging
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)

def operate_door(delay):
    logging.debug("operate_door thread started")
    from time import sleep
    import RPi.GPIO as GPIO

    pin = 23
#    pin = 25 #AC relay pin for testing

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT, initial=0)
        logging.debug("Initializing relay to 0 for 4 seconds.")
        sleep(4)

        GPIO.output(pin, 1)
        logging.info("operate_door thread: Setting relay to 1 for {} seconds.".format(delay))
        sleep(delay)

        GPIO.output(pin, 0)
        logging.debug("Final: turning off relay.")
    except Exception as e:
        logger.exception(e)
        logging.error("Exception in door relay control thread: {}".format(str(e)))

if __name__ == "__main__":
    x = threading.Thread(target=operate_door, args=(9, ))
    x.start()
    logging.debug("Main    : wait for the thread to finish")
    x.join()
