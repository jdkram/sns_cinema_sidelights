"""
check_buttons.py -- quick manual verification of button wiring

Run on the Pi with:
    python3 check_buttons.py

What it does:
  Configures GPIO 4, 17, 18, 22, 27 as inputs with internal pull-down
  resistors, then busy-polls all five pins and prints the button number
  (1-5) to stdout whenever a pin reads HIGH.

What to look for:
  - Each physical button should print its own number when held and nothing
    when released.
  - If a button never prints: the pin may be wired wrong, or the pull-down
    resistor / signal wire may be missing.
  - If a button always prints: the pin is floating HIGH or wired directly
    to 3.3V with no switch in the circuit.

Limitations:
  - No debouncing: holding a button floods stdout (expected).
  - CPU spins continuously - exit with Ctrl+C when done.
  - No state machine: use test_runner.py for structured pass/fail testing.
"""

import RPi.GPIO as GPIO

# Reset any previous GPIO state left by earlier scripts/runs.
GPIO.cleanup()

# Use Broadcom SoC pin numbering (GPIOxx), not physical header pin numbers.
GPIO.setmode(GPIO.BCM)

# Reference mapping:
#   GPIO 4  -> physical pin 7
#   GPIO 17 -> physical pin 11
#   GPIO 18 -> physical pin 12
#   GPIO 27 -> physical pin 13
#   GPIO 22 -> physical pin 15
#
# NOTE: comment values in brackets above are physical pin numbers.

# Logical button labels mapped to BCM GPIO inputs.
# The numbers printed in the loop correspond to BUTTON_1..BUTTON_5.
BUTTON_4 = 4
BUTTON_5 = 17
BUTTON_3 = 18
BUTTON_2 = 27
BUTTON_1 = 22

# Configure each button pin as input with an internal pull-down resistor.
# With this setup, pin reads LOW (0) when idle and HIGH (1) when pressed
# assuming the button wiring drives 3.3V on press.
GPIO.setup(BUTTON_1, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_2, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_3, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_4, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BUTTON_5, GPIO.IN, GPIO.PUD_DOWN)

# Busy-poll loop: continually reads each input and prints the button index
# whenever a button is currently HIGH.
#
# This is intentionally simple for quick manual validation, but it does not:
#   - debounce mechanical button chatter
#   - throttle output rate while a button is held
#   - sleep between iterations (CPU spins continuously)
while True:
    if GPIO.input(BUTTON_1):
        print(1)
    if GPIO.input(BUTTON_2):
        print(2)
    if GPIO.input(BUTTON_3):
        print(3)
    if GPIO.input(BUTTON_4):
        print(4)
    if GPIO.input(BUTTON_5):
        print(5)
