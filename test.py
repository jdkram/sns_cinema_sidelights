import os
import RPi.GPIO as GPIO

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

# GPIO 4(7)
# GPIO 17(11)
# GPIO 18(12)
# GPIO 27(13)
# GPIO 22(15)

BUTTON_4 = 4 # 8
BUTTON_5 = 17 # 8
BUTTON_3 = 18 # 8
BUTTON_2 = 27 # 8
BUTTON_1 = 22 # 8

GPIO.setup(BUTTON_1, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_2, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_3, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_4, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_5, GPIO.IN, GPIO.PUD_DOWN)

while 1:
    if GPIO.input(BUTTON_1):
        print 1;
    if GPIO.input(BUTTON_2):
        print 2;
    if GPIO.input(BUTTON_3):
        print 3;
    if GPIO.input(BUTTON_4):
        print 4;
    if GPIO.input(BUTTON_5):
        print 5;
