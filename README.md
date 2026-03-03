`#ai-input`

# Star and Shadow sidelight controller

Public code for a Raspberry Pi based sidelight controller used at Star and Shadow cinema.

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
