def gpio_switch(pin, new_state):
    try:
        import RPi.GPIO as GPIO
    except:
        return "error: missing RPi GPIO"

    if new_state not in [0,1]:
        return "error: called with invalid pin state: {}".format(new_state)

    if pin not in [23, 24, 25]:
        return "error: called with invalid pin number: {}".format(pin)

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
    except:
        return "error: gpio setup failed"

    if new_state == GPIO.input(pin):
        return "already {}".format(new_state)
    else:
        GPIO.output(pin, new_state)
        return "success"
