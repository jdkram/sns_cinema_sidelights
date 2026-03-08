---
human-authors: Jonny Kram
ai-authors: ["Claude Sonnet 4.6"]
session-date: TBD
session-number: "001"
---

# Session 001: Get test_runner.py working; characterise PWM and light responsiveness

**Date:** ___________
**Location:** Star and Shadow Cinema
**Tester:**
**Commit on Pi before session:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)
**Commit on dev machine before session:** (run `git rev-parse --short HEAD`)

---

## Anticipated failure modes (read before starting)

This Pi has likely not received OS or package updates since ~2019 (probably running Raspbian Buster, Debian 10). Known issues to expect:

| Symptom | Cause | Where addressed |
| ------- | ----- | --------------- |
| `apt-get` gives 404 errors | Buster packages moved to archive.debian.org | Phase 4b |
| `apt-get` gives IP/DNS errors | DNS failing over phone hotspot | Phase 4b |
| `RPi.GPIO` already works | Was pre-installed on 2019 Pi OS images | Phase 4a |
| `import smbus2` fails but `import smbus` works | Old Pi OS uses `python3-smbus` package, not `smbus2` | Phase 6a |
| `cmake .` fails with wiringPi not found | wiringPi was retired in 2019, may be missing | Phase 2 |
| `make -j2` misses new source files | cmake cache is stale from 2019 build | Phase 2 |
| Service shows `Unit not found` | Pi may use old rc.local startup, not systemd | Phase 1 |

**The Python annotation issue is already fixed in this repo** (added `from __future__ import annotations` to `test_runner.py`). If the Pi has a cached old copy of the script without this fix, you will see `TypeError: unsupported operand type(s) for |` on Python 3.9 or a `SyntaxError` variant on 3.7. The fix is to git pull or manually add `from __future__ import annotations` after the module docstring.

---

## Phase 1: Connect and verify

- [ ] SSH in: `ssh pi@<pi-ip>`
- [ ] Service running: `sudo systemctl status sns-sidelights.service`
  - If `Unit not found`: the Pi may be using the old `rc.local` startup method, not systemd. See DEPLOYMENT.md "Migrating from rc.local to systemd".
  - If `inactive (dead)` or failed: `journalctl -u sns-sidelights.service -n 30`
- [ ] I2C visible: `i2cdetect -y 1`
  - Expected: `0x40` and `0x60`
  - If `command not found`: `sudo apt-get install -y i2c-tools`
- [ ] Lights look right (not stuck, not off)
- [ ] Quick button check: press 1-5, each triggers expected sequence

Record the Pi's environment -- this shapes everything else in the session:

```bash
cat /etc/os-release          # OS name and version (Buster = Debian 10, Stretch = 9, Bullseye = 11)
python3 --version            # expect 3.7.x on Buster, 3.9.x on Bullseye
pip3 --version               # note version and Python it's tied to
dpkg -l | grep -i rpi.gpio   # check if RPi.GPIO is already installed
dpkg -l | grep -i smbus      # check if smbus is already installed
```

**OS version:** ___________
**Python version:** ___________
**RPi.GPIO already installed:** yes / no
**smbus already installed:** yes / no

**Notes:**

```text

```

---

## Phase 1.5: Check I2C bus speed and thermal health

These are quick checks that directly affect whether sequences like KnightRider will work. Do them before the build.

### I2C bus speed

The C++ main loop runs tight (no sleep). Each active fade event writes to I2C every iteration. KnightRider has overlapping fades -- at 100kHz I2C, that can produce enough I2C traffic to lag visibly behind animation timing. At 400kHz, it should be fine.

```bash
# Check current I2C bus speed
cat /sys/module/i2c_bcm2835/parameters/baudrate 2>/dev/null || \
cat /sys/module/i2c_bcm2708/parameters/baudrate 2>/dev/null
```

- [ ] **100000** → slow mode; enable fast mode (see below)
- [ ] **400000** → already in fast mode; no action needed

**To enable fast mode** (safe, reversible on reboot if you remove the line):

```bash
sudo nano /boot/config.txt
# Add this line at the end:
dtparam=i2c_arm_baudrate=400000
# Save, then reboot:
sudo reboot
```

After reboot, re-check with the same `cat` command above.

**I2C bus speed recorded:** ___________
**Fast mode enabled this session:** yes / no / already set

---

### Thermal throttling check

The Pi Zero runs at 100% CPU during any sequence (tight loop). After 5+ minutes of running, the board can throttle -- which would affect animation timing.

```bash
# Run during a sequence, a few minutes in
vcgencmd get_throttled   # 0x0 = healthy; anything else = throttling has occurred
vcgencmd measure_temp    # check current temp
```

| Metric | Value |
| ------ | ----- |
| `get_throttled` | |
| `measure_temp` | |

- [ ] 0x0 (healthy) → no action
- [ ] Any non-zero throttled flags → note it; consider reducing animation complexity or adding a heatsink

**Notes:**

```text

```

---

## Phase 2: Deploy recent changes

This Pi has likely not been built against since ~2019. New sequence files (Ember, Breathing478) have been added since then, so cmake must be re-run -- `make -j2` alone will silently skip new files.

- [ ] `cd /home/pi/sidelights && git pull`
  - If git remote is stale or auth fails, copy files manually from your dev machine instead: `rsync -av --exclude='.git' /path/to/sns_cinema_sidelights/ pi@<pi-ip>:/home/pi/sidelights/`
- [ ] Always run both on this first session: `cmake . && make -j2`
  - Build takes 2-4 minutes on Pi Zero; the fan-less Zero gets warm, this is normal
  - If cmake fails with `wiringPi not found`: wiringPi may need reinstalling (see below)
  - If make fails with missing `.cpp` files: cmake picked up a stale cache; `rm CMakeCache.txt` then `cmake . && make -j2`
- [ ] Stop service before testing: `sudo systemctl stop sns-sidelights.service`
- [ ] `./main` -- confirm starts cleanly, Ctrl+C when done
- [ ] `sudo systemctl start sns-sidelights.service`
- [ ] `sudo systemctl status sns-sidelights.service`
- [ ] Note deployed commit:

**If wiringPi is missing:** it was retired in 2019 but should still be installed on a 2019 Pi. Check with `dpkg -l | grep wiringpi`. If absent, build from source:

```bash
cd /tmp
git clone https://github.com/WiringPi/WiringPi   # community fork
cd WiringPi
./build
```

This needs internet. If DNS is broken, use the DNS fix from Phase 4 first, then come back.

**Notes:**

```text

```

---

## Phase 3: Verify everything still works

- [ ] Button 1 (Ambient)
- [ ] Button 2 (FadeOutSimple)
- [ ] Button 3 (HeartBeat)
- [ ] Button 4 (FadeInSparkle)
- [ ] Button 5 (KnightRider)
- [ ] No flicker, freeze, or lag

**Notes:**

```text

```

---

## Phase 4: Install RPi.GPIO and get test_runner.py working

### Background

`test_runner.py` imports `RPi.GPIO`. Last visit, `apt install python3-rpi.gpio` produced IP address errors. On a ~2019 Pi running Buster or Stretch, there are two possible causes:

- **DNS failure over the hotspot** -- the Pi couldn't resolve `archive.raspberrypi.org` (most likely)
- **404 from dead archive URLs** -- Buster and Stretch are EOL; their packages moved to `archive.debian.org` and the old source URLs return 404

On a 2019 Pi, `python3-rpi.gpio` was installed by default as part of the base image. **Check first -- it may already be there.** The apt step may not be needed at all.

The fix for any missing packages is to **avoid relying on the Pi's internet access**. Prepare files on your dev machine before the session and copy them over SSH -- SSH uses the local hotspot, not the internet, so it works even when DNS is broken.

---

### Before you leave for the cinema: prep on dev machine

Do this at home where you have reliable internet. It takes 2 minutes.

**For test_runner.py (RPi.GPIO):** on a 2019 Pi, `RPi.GPIO` is probably already installed. If not, `rpi-lgpio` is a drop-in replacement. Download its wheel as a fallback:

```bash
# On your dev machine -- adjust python version to match Pi if needed (check with: python3 --version on Pi)
pip3 download rpi-lgpio --only-binary=:all: --platform linux_armv6l --python-version 311 -d ./pi_wheels/
# If that platform tag returns nothing, try armv7l (Pi 3/4):
pip3 download rpi-lgpio --only-binary=:all: --platform linux_armv7l --python-version 311 -d ./pi_wheels/
ls ./pi_wheels/
```

If no pre-built wheel is available (empty directory), download as source and plan to build on the Pi:

```bash
pip3 download rpi-lgpio --no-binary=:all: -d ./pi_wheels/
```

**For Phase 6 (smbus2):** smbus2 is pure Python, so no platform fuss:

```bash
pip3 download smbus2 --no-deps -d ./pi_wheels/
ls ./pi_wheels/
```

Copy everything to the Pi at session start (once SSH is up):

```bash
ssh pi@<pi-ip> mkdir -p /home/pi/pi_wheels
scp ./pi_wheels/*.whl ./pi_wheels/*.tar.gz pi@<pi-ip>:/home/pi/pi_wheels/ 2>/dev/null; true
```

**Files prepped (tick what you downloaded):**

- [ ] `rpi_lgpio-*.whl` or `rpi_lgpio-*.tar.gz`
- [ ] `smbus2-*.whl`

---

### Step 4a: Check what's already there

```bash
python3 -c "import RPi.GPIO; print(RPi.GPIO.VERSION)"
```

- [ ] Works → skip to Phase 5
- [ ] Fails with `ModuleNotFoundError` → continue

```bash
dpkg -l | grep -i gpio
pip3 list 2>/dev/null | grep -i gpio
```

**What you see:**

```text

```

---

### Step 4b: Try apt -- but diagnose DNS first

Before running apt, check whether DNS actually works from the Pi:

```bash
ping -c 2 8.8.8.8                    # tests basic internet routing (no DNS)
ping -c 2 archive.raspberrypi.org    # tests DNS resolution
```

- [ ] Both work → DNS is fine, try apt normally (step 4b-i)
- [ ] First works, second fails → DNS broken; fix it temporarily, then try apt (step 4b-ii)
- [ ] First fails too → no internet at all, skip to step 4c

**Step 4b-i: apt when DNS works:**

```bash
sudo apt-get install -y python3-rpi.gpio
python3 -c "import RPi.GPIO; print(RPi.GPIO.VERSION)"
```

If apt returns 404 errors (not connection errors), the package sources for this OS version have moved to the archive. Fix them first:

```bash
# For Buster (Debian 10) -- check with cat /etc/os-release
sudo sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list
sudo sed -i 's|security.debian.org|archive.debian.org/debian-security|g' /etc/apt/sources.list
sudo sed -i '/buster-updates/d' /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y python3-rpi.gpio
```

**Step 4b-ii: fix DNS temporarily and retry:**

```bash
# Lost on reboot, which is fine
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
ping -c 2 archive.raspberrypi.org    # confirm it resolves now
sudo apt-get install -y python3-rpi.gpio
python3 -c "import RPi.GPIO; print(RPi.GPIO.VERSION)"
```

- [ ] apt install worked and import succeeds → skip to Phase 5
- [ ] apt fails or import still broken → go to step 4c

**Output / errors:**

```text

```

---

### Step 4c: Install from prepped wheel files (offline fallback)

If you prepped wheel files at home and copied them over, install directly:

```bash
cd /home/pi/sidelights
python3 -m venv .venv --system-site-packages
ls /home/pi/pi_wheels/
.venv/bin/pip install --no-index --find-links /home/pi/pi_wheels/ rpi-lgpio
.venv/bin/python3 -c "import RPi.GPIO; print(RPi.GPIO.VERSION)"
```

If the wheel directory has a `.tar.gz` source dist instead of a pre-built wheel, pip will try to compile. This needs build tools:

```bash
sudo apt-get install -y python3-dev build-essential    # may also have DNS issues
```

If that also fails, stop here. Record what happened and carry forward to next session.

- [ ] Works → note invocation command below
- [ ] Fails → record exact error, stop

**Output / errors:**

```text

```

**Invocation command confirmed working (fill in):**

```bash
# python3 test_runner.py --mode smoke
# or: .venv/bin/python3 test_runner.py --mode smoke
```

---

### Step 4d: GPIO permissions (if import works but raises PermissionError at runtime)

```bash
sudo usermod -a -G gpio pi    # then log out and back in, or use sudo as a shortcut:
sudo python3 test_runner.py --mode smoke
```

- [ ] `sudo` works → note it; fine for testing
- [ ] Still fails → record exact error

**Notes:**

```text

```

---

### On OS updates: do not run them

Do not run `apt upgrade` or `apt dist-upgrade` during a cinema session.

Reasons:

- The Pi runs wiringPi and GPIO kernel modules. An uncontrolled upgrade can break these, and there is no time to recover during a visit.
- The download is large and the hotspot is slow and unreliable. A partial upgrade is worse than no upgrade.
- The device runs mostly offline by design (see OPERATIONS.md). Security updates are a low priority compared to show stability.
- If the OS is old (Buster/Bullseye), security updates for end-of-life packages are not meaningful anyway -- the attacker model for this device doesn't justify the upgrade risk.

**What to do instead:** if OS updates are ever needed, do it on a spare SD card with a stable wired connection, test fully, then swap cards. Never upgrade in place on the production Pi during a session.

The only apt commands acceptable in a session are targeted single-package installs (e.g. `apt-get install -y python3-rpi.gpio`) -- and only if DNS is confirmed working.

---

## Phase 5: Run the button test suite

Only reach this phase once `python3 test_runner.py --help` works without errors.

Use the confirmed invocation command from Phase 4.

---

### Step 5a: Smoke test

```bash
python3 test_runner.py --mode smoke
```

Press any button several times during the 15-second window.

- [ ] At least one press detected: PASS / FAIL

**Output:**

```text

```

---

### Step 5b: Full test suite

```bash
python3 test_runner.py --mode all
```

Work through each button as prompted.

| Test | Result |
| ---- | ------ |
| smoke | PASS / FAIL |
| mapping | PASS / FAIL |
| debounce | PASS / FAIL |
| hold | PASS / FAIL |
| **overall** | PASS / FAIL |

**Log file saved to:**

```text
button_test_log_YYYYMMDD_HHMMSS.csv
```

Copy log off Pi for reference (from your dev machine):

```bash
scp pi@<pi-ip>:/home/pi/sidelights/button_test_log_*.csv .
```

**Anything unexpected:**

```text

```

---

## Phase 6: PWM and light responsiveness characterisation

This is the "if time allows" section. The goal is to empirically measure the limits of the PCA9685 hardware rather than rely on assumptions.

The PCA9685 has 12-bit PWM resolution (values 0-4095) across 24 channels (two boards). All of this is exercised through the C++ `main` binary. For quick interactive probing we use `smbus2` to write I2C directly.

---

### Step 6a: Confirm smbus2 is available

The probe scripts below use `smbus2`. On a 2019 Pi, the installed package is `python3-smbus`, which provides `import smbus` (no "2"). These are compatible for our purposes -- if `smbus2` is not available but `smbus` is, edit the `import smbus2` line in each script to `import smbus` and replace `smbus2.SMBus` with `smbus.SMBus`.

```bash
python3 -c "import smbus2; print('smbus2 ok')"
python3 -c "import smbus; print('smbus ok')"    # fallback to check
```

- [ ] `smbus2` works → use scripts as written
- [ ] Only `smbus` works → note it; edit import lines in each script before running
- [ ] Neither works → install from prepped wheel or apt:

  ```bash
  sudo apt-get install -y python3-smbus    # provides 'import smbus'
  # or from wheel:
  .venv/bin/pip install --no-index --find-links /home/pi/pi_wheels/ smbus2
  ```

**Which smbus module is available:** smbus2 / smbus / neither

**Notes:**

```text

```

---

### Step 6b: Write a minimal PWM probe script

Stop the service first so there is no I2C conflict:

```bash
sudo systemctl stop sns-sidelights.service
```

Create a quick throwaway script to sweep a single channel:

```bash
cat > /tmp/pwm_probe.py << 'EOF'
#!/usr/bin/env python3
"""
Quick PWM sweep probe for PCA9685.
Writes a single channel and steps through brightness values.
Run: python3 /tmp/pwm_probe.py
"""
import smbus2
import time

I2C_BUS = 1
PCA_ADDR = 0x40   # primary board; try 0x60 for secondary
CHANNEL = 0       # LED channel 0-15 on this board

MODE1    = 0x00
LED0_ON_L  = 0x06

def set_channel(bus, addr, ch, on, off):
    base = LED0_ON_L + 4 * ch
    bus.write_i2c_block_data(addr, base, [
        on & 0xFF, (on >> 8) & 0x0F,
        off & 0xFF, (off >> 8) & 0x0F,
    ])

def init(bus, addr):
    bus.write_byte_data(addr, MODE1, 0x00)
    time.sleep(0.01)

with smbus2.SMBus(I2C_BUS) as bus:
    init(bus, PCA_ADDR)
    print(f"Sweeping channel {CHANNEL} on 0x{PCA_ADDR:02X}")
    print("Watch the light. Press Ctrl+C to stop.")

    # Step through 0 to 4095 slowly
    for pwm in range(0, 4096, 64):
        set_channel(bus, PCA_ADDR, CHANNEL, 0, pwm)
        print(f"  PWM = {pwm:4d}  ({pwm/4095*100:.1f}%)")
        time.sleep(0.3)

    # Hold at max
    set_channel(bus, PCA_ADDR, CHANNEL, 0, 4095)
    print("At maximum. Ctrl+C to end.")
    time.sleep(5)

    # Off
    set_channel(bus, PCA_ADDR, CHANNEL, 0, 0)
    print("Off.")
EOF
python3 /tmp/pwm_probe.py
```

Observe and record:

- [ ] First visible light at PWM value: ___________ (lowest value where the LED is clearly on)
- [ ] Saturation point (if visible): ___________ (value where further increase has no visible effect)
- [ ] Sweep looks linear / logarithmic to the eye? ___________
- [ ] Any flicker during the sweep? ___________
- [ ] Any I2C errors during the script? ___________

**Notes:**

```text

```

---

### Step 6c: Measure response latency (rough)

Try reducing the sleep between commands to find where the hardware stops keeping up:

```bash
cat > /tmp/pwm_latency.py << 'EOF'
#!/usr/bin/env python3
"""
PWM rate test: how fast can we send commands before visual lag or I2C errors?
"""
import smbus2
import time

I2C_BUS = 1
PCA_ADDR = 0x40
CHANNEL = 0
LED0_ON_L = 0x06

def set_channel(bus, addr, ch, off_val):
    base = LED0_ON_L + 4 * ch
    bus.write_i2c_block_data(addr, base, [
        0x00, 0x00,
        off_val & 0xFF, (off_val >> 8) & 0x0F,
    ])

with smbus2.SMBus(I2C_BUS) as bus:
    bus.write_byte_data(PCA_ADDR, 0x00, 0x00)
    time.sleep(0.01)

    for delay_ms in [100, 50, 20, 10, 5, 2, 1]:
        delay = delay_ms / 1000.0
        print(f"\nDelay between commands: {delay_ms}ms")
        errors = 0
        t_start = time.monotonic()
        for i in range(50):
            val = 4095 if (i % 2 == 0) else 0
            try:
                set_channel(bus, PCA_ADDR, CHANNEL, val)
                time.sleep(delay)
            except OSError as e:
                errors += 1
                print(f"  I2C error at step {i}: {e}")
        elapsed = time.monotonic() - t_start
        print(f"  50 commands in {elapsed:.2f}s ({elapsed/50*1000:.1f}ms avg)")
        print(f"  Errors: {errors}")
        if errors > 0:
            print("  --> I2C errors at this rate, this is the limit")
            break
        time.sleep(0.5)

    set_channel(bus, PCA_ADDR, CHANNEL, 0)
    print("\nOff. Done.")
EOF
python3 /tmp/pwm_latency.py
```

Record findings:

| Delay (ms) | Errors? | Notes |
| ---------- | ------- | ----- |
| 100ms | | |
| 50ms | | |
| 20ms | | |
| 10ms | | |
| 5ms | | |
| 2ms | | |
| 1ms | | |

**Minimum reliable delay between commands:** ___________

**Notes:**

```text

```

---

### Step 6d: Bring service back up

```bash
sudo systemctl start sns-sidelights.service
sudo systemctl status sns-sidelights.service
```

- [ ] Service back up and running

---

## Sign-off

- [ ] Service is running and healthy at end of session
- [ ] Lights in appropriate state for leaving
- [ ] Log files copied off Pi (button test CSV, any probe script output)
- [ ] Notes above completed

**End commit on Pi:** ___________

**Overall result:** PASS / FAIL / PARTIAL

**Carry forward to next session:**

```text
- Did RPi.GPIO install? Which method worked?
- Did button tests pass?
- What were the PWM limits found?
- Any open issues?
```
