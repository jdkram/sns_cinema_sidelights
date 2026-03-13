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

This Pi has likely not received OS or package updates since ~2019 (**confirmed Raspbian Stretch, Debian 9** — not Buster as originally expected). Known issues to expect:

| Symptom | Cause | Where addressed |
| ------- | ----- | --------------- |
| `apt-get` gives 404 errors | Buster/Stretch packages moved to archive.debian.org | Phase 4b |
| `apt-get` gives IP/DNS errors | DNS failing over phone hotspot | Phase 4b |
| `legacy.raspberrypi.org` DNS failure | Raspbian Stretch uses this host; DNS may fail on hotspot | Phase 4b |
| `RPi.GPIO` already works | Was pre-installed on 2019 Pi OS images | Phase 4a |
| `import smbus2` fails but `import smbus` works | Old Pi OS uses `python3-smbus` package, not `smbus2` | Phase 6a |
| `cmake .` fails with wiringPi not found | wiringPi was retired in 2019, may be missing | Phase 2 |
| `make -j2` misses new source files | cmake cache is stale from 2019 build | Phase 2 |
| Service shows `Unit not found` | Pi may use old rc.local startup, not systemd | Phase 1 |
| `test_runner.py` crashes with `SyntaxError: future feature annotations is not defined` | Python 3.5 doesn't have `from __future__ import annotations` (needs 3.7+) | Phase 4 |
| Phase 6 probe scripts crash with `SyntaxError: invalid syntax` on f-strings | Python 3.5 doesn't have f-strings (needs 3.6+) | Phase 6 |
| `pip3: command not found` | pip not installed as pip3 on this image; use `python3 -m pip` or `sudo apt-get install -y python3-pip` | Phase 4 |

**The Python annotation issue is already fixed in this repo** (added `from __future__ import annotations` to `test_runner.py`). If the Pi has a cached old copy of the script without this fix, you will see `TypeError: unsupported operand type(s) for |` on Python 3.9 or a `SyntaxError` variant on 3.7. The fix is to git pull or manually add `from __future__ import annotations` after the module docstring.

---

## Phase 1: Connect and verify

- [x] SSH in: `ssh pi@<pi-ip>`
- [x] Service running: `sudo systemctl status sns-sidelights.service`
  - If `Unit not found`: the Pi may be using the old `rc.local` startup method, not systemd. See DEPLOYMENT.md "Migrating from rc.local to systemd".
  - If `inactive (dead)` or failed: `journalctl -u sns-sidelights.service -n 30`
- [x] I2C visible: `i2cdetect -y 1`
  - Expected: `0x40` and `0x60`
  - If `command not found`: `sudo apt-get install -y i2c-tools`
        APT SOURCE FIX NEEDED — RESOLVED: see Phase 4b notes. i2c-tools was already installed once sources were fixed.
  - **Result:** `0x40` (primary PCA9685), `0x60` (secondary PCA9685), `0x70` (PCA9685 all-call broadcast address — expected, not a mystery device)
- [x] Lights look right (not stuck, not off)
- [x] Quick button check: press 1-5, each triggers expected sequence
        4 does nothing until 60 seconds in
        5 does nothing visible

Record the Pi's environment -- this shapes everything else in the session:

```bash
cat /etc/os-release          # OS name and version (Buster = Debian 10, Stretch = 9, Bullseye = 11)
python3 --version            # expect 3.7.x on Buster, 3.9.x on Bullseye
pip3 --version               # note version and Python it's tied to
dpkg -l | grep -i rpi.gpio   # check if RPi.GPIO is already installed
dpkg -l | grep -i smbus      # check if smbus is already installed
```

**OS version:** Raspbian Stretch (Debian 9)
**Python version:** 3.5.3
**RPi.GPIO already installed:** Broken — dist-info for 0.7.1 present, .so extension missing (ImportError at runtime)
**smbus already installed:** yes / no

**Notes:**

```text
pip3: command not found — pip is not installed on this image.
Use `python3 -m pip` as a substitute, or install pip with:
  sudo apt-get install -y python3-pip

CRITICAL: Python 3.5.3 is older than expected.
  - `from __future__ import annotations` requires Python 3.7+ — test_runner.py will
    SyntaxError at import time on this Python version.
  - f-strings (used in Phase 6 probe scripts) require Python 3.6+ — those scripts
    will also SyntaxError and must be rewritten with .format() before running.
  - test_runner.py will need the `from __future__ import annotations` line removed
    and all union-type annotations (e.g. `int | None`) replaced with `Optional[int]`
    or removed entirely before it will run on this Pi.
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

- [ ] **No output at all** → old kernel doesn't expose this sysfs path; check `/boot/config.txt` instead (see below)

**If the `cat` command returns nothing:** the kernel is too old to expose the baudrate via sysfs. Use this instead to check and set:

```bash
grep -i baudrate /boot/config.txt   # if nothing returned, you're on the 100kHz default
grep -i i2c /boot/config.txt        # shows all i2c-related config lines
```

**To enable fast mode** (safe, reversible by removing the line):

```bash
echo "dtparam=i2c_arm_baudrate=400000" | sudo tee -a /boot/config.txt
sudo reboot
```

After reboot, re-check with `grep -i baudrate /boot/config.txt` — the line should be present. The `cat /sys/module...` path may still return nothing on old kernels even after the change; the config file is the ground truth.

**I2C bus speed recorded:** 100kHz default (no baudrate line in /boot/config.txt; `dtparam=i2c_arm=on` present confirming I2C enabled)
**Fast mode enabled this session:** yes — added `dtparam=i2c_arm_baudrate=400000` to /boot/config.txt and rebooted

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

- [x] 0x0 (healthy) → no action
- [ ] Any non-zero throttled flags → note it; consider reducing animation complexity or adding a heatsink

**Notes:**

```text
34.7degC after having been on a while
```

---

## Phase 2: Deploy recent changes

This Pi has likely not been built against since ~2019. New sequence files (Ember, Breathing478) have been added since then, so cmake must be re-run -- `make -j2` alone will silently skip new files.

- [x] `cd /home/pi/sidelights && git pull`
  - If git remote is stale or auth fails, copy files manually from your dev machine instead: `rsync -av --exclude='.git' /path/to/sns_cinema_sidelights/ pi@<pi-ip>:/home/pi/sidelights/`
  - **Note:** SSH returned exit 255 immediately after the reboot for baudrate change — Pi was still coming up. Wait ~30s and retry.
- [x] Always run both on this first session: `cmake . && make -j2`
  - Build takes 2-4 minutes on Pi Zero; the fan-less Zero gets warm, this is normal
  - If cmake fails with `wiringPi not found`: wiringPi may need reinstalling (see below)
  - If make fails with missing `.cpp` files: cmake picked up a stale cache; `rm CMakeCache.txt` then `cmake . && make -j2`
  - **Note:** this build includes the `usleep(10000)` patch in `update()` — the tight loop had no sleep at all before; this prevents I2C bus saturation on KnightRider and explains why button 5 did nothing visible on the old binary.
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
Source build of WiringPi from /tmp/WiringPi failed (Makefile:82 wiringPi.o error) —
community fork requires GPIO v2 ioctl structs (kernel 5.10+); this Pi is on 4.9.59.
git stash had nothing to save (usleep patch already committed/in tree).
git pull: already up-to-date.
cmake . && make -j2: succeeded immediately. [100%] Built target main.
./main: failed with libwiringPi.so: cannot open shared object file.
Root cause: /usr/lib/libwiringPi.so symlink pointed to /usr/local/lib/libwiringPi.so.2.44
which was missing. A previous source build in /home/pi/wiringPi/ had the real .so but
never ran `make install`.
Fix: sudo cp /home/pi/wiringPi/wiringPi/libwiringPi.so.2.44 /usr/local/lib/ && sudo ldconfig
./main then ran correctly.

wiringPi.h headers NOT in system include paths (/usr/include, /usr/local/include).
The initial cmake+make succeeded only because all 2019 .o files were still valid — make
just relinked without recompiling anything. When CLEDManager.cpp was rsync'd and
recompiled, it failed: "wiringPi.h: No such file or directory".
Fix: added find_path(WIRINGPI_INCLUDE ...) to CMakeLists.txt. cmake now automatically
finds headers in /home/pi/wiringPi/wiringPi/ (old source-build location). After this
change: rm CMakeCache.txt && cmake . && make -j2 should compile cleanly from scratch.
```

---

## Phase 3: Verify everything still works

- [x] Button 1 (Ambient)
- [x] Button 2 (FadeOutSimple)
- [x] Button 3 (HeartBeat)
- [ ] Button 4 (Ember — temporarily remapped from FadeInSparkle for diagnostics, see notes)
- [ ] Button 5 (KnightRider — slowed 5x for diagnostics, see notes)
- [x] No flicker, freeze, or lag

**Notes:**

```text
Button 4 (FadeInSparkle): only the final full-on at 60s was visible. Sparkles not seen.
  Probably correct behaviour: sparkle brightness is 2-8% with short pulses — likely
  invisible in ambient cinema lighting. Sequence is probably working.
  Remapped to Ember for diagnostics (button 4 now confirms Ember works).

Button 5 (KnightRider): absolutely nothing visible. Persistent across old and new binary.
  Total failure — not dim flicker, not wrong colour, completely blank.

--- ESTABLISHED FACT: active-low LED wiring (do not re-derive this) ---
Buttons 1-3 all work → CLEDManager formula `onTime = 4095 - powerScaledUp` is correct.
LEDs are active-low: output LOW = LED on, output HIGH = LED off.
  brightness=0:   onTime=4095 → pca9685PWMWrite(0,4095) → HIGH 99.98% → LED off.   ✓
  brightness=50:  onTime=2048 → pca9685PWMWrite(0,2048) → HIGH 50%    → LED 50%.   ✓
  brightness=100: onTime=0    → pca9685FullOff (value=0) → always LOW  → LED on.   ✓
pca9685FullOff at brightness=100 is CORRECT. Do NOT change it to pca9685FullOn.
pca9685FullOn = output always HIGH = active-low LED OFF. That would be wrong.
(An earlier AI agent incorrectly applied a "fix" to use FullOn. This broke 100% brightness
and was reverted. The revert is in git history. Do not re-apply this change.)

--- KnightRider diagnostic history ---
Hypothesis 1: tight loop without sleep causes I2C bus saturation.
  → Added usleep(10000) → 100Hz cap. Rebuilt and deployed. → STILL nothing.

Hypothesis 2: CLEDManager brightness=100 → FullOff → LED off at peak.
  → INCORRECT. FullOff on active-low = LED on. See above. Original code is correct.
  → The AI-applied "fix" (FullOn) was actually wrong and was reverted.

Hypothesis 3: I2C bus too slow for overlapping fades at 100kHz.
  → Python probe also gave zero output; but probe had two independent bugs:
      (a) `with smbus.SMBus() as bus:` raises AttributeError on old python3-smbus (no __exit__)
      (b) MODE1 reset to 0x00 clears AI bit (auto-increment). write_i2c_block_data then
          writes all 4 bytes to the same register — OFF registers never set → no PWM.
      (c) CHANNEL=0 unwired. CLEDManager maps channels 2-7 and 8-13 on each PCA9685 board.
  → Probe bugs do not explain C++ failure — C++ uses wiringPiI2CWriteReg16 (no AI needed).
  → To isolate I2C speed: KnightRider slowed 5x (STAGGER=1.0s, FADE_TIME=1.5s).
     If slowed KnightRider still shows nothing, I2C speed is NOT the cause.
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

- [x] Both work → DNS is fine, try apt normally (step 4b-i)
- [ ] First works, second fails → DNS broken; fix it temporarily, then try apt (step 4b-ii)
- [ ] First fails too → no internet at all, skip to step 4c

**Note from this session:** DNS resolved fine. The issue was the archive URLs for Stretch being moved — not a DNS problem.

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

**If the Pi is running Stretch (Debian 9):** the codename is different. In addition to the above, use `stretch-updates` instead of `buster-updates`:

```bash
# For Stretch (Debian 9)
sudo sed -i 's|deb.debian.org|archive.debian.org|g' /etc/apt/sources.list
sudo sed -i 's|security.debian.org|archive.debian.org/debian-security|g' /etc/apt/sources.list
sudo sed -i '/stretch-updates/d' /etc/apt/sources.list
sudo apt-get update
sudo apt-get install -y python3-rpi.gpio
```

**If `legacy.raspberrypi.org` fails DNS** (seen in practice on Stretch): this is the Raspbian-specific repo and is not needed for `python3-rpi.gpio`. Comment it out (it may be in `/etc/apt/sources.list` or a separate `/etc/apt/sources.list.d/raspi.list`):

```bash
# Fix DNS first (lost on reboot, harmless):
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
sudo apt-get update

# If legacy.raspberrypi.org still fails, comment it out:
sudo sed -i 's|^deb http://legacy.raspberrypi.org|#deb http://legacy.raspberrypi.org|g' /etc/apt/sources.list
sudo sed -i 's|^deb http://legacy.raspberrypi.org|#deb http://legacy.raspberrypi.org|g' /etc/apt/sources.list.d/raspi.list 2>/dev/null; true
sudo apt-get update
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
- [x] apt fails or import still broken → go to step 4c

**Output / errors:**

```text
Ran Buster sed commands (1st block) then Stretch sed commands (2nd block).
The /buster-updates grep had no results (expected — Pi is Stretch not Buster).
The /stretch-updates grep also had no results (line not present in sources.list).
The raspi.list sed (3rd command in legacy.raspberrypi.org block) had no match —
raspi.list either didn't exist or didn't contain that line.
apt-get update then succeeded. Issue resolved.
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
- [x] Fails — deferred to next session

**Output / errors:**

```text
RPi.GPIO 0.7.1 dist-info present; pip reports "Requirement already satisfied";
but `import RPi.GPIO` gives ImportError: No module named 'RPi.GPIO'.
`ls /usr/local/lib/python3.5/dist-packages/` shows RPi/ dir and RPi.GPIO-0.7.1.dist-info.
The compiled .so extension is missing from inside the RPi/ directory.
python3-dev already at 3.5.3-1, so missing headers is not the cause.
rpi-lgpio uninstall failed: "Cannot uninstall, not installed".
Force-reinstall was not attempted — deferred to next session.
Next time: `ls /usr/local/lib/python3.5/dist-packages/RPi/` to confirm .so absent,
then: `sudo pip3 install --force-reinstall --no-binary :all: RPi.GPIO`
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
- [x] Neither works → install from prepped wheel or apt:

  ```bash
  sudo apt-get install -y python3-smbus    # provides 'import smbus'
  # or from wheel:
  .venv/bin/pip install --no-index --find-links /home/pi/pi_wheels/ smbus2
  ```

**Which smbus module is available:** `smbus` (no "2") — installed via apt this session

**Notes:**

```text
Both `import smbus` and `import smbus2` failed with ImportError.
Fixed with: sudo apt-get install -y python3-smbus
(apt sources already pointing to archive.debian.org from Phase 4b fix)

CRITICAL: old python3-smbus on Stretch does NOT support context manager protocol.
`with smbus.SMBus(I2C_BUS) as bus:` raises AttributeError: __exit__
Fix: use explicit open/close:
  bus = smbus.SMBus(I2C_BUS)
  ...  (do I2C operations)
  bus.close()
All probe scripts in this doc that use `with smbus.SMBus(...) as bus:` must be
changed to this pattern before running on this Pi.
```

---

### Step 6b: Write a minimal PWM probe script

Stop the service first so there is no I2C conflict:

```bash
sudo systemctl stop sns-sidelights.service
```

Create a quick throwaway script to sweep a single channel:

**CRITICAL PROBE RULES for this Pi (Raspbian Stretch, python3-smbus):**
- Use `bus = smbus.SMBus(1)` / `bus.close()` — NO `with smbus.SMBus() as bus:` (no \_\_exit\_\_)
- Set MODE1 = **0x20** (auto-increment enabled). NOT 0x00 — that clears AI, breaking block writes.
- Use per-register **byte** writes. Do NOT use `write_i2c_block_data` — it silently fails without AI.
- Wired PCA9685 channels on each board: **2-7 and 8-13**. Channels 0, 1, 14, 15 are unwired.
- LEDs are **active-low**: off_tick=0 → output LOW → LED on. off_tick=4095 → LED off.
  Mirror C++ formula: off_tick = 4095 - int(brightness% × 4095/100)

Step 1 — channel scanner (run this first to confirm I2C works and find a live channel):

```bash
cat > /tmp/pwm_scan.py << 'EOF'
import smbus, time
I2C_BUS, LED0_ON_L = 1, 0x06

def led_on(bus, addr, ch):
    base = LED0_ON_L + 4 * ch
    bus.write_byte_data(addr, base + 1, 0x00)  # ON_H: clear full-on
    bus.write_byte_data(addr, base + 3, 0x10)  # OFF_H: set full-off bit = output always LOW = LED on

def led_off(bus, addr, ch):
    base = LED0_ON_L + 4 * ch
    bus.write_byte_data(addr, base + 0, 0x00)  # ON_L
    bus.write_byte_data(addr, base + 1, 0x00)  # ON_H
    bus.write_byte_data(addr, base + 2, 0xFF)  # OFF_L = 255
    bus.write_byte_data(addr, base + 3, 0x0F)  # OFF_H = 0x0F -> off_tick=4095 = LED off

for board_addr in [0x40, 0x60]:
    print("Board 0x{:02X}".format(board_addr))
    bus = smbus.SMBus(I2C_BUS)
    bus.write_byte_data(board_addr, 0x00, 0x20)  # MODE1: enable auto-increment
    time.sleep(0.01)
    for ch in list(range(2, 8)) + list(range(8, 14)):
        led_on(bus, board_addr, ch)
        print("  ch {:2d} ON".format(ch))
        time.sleep(0.8)
        led_off(bus, board_addr, ch)
        time.sleep(0.2)
    bus.close()
    print("Board done.")
EOF
python3 /tmp/pwm_scan.py
```

Step 2 — brightness sweep on a known-live channel:

```bash
cat > /tmp/pwm_sweep.py << 'EOF'
import smbus, time
I2C_BUS, PCA_ADDR, CHANNEL = 1, 0x40, 2  # first wired channel on board 0x40
LED0_ON_L = 0x06

def set_brightness(bus, addr, ch, pct):
    off_tick = 4095 - int(pct * 4095.0 / 100.0)  # mirrors C++ CLEDManager formula
    base = LED0_ON_L + 4 * ch
    bus.write_byte_data(addr, base + 0, 0x00)
    bus.write_byte_data(addr, base + 1, 0x00)
    bus.write_byte_data(addr, base + 2, off_tick & 0xFF)
    bus.write_byte_data(addr, base + 3, (off_tick >> 8) & 0x0F)

bus = smbus.SMBus(I2C_BUS)
bus.write_byte_data(PCA_ADDR, 0x00, 0x20)  # MODE1: AI enable
time.sleep(0.01)
print("Sweep ch {} on 0x{:02X}: 0 to 100%".format(CHANNEL, PCA_ADDR))
for pct in range(0, 101, 5):
    set_brightness(bus, PCA_ADDR, CHANNEL, pct)
    print("  {:3d}%".format(pct))
    time.sleep(0.4)
bus.close()
print("Done.")
EOF
python3 /tmp/pwm_sweep.py
```

Observe and record:

- [ ] Channel scanner: first channel that lights up: ___________ (confirms I2C working)
- [ ] Brightness sweep: first visible brightness %: ___________
- [ ] Sweep looks linear / logarithmic to the eye? ___________
- [ ] Any I2C errors during either script? ___________

**Notes:**

```text

```

---

### Step 6c: Measure response latency (rough)

Try reducing the sleep between commands to find where the hardware stops keeping up:

```bash
cat > /tmp/pwm_latency.py << 'EOF'
import smbus, time
I2C_BUS, PCA_ADDR, CHANNEL = 1, 0x40, 2   # ch2 = first wired LED
LED0_ON_L = 0x06

def set_off_tick(bus, addr, ch, off_val):
    base = LED0_ON_L + 4 * ch
    bus.write_byte_data(addr, base + 0, 0x00)
    bus.write_byte_data(addr, base + 1, 0x00)
    bus.write_byte_data(addr, base + 2, off_val & 0xFF)
    bus.write_byte_data(addr, base + 3, (off_val >> 8) & 0x0F)

bus = smbus.SMBus(I2C_BUS)
bus.write_byte_data(PCA_ADDR, 0x00, 0x20)  # MODE1: AI enable
time.sleep(0.01)

# Active-low: off_tick=4095 = LED off, off_tick=0 = LED on
for delay_ms in [100, 50, 20, 10, 5, 2, 1]:
    delay = delay_ms / 1000.0
    print("\nDelay {}ms".format(delay_ms))
    errors = 0
    t_start = time.monotonic()
    for i in range(50):
        val = 0 if (i % 2 == 0) else 4095  # alternate on/off
        try:
            set_off_tick(bus, PCA_ADDR, CHANNEL, val)
            time.sleep(delay)
        except OSError as e:
            errors += 1
            print("  I2C error step {}: {}".format(i, e))
    elapsed = time.monotonic() - t_start
    print("  50 cmds in {:.2f}s ({:.1f}ms avg), errors: {}".format(elapsed, elapsed/50*1000, errors))
    if errors > 0:
        print("  --> limit reached")
        break
    time.sleep(0.5)

set_off_tick(bus, PCA_ADDR, CHANNEL, 4095)  # LED off
bus.close()
print("\nDone.")
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
- RPi.GPIO: BLOCKED. Dist-info for 0.7.1 present but .so extension missing.
  Next session: `ls /usr/local/lib/python3.5/dist-packages/RPi/` to confirm,
  then: `sudo pip3 install --force-reinstall --no-binary :all: RPi.GPIO`
  Phase 5 (test_runner.py / button test suite) is gated on this.

- BUILD: wiringPi.h header problem is now fixed in CMakeLists.txt (find_path added).
  But cmake cache is stale — must run `rm CMakeCache.txt && cmake . && make -j2` on Pi.
  This is mandatory before any button test — the current Pi binary still has incorrect
  CLEDManager code (the wrong FullOn "fix" that was never deployed due to build failure).
  Wait — actually the build failed BEFORE the wrong fix was deployed, so the Pi binary
  is the original 2019 build. Regardless: the repo is now correct; just need a clean build.

- Button 4: remapped to Ember for diagnostics. FadeInSparkle is probably working but
  sparkles are too dim to see in cinema lighting. Remap back after KnightRider is resolved:
  change BUTTON_SEQUENCE_MAP index 3 from 6 back to 4 in main.cpp.

- Button 5 (KnightRider): total failure. Cause unknown after 3 hypotheses eliminated.
  Slowed 5x (STAGGER=1.0s, FADE_TIME=1.5s) for next test. If still nothing at 5x slow,
  I2C speed is not the cause and something deeper needs investigation.
  At 5x slow: full sweep takes ~48s, each LED fades over 1.5s. Should be clearly visible.

- Phase 6 probe scripts: rewritten with per-register byte writes (no write_i2c_block_data),
  MODE1=0x20, correct active-low polarity, correct channels (2-7, 8-13 not 0).
  Separate scan script (pwm_scan.py) and sweep script (pwm_sweep.py).
```
