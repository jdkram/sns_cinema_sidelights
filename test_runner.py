#!/usr/bin/env python3
# author: Jonny Kram; ai-model: Claude Sonnet; status: "#ai-input"
"""
test_runner.py -- GPIO button hardware diagnostic and stress test

WHAT IT DOES
============
Comprehensive hardware test suite for the 5-button control panel. Verifies GPIO
wiring, debouncing quality, and mechanical reliability. Produces a CSV event log
and human-readable pass/fail results for each test.

Designed to catch wiring faults, stuck buttons, and noisy inputs before the
device goes into production or when troubleshooting field failures.

PREREQUISITES
=============
- Raspberry Pi with RPi.GPIO installed: sudo apt install python3-rpi.gpio
- All five buttons physically connected and powered
- User permission to access GPIO (usually pi user on Raspberry Pi OS)

TEST MODES
==========
Five tests are available, run individually or all together (default):

1. SMOKE TEST (--mode smoke)
   Duration: ~15 seconds (customizable with --smoke-seconds)
   Tests: "Do the buttons work at all?"
   - Listens for any button press/release transitions
   - Does not care which button is pressed when or which GPIO pin
   - Passes if at least one button produces a state change
   - Quick validation that hardware is not completely broken

2. MAPPING TEST (--mode mapping)
   Duration: ~1 minute (depends on --step-timeout)
   Tests: "Is each physical button wired to its correct GPIO?"
   - Prompts for each button 1-5 in sequence
   - Detects which GPIO transitions when you press
   - Fails if a button presses GPIO X when it should press GPIO Y
   - Essential after any rewiring or to validate a new device

3. DEBOUNCE TEST (--mode debounce)
   Duration: ~30 seconds
   Tests: "Does mechanical chatter cause line noise?"
   - One fresh tap per button
   - Counts state transitions during a single press/release cycle
   - Expects 2-4 transitions (press down, settle, release, settle)
   - Warns/fails if >4 transitions (indicates worn contacts or poor solder)

4. HOLD TEST (--mode hold)
   Duration: ~1 minute
   Tests: "Can each button stay held reliably for 2 seconds?"
   - Measures how long each button reads HIGH when you hold it
   - Fails if button cannot sustain 1.5+ seconds (default threshold)
   - Catches intermittent contact and wobbling mechanical connections

5. ALL TESTS (--mode all, default)
   Runs smoke, mapping, debounce, hold in sequence.
   Total time: ~3-5 minutes depending on timeouts and user interaction.

USAGE EXAMPLES
==============
Single-person mode (you operate buttons yourself):
  python3 test_runner.py
  python3 test_runner.py --mode mapping

Two-person mode (operator in booth, caller on stage with a script):
  python3 test_runner.py --two-person
  python3 test_runner.py --mode mapping --two-person

Adjust timing if you're working remotely or over a phone call:
  python3 test_runner.py --two-person --step-timeout 30 --prep-seconds 5

Generate a log with a custom filename:
  python3 test_runner.py --log /tmp/buttons_2026-03-05.csv

OUTPUT
======
Console: pass/fail summary and per-button details for each test.
CSV log file: timestamped events (default: button_test_log_YYYYMMDD_HHMMSS.csv).
             Useful for reviewing exactly when each button registered and with
             how many transitions. Can be opened in a spreadsheet for analysis.

EXIT CODE
=========
0 = All tests passed
1 = At least one test failed or warned
130 = Interrupted by Ctrl+C (cleanup still runs)

TWO-PERSON MODE
===============
Designed for theatre/cinema environments where one person reads a script aloud
(stage/FOH) and another operates the buttons (booth/backstage). Calls are
repeated twice and use military call signs (ONE, TWO, THREE, FOUR, FIVE) to
prevent misunderstanding over phone or intercom.

Timing is intentionally generous (20+ second windows by default) to account for
shout delay, phone latency, and the time needed to run to the booth.

Customize with --prep-seconds (countdown before each call) and --step-timeout
(wait window) if needed.

EXAMPLE FIELD SETUP
===================
Goal: verify the live device's buttons still work after a repair session.

1. SSH into the Pi.
2. Run: python3 /home/pi/sidelights/test_runner.py --mode smoke
   (Quick check: does anything work?)
3. If smoke passes, run: python3 /home/pi/sidelights/test_runner.py --mode mapping
   (Detailed check: is each button correctly wired?)
4. Review results. If buttons work, the device is ready.
5. If buttons fail mapping, check GPIO connections before redeploying.

TROUBLESHOOTING NOTES
=====================
- Command not found / import error: pip3 install RPi.GPIO or apt install python3-rpi.gpio
- Permission denied: Run with sudo, or add user to gpio group (sudo usermod -a -G gpio pi)
- No press detected ever: Check pull-down resistors, power supply, and button solder joints
- Button registers button N when you press button M: Rewiring mismatch; see BUTTON_PINS map
- Excessive transitions (5+): Clean contacts, reflow solder, or replace worn mechanical switch
"""

import argparse
import csv
import sys
import time
from datetime import datetime

import RPi.GPIO as GPIO


BUTTON_PINS = {
    1: 22,
    2: 27,
    3: 18,
    4: 4,
    5: 17,
}

CALL_SIGNS = {
    1: "ONE",
    2: "TWO",
    3: "THREE",
    4: "FOUR",
    5: "FIVE",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def setup_gpio() -> None:
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for pin in BUTTON_PINS.values():
        GPIO.setup(pin, GPIO.IN, GPIO.PUD_DOWN)


def wait_for_enter(prompt: str = "Press Enter to continue...") -> None:
    input(f"\n{prompt}")


def announce_two_person_step(message: str, prep_seconds: float) -> None:
    print("\n" + "-" * 72)
    print("CALL OUT:")
    print(message)
    print("REPEAT:")
    print(message)
    print("-" * 72)
    if prep_seconds > 0:
        print(f"Start in {prep_seconds:.0f} seconds...")
        time.sleep(prep_seconds)


def read_states() -> dict[int, int]:
    return {button: GPIO.input(pin) for button, pin in BUTTON_PINS.items()}


def append_log(log_writer: csv.DictWriter, event_type: str, button: int, details: str) -> None:
    log_writer.writerow(
        {
            "timestamp": now_iso(),
            "event_type": event_type,
            "button": button,
            "details": details,
        }
    )


def test_smoke(log_writer: csv.DictWriter, duration: float) -> bool:
    print_header("SMOKE TEST")
    print("What this checks: buttons produce press/release events at all.")
    print(f"For the next {duration:.0f} seconds, press any buttons a few times.")
    print("You should see lines like: 'Button 3 PRESSED' and 'Button 3 RELEASED'.")

    start = time.monotonic()
    previous = read_states()
    seen_press = {button: False for button in BUTTON_PINS}

    while (time.monotonic() - start) < duration:
        current = read_states()
        for button in BUTTON_PINS:
            if current[button] != previous[button]:
                if current[button] == 1:
                    seen_press[button] = True
                    print(f"[{now_iso()}] Button {button} PRESSED")
                    append_log(log_writer, "pressed", button, "smoke")
                else:
                    print(f"[{now_iso()}] Button {button} RELEASED")
                    append_log(log_writer, "released", button, "smoke")
        previous = current
        time.sleep(0.005)

    pressed_any = any(seen_press.values())
    if pressed_any:
        print("\nResult: PASS (at least one button press detected)")
    else:
        print("\nResult: FAIL (no button press detected)")
    return pressed_any


def detect_single_press(timeout: float) -> int | None:
    deadline = time.monotonic() + timeout
    previous = read_states()
    while time.monotonic() < deadline:
        current = read_states()
        for button in BUTTON_PINS:
            if previous[button] == 0 and current[button] == 1:
                return button
        previous = current
        time.sleep(0.003)
    return None


def wait_for_release(button: int, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    pin = BUTTON_PINS[button]
    while time.monotonic() < deadline:
        if GPIO.input(pin) == 0:
            return True
        time.sleep(0.003)
    return False


def test_mapping(
    log_writer: csv.DictWriter,
    step_timeout: float,
    two_person: bool,
    prep_seconds: float,
) -> bool:
    print_header("MAPPING TEST")
    print("What this checks: each physical button is wired to the expected button number.")
    print("When prompted, press exactly the requested button.")

    all_ok = True
    for expected in range(1, 6):
        if two_person:
            announce_two_person_step(
                (
                    f"STEP {expected} OF 5. PRESS BUTTON {expected} NOW. "
                    f"CALL SIGN {CALL_SIGNS[expected]}."
                ),
                prep_seconds=prep_seconds,
            )
            print(f"Listening for press for up to {step_timeout:.0f} seconds...")
        else:
            print(
                f"\nStep {expected}/5: Press BUTTON {expected} now "
                f"(you have {step_timeout:.0f} seconds)."
            )

        detected = detect_single_press(timeout=step_timeout)
        if detected is None:
            print(f"  FAIL: no press detected for BUTTON {expected}.")
            append_log(log_writer, "mapping_fail", expected, "timeout_no_press")
            all_ok = False
            continue

        append_log(log_writer, "mapping_detected", detected, f"expected_{expected}")
        if detected == expected:
            print(f"  PASS: detected BUTTON {detected} as expected.")
        else:
            print(f"  FAIL: expected BUTTON {expected}, but detected BUTTON {detected}.")
            all_ok = False

        wait_for_release(detected)

    print("\nResult: PASS" if all_ok else "\nResult: FAIL")
    return all_ok


def count_transitions(button: int, window_seconds: float) -> int:
    pin = BUTTON_PINS[button]
    end = time.monotonic() + window_seconds
    transitions = 0
    previous = GPIO.input(pin)
    while time.monotonic() < end:
        current = GPIO.input(pin)
        if current != previous:
            transitions += 1
        previous = current
        time.sleep(0.001)
    return transitions


def test_debounce(
    log_writer: csv.DictWriter,
    two_person: bool,
    prep_seconds: float,
    step_timeout: float,
) -> bool:
    print_header("DEBOUNCE/NOISE TEST")
    print("What this checks: one quick press should not generate many rapid state changes.")
    print("For each button, do ONE clean tap when asked.")

    all_ok = True
    for button in range(1, 6):
        if two_person:
            announce_two_person_step(
                (
                    f"BUTTON {button}. QUICK TAP ONCE NOW. "
                    f"CALL SIGN {CALL_SIGNS[button]}."
                ),
                prep_seconds=prep_seconds,
            )
            transitions = count_transitions(button=button, window_seconds=step_timeout)
        else:
            wait_for_enter(f"Press Enter, then quickly tap BUTTON {button} once...")
            transitions = count_transitions(button=button, window_seconds=1.2)

        append_log(log_writer, "debounce_transitions", button, f"count={transitions}")
        print(f"  BUTTON {button}: transitions seen = {transitions}")

        if transitions <= 4:
            print("  PASS")
        else:
            print("  WARN/FAIL: high transition count, likely bounce/noise.")
            all_ok = False

    print("\nResult: PASS" if all_ok else "\nResult: FAIL/WARN")
    return all_ok


def measure_high_duration(button: int, timeout: float = 5.0) -> float:
    pin = BUTTON_PINS[button]
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline and GPIO.input(pin) == 0:
        time.sleep(0.003)
    if GPIO.input(pin) == 0:
        return 0.0

    start = time.monotonic()
    while time.monotonic() < deadline and GPIO.input(pin) == 1:
        time.sleep(0.003)
    return time.monotonic() - start


def test_hold(
    log_writer: csv.DictWriter,
    two_person: bool,
    prep_seconds: float,
    hold_threshold: float,
    hold_timeout: float,
) -> bool:
    print_header("HOLD TEST")
    print("What this checks: each button can stay held steadily for about 2 seconds.")

    all_ok = True
    for button in range(1, 6):
        if two_person:
            announce_two_person_step(
                (
                    f"BUTTON {button}. PRESS AND HOLD NOW. "
                    f"TARGET {hold_threshold:.1f} SECONDS. CALL SIGN {CALL_SIGNS[button]}."
                ),
                prep_seconds=prep_seconds,
            )
        else:
            wait_for_enter(f"Press Enter, then hold BUTTON {button} for about 2 seconds...")

        held_seconds = measure_high_duration(button=button, timeout=hold_timeout)
        append_log(log_writer, "hold_duration", button, f"seconds={held_seconds:.3f}")
        print(f"  BUTTON {button}: held for {held_seconds:.2f}s")

        if held_seconds >= hold_threshold:
            print("  PASS")
        else:
            print("  FAIL: hold not stable/long enough.")
            all_ok = False

    print("\nResult: PASS" if all_ok else "\nResult: FAIL")
    return all_ok


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPIO button hardware test runner")
    parser.add_argument(
        "--mode",
        choices=["smoke", "mapping", "debounce", "hold", "all"],
        default="all",
        help="Which test mode to run",
    )
    parser.add_argument(
        "--smoke-seconds",
        type=float,
        default=15.0,
        help="Duration for smoke mode",
    )
    parser.add_argument(
        "--log",
        default=f"button_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        help="CSV file path for event log",
    )
    parser.add_argument(
        "--two-person",
        action="store_true",
        help="Enable screen-caller/booth-operator flow with repeated, shoutable commands",
    )
    parser.add_argument(
        "--step-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for each expected action in mapping/debounce two-person mode",
    )
    parser.add_argument(
        "--prep-seconds",
        type=float,
        default=3.0,
        help="Countdown before each spoken two-person command",
    )
    parser.add_argument(
        "--hold-threshold",
        type=float,
        default=1.5,
        help="Minimum held time (seconds) to count as PASS in hold test",
    )
    parser.add_argument(
        "--hold-timeout",
        type=float,
        default=12.0,
        help="Max seconds to wait for press+release in hold test",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.two_person and args.step_timeout < 20.0:
        print("Two-person mode enabled: increasing --step-timeout to 20 seconds for call delays.")
        args.step_timeout = 20.0

    setup_gpio()

    print_header("Raspberry Pi GPIO Button Test Runner")
    print("Button map (logical -> BCM GPIO):")
    for button, pin in BUTTON_PINS.items():
        print(f"  Button {button} -> GPIO {pin}")
    print(f"\nLog file: {args.log}")

    if args.two_person:
        print("\nTwo-person mode: ON")
        print("  - Person A (screen): reads each CALL OUT line aloud twice")
        print("  - Person B (booth): performs the requested button action")
        print("  - Timing windows are widened for shout/phone delay")
    else:
        print("\nTwo-person mode: OFF")

    results: list[tuple[str, bool]] = []

    with open(args.log, "w", newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=["timestamp", "event_type", "button", "details"])
        writer.writeheader()

        if args.mode in ("smoke", "all"):
            results.append(("smoke", test_smoke(writer, args.smoke_seconds)))
        if args.mode in ("mapping", "all"):
            results.append(
                (
                    "mapping",
                    test_mapping(
                        writer,
                        step_timeout=args.step_timeout,
                        two_person=args.two_person,
                        prep_seconds=args.prep_seconds,
                    ),
                )
            )
        if args.mode in ("debounce", "all"):
            results.append(
                (
                    "debounce",
                    test_debounce(
                        writer,
                        two_person=args.two_person,
                        prep_seconds=args.prep_seconds,
                        step_timeout=max(args.step_timeout / 8.0, 1.2),
                    ),
                )
            )
        if args.mode in ("hold", "all"):
            results.append(
                (
                    "hold",
                    test_hold(
                        writer,
                        two_person=args.two_person,
                        prep_seconds=args.prep_seconds,
                        hold_threshold=args.hold_threshold,
                        hold_timeout=args.hold_timeout,
                    ),
                )
            )

    print_header("SUMMARY")
    for test_name, passed in results:
        print(f"{test_name:10s}: {'PASS' if passed else 'FAIL'}")

    all_passed = all(passed for _, passed in results)
    print("\nOverall:", "PASS" if all_passed else "FAIL")
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
    finally:
        GPIO.cleanup()