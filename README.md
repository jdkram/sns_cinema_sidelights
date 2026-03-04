`#ai-input`

# Star and Shadow sidelight controller

Repository status: this is the active public development repository for the sidelight controller.

Public code for a Raspberry Pi based sidelight controller used at Star and Shadow cinema.

## New install? Start here

To set things up from scratch, go to [USER_SETUP.md](USER_SETUP.md).

## What this repository contains

- C++ controller application (`main`)
- sequence/event engine for LED animations
- PCA9685 driver integration (24 channels across two I2C addresses)
- optional button input test script (`test.py`)

## What this repository does not contain

- private network credentials
- device-specific login details
- shell histories from production devices
- complete Pi home-folder snapshots

## Quick start (development)

1. Install build dependencies (`cmake`, C/C++ toolchain, GPIO/I2C dependencies on target Pi).
2. Build from project root:
   - `cmake .`
   - `make -j2`
3. Run manually:
   - `./main`

## Runtime behaviour

- listens for five GPIO button inputs
- starts one sequence per button press
- updates LED brightness through PCA9685 over I2C

## Button test suite (guided)

For a more thorough GPIO button check, use `test_runner.py`.

Run all tests:

```bash
python3 test_runner.py --mode all
```

Run one test mode only:

```bash
python3 test_runner.py --mode mapping
```

Available modes:

- `smoke` (basic press/release detection)
- `mapping` (checks each physical button maps to the expected number)
- `debounce` (checks for noisy or bouncing button signals)
- `hold` (checks each button can remain stably pressed)
- `all` (runs everything in sequence)

### Two-person mode (screen + projection booth)

Use this when one person is near the controller/screen and another person is at the booth panel.

Recommended command:

```bash
python3 test_runner.py --mode all --two-person --step-timeout 25 --prep-seconds 4
```

How it works:

- Person A (screen side) reads each `CALL OUT` line aloud twice
- Person B (booth side) performs the requested button action
- the script waits longer per step, so shout/phone delay is tolerated

If there is heavy delay on a phone call, increase timeout further:

```bash
python3 test_runner.py --mode all --two-person --step-timeout 35 --prep-seconds 5
```

### What a non-technical user should expect to see

1. You run `python3 test_runner.py --mode all`.
2. The script prints a simple title and the button map.
3. In each section, it tells you exactly which button to press and when.
   In two-person mode, it prints a bold `CALL OUT` message intended to be spoken.
4. After each step, it prints `PASS` or `FAIL`.
5. At the end, it shows a short summary plus an overall `PASS`/`FAIL`.
6. It also saves a log file in the current folder (for example `button_test_log_20260303_183015.csv`).

If you see a fail:

- `mapping` fail usually means a wiring mismatch (wrong button connected to a pin)
- `debounce` fail usually means switch bounce/noise (may need wiring cleanup or software debounce)
- `hold` fail usually means unstable contact while holding the button
- no events in `smoke` usually means power/wiring/GPIO setup issue

## Current button map (important)

Current code maps buttons to sequences in this order:

1. **Button 1** → Ambient (slow random fades)
2. **Button 2** → FadeOutSimple (all lights fade down to off)
3. **Button 3** → HeartBeat (double-pulse loop)
4. **Button 4** → FadeInSparkle (sparkle pulses, then full brightness)
5. **Button 5** → KnightRider (back-and-forth sweep loop)

If this mapping changes in code, update docs in the same commit.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for service setup and reliability guidance.

For a beginner-friendly step-by-step guide (flash card, SSH, install, auto-start), see [USER_SETUP.md](USER_SETUP.md).

For network policy, hardening, and update automation choices, see [OPERATIONS.md](OPERATIONS.md).

For adding/changing lighting patterns safely, see [DEVELOPMENT.md](DEVELOPMENT.md).

Before major refactors, run and complete [BASELINE_SIGNOFF.md](BASELINE_SIGNOFF.md).

## Security and operations

If you need operational access to a live unit, request credentials directly from Star and Shadow maintainers.

See [SECURITY.md](SECURITY.md) for disclosure and maintenance policy.
