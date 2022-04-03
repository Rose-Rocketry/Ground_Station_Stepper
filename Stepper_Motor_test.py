from time import sleep
import RPi.GPIO as GPIO


def setup_yagi():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(STEP, GPIO.OUT)
    GPIO.output(DIR, CW)

def rotate_yagi():
"""
Rotate the yagi one rotation and then roate it back
"""
    for x in range(step_count):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

    sleep(.5)
    GPIO.output(DIR, CCW)
    for x in range(step_count):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

def on_end(inturrupted):
"""
Call this when the api is done with us or when we lose connection or in some other way are inturrepted
"""
    GPIO.cleanup()
    

if __name__ == "__main__":
"""
Main program here
"""

    DIR = 17
    STEP = 27
    CW =1
    CCW =0
    SPR = 200 #steps per revolution (360/1.8)
    
    
    delay = .108
    step_count = SPR
    setup_yagi()

    rotate_yagi()

    on_end()

