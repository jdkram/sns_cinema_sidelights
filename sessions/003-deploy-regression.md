---
human-authors: Jonny Kram
ai-authors: ["Claude Sonnet 4.6"]
session-date: 2026-03-13
session-number: "003"
---

# Session 003: Deploy from session-001 carry-forward; sequences 4–6 invisible

**Date:** 2026-03-13
**Location:** Star and Shadow Cinema
**Tester:** Jonny
**Commit on Pi at start:** ___________ (run `git -C /home/pi/sidelights rev-parse --short HEAD`)
**Commit on dev machine at start:** `9e20cad` ("Enhance wiringPi integration and improve Python compatibility")

---

## Session summary

Session went significantly off-plan. Planned agenda was SSH hardening / Tailscale (session 002) but that was not carried out. Instead the session focused on deploying the current codebase from the session-001 carry-forward list and testing sequence visibility.

**Net result: code deployed. Buttons 1–3 produce some visible output. Sequences 4, 5, 6 produce nothing visible via CLI. Python I2C probe scripts were attempted but never produced visible output on the lights. Root causes unconfirmed.**

---

## Phase 1: Connect and verify

- [x] SSH in
- [x] `i2cdetect -y 1` — `0x40`, `0x60`, `0x70` visible (expected)
- [x] Service status checked

**Notes:**

```text
[fill in anything noteworthy from startup checks]
```

---

## Phase 2: Deploy

- [x] `git pull` on Pi — up to date (or pulled changes)
- [x] `cmake . && make -j2` — build completed
- [ ] `rm CMakeCache.txt` before cmake? (tick if yes — affects whether new source files were picked up)

**Commit deployed on Pi:** ___________ (fill in)

**Build notes:**

```text
[any errors, warnings, or anything unexpected from the build]
```

---

## Phase 3: Sequence testing

The `BUTTON_SEQUENCE_MAP` in `main.cpp` at this commit is `{1, 2, 3, 6, 5}`:

| Button | Sequence | Works? | Notes |
|--------|----------|--------|-------|
| 1 | Ambient (seq 1) | vaguely yes | |
| 2 | FadeOutSimple (seq 2) | vaguely yes | |
| 3 | HeartBeat (seq 3) | vaguely yes | |
| 4 | → Ember (seq 6, remapped) | not confirmed | button not tested separately |
| 5 | → KnightRider (seq 5) | not confirmed | |

CLI tests (`./main N` launches sequence N directly, bypassing buttons):

| Command | Result |
|---------|--------|
| `./main 4` (FadeInSparkle) | **nothing visible** |
| `./main 5` (KnightRider) | **nothing visible** |
| `./main 6` (Ember) | **nothing visible** |

**Key observations:**
- "Vaguely work" for buttons 1–3 means some visible change was seen, not a full confirmed
  healthy sequence. Exact nature not recorded.
- KnightRider (seq 5) has been non-functional since session 001 — expected.
- Ember (seq 6) and FadeInSparkle (seq 4) failing via CLI is new or newly confirmed failing.
  In session 001 notes, Ember was remapped to button 4 "for diagnostics" but no checkbox
  was ticked confirming it was actually tested. Its working state is unconfirmed.
- Whether sequences 4–6 throw errors to stdout or silently do nothing: **not captured**.
  This is important diagnostic information — see "Before you leave" section.

---

## Phase 4: Python I2C probe

The corrected probe scripts from session 001 (`pwm_scan.py`, `pwm_sweep.py`) were attempted.
Both scripts were rewritten in session 001 with:
- `smbus` (not smbus2) / explicit open/close (no `with` context manager)
- `MODE1 = 0x20` (auto-increment enabled)
- Per-register byte writes (no `write_i2c_block_data`)
- Correct wired channels: 2–7 and 8–13 on each board
- Active-low polarity: off_tick=0 → LED on, off_tick=4095 → LED off

**Result: no visible output from Python scripts in any session. Cause unconfirmed.**

Most probable causes (in descending likelihood):

1. **Scripts run without `sudo`** — on Raspbian Stretch, I2C access may require root or `i2c` group
   membership. Check: `groups pi` — does it include `i2c`?
2. **Script stopped before reaching a wired channel** — the full channel scan (`pwm_scan.py`)
   takes ~14 minutes for both boards (all 24 channels × 1 second each). Channels 0, 1, 14, 15
   are unwired. If stopped early, a wired channel may never have been reached.
3. **Active-low polarity still wrong in the code actually run on the Pi** — unlikely if the
   corrected scripts from session 001 were used rather than an older version.
4. **I2C writes silently rejected by hardware** — unlikely since C++ main works.

---

## Before you leave: capture these before walking out (~5 minutes)

Run these while you still have SSH. Paste output here or save to a text file.

```bash
# 1. I2C hardware health
sudo i2cdetect -y 1
# Expected: 0x40 and 0x60. If missing → hardware / wiring problem.
```

```bash
# 2. Confirm deployed commit on Pi
git -C /home/pi/sidelights rev-parse --short HEAD
```

```bash
# 3. Is 'pi' in the i2c group? (relevant to Python probe failures)
groups pi
# Expected to include 'i2c'. If not: sudo usermod -aG i2c pi (takes effect on next login)
```

```bash
# 4. Does Ambient work via CLI? (isolates button-press path from sequence engine)
sudo /home/pi/sidelights/main 1
# Run for 5-8 seconds, then Ctrl+C.
# If lights do something → binary works for seq 1 regardless of button presses.
# If nothing → binary itself may be broken for CLI invocation, or LEDs are unhealthy.
```

```bash
# 5. What does Ember print to terminal, and does it do anything visual?
sudo /home/pi/sidelights/main 6
# Run for 8-10 seconds, then Ctrl+C.
# Note: what EXACTLY is printed to the terminal (startup messages, any errors)?
# This tells us whether the sequence started at all, vs started but produced no I2C output.
```

```bash
# 6. Service health at end
sudo systemctl restart sns-sidelights.service
sudo systemctl status sns-sidelights.service
```

**Results:**

```text
pi@raspberrypi:~ $ sudo i2cdetect -y 1          # confirm 0x40 and 0x60 still visible
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: 40 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: 60 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: 70 -- -- -- -- -- -- --                         
pi@raspberrypi:~ $ git -C /home/pi/sidelights rev-parse --short HEAD   # which commit is deployed
9e20cad
pi@raspberrypi:~ $ groups pi                    # does it include 'i2c'? (likely why Python probe did nothing)
pi : pi adm dialout cdrom sudo audio video plugdev games users input netdev spi i2c gpio
pi@raspberrypi:~ $ sudo /home/pi/sidelights/main 1   # does Ambient work via CLI? (5 seconds then Ctrl+C)
SNS Lights started

Available sequences:
  1: Ambient
  2: FadeOutSimple
  3: HeartBeat
  4: FadeInSparkle
  5: KnightRider
  6: Ember
  7: Breathing478

Button map:
  Button 1 -> 1: Ambient
  Button 2 -> 2: FadeOutSimple
  Button 3 -> 3: HeartBeat
  Button 4 -> 6: Ember
  Button 5 -> 5: KnightRider

Usage: ./sns_lights [SEQUENCE_NUMBER]
  ./sns_lights        -- run normally, buttons active
  ./sns_lights 6      -- start Ember immediately, buttons active
  ./sns_lights --help -- print this message

KnightRider sequence length: 47.01s
CLI: starting 1: Ambient
Starting sequence
^C
pi@raspberrypi:~ $ sudo /home/pi/sidelights/main 6   # note exactly what's printed — did Ember even start?
SNS Lights started

Available sequences:
  1: Ambient
  2: FadeOutSimple
  3: HeartBeat
  4: FadeInSparkle
  5: KnightRider
  6: Ember
  7: Breathing478

Button map:
  Button 1 -> 1: Ambient
  Button 2 -> 2: FadeOutSimple
  Button 3 -> 3: HeartBeat
  Button 4 -> 6: Ember
  Button 5 -> 5: KnightRider

Usage: ./sns_lights [SEQUENCE_NUMBER]
  ./sns_lights        -- run normally, buttons active
  ./sns_lights 6      -- start Ember immediately, buttons active
  ./sns_lights --help -- print this message

KnightRider sequence length: 47.01s
CLI: starting 6: Ember
Starting sequence
^C
pi@raspberrypi:~ $ 
```

---

## Remote access plan

Session 002 (SSH hardening + Tailscale) was not executed. This is now the **top priority** for
off-site troubleshooting.

### Option A: Tailscale (preferred — enables live SSH from anywhere)

⚠️ Tailscale dropped official support for Raspbian Stretch (Debian 9) around 2023. The install
script may refuse, or install a very old version. Try it; if it fails, fall back to Option B.

Do this while still at the cinema (Pi has internet access there):

```bash
# 1. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. Start and authenticate
sudo tailscale up
# The terminal prints a URL — open it on your phone to authenticate.
# Once done, Tailscale assigns the Pi an IP like 100.x.x.x

# 3. Note that IP
tailscale ip -4
```

From home, once authenticated:
```bash
ssh pi@<tailscale-ip>    # password auth until key auth is set up
```

Tailscale survives reboots once authenticated. The Pi will appear in your Tailscale admin
console at https://login.tailscale.com/admin/machines.

If `curl` fails or the install script errors on Stretch, see session 002 notes for the
offline `.deb` approach (download `armhf` package on dev machine, `scp` it over, `dpkg -i`).

### Option B: Auto-update cron (code deploys from home, no live SSH)

If Tailscale is not viable right now, this gives one-way deployment via git push.
Push new code to GitHub from home → Pi pulls it and rebuilds at 3am.

```bash
# On the Pi:

# 1. Create the update script
cat > /home/pi/update_sidelights.sh << 'SCRIPT'
#!/bin/bash
set -e
cd /home/pi/sidelights
git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
    logger -t sns-update "New commit detected, rebuilding..."
    git pull origin main
    cmake . && make -j2
    sudo systemctl restart sns-sidelights.service
    logger -t sns-update "Deploy complete: $(git rev-parse --short HEAD)"
else
    logger -t sns-update "Already up to date: $(git rev-parse --short HEAD)"
fi
SCRIPT

chmod +x /home/pi/update_sidelights.sh

# 2. Test it once manually
bash /home/pi/update_sidelights.sh

# 3. Add to cron: run at 3am daily
(crontab -l 2>/dev/null; echo "0 3 * * * /home/pi/update_sidelights.sh") | crontab -
crontab -l    # confirm the entry was added
```

**Notes on Option B:**
- Works only if the repo is public (no credentials needed for HTTPS git pull). If private,
  the Pi needs an SSH deploy key — defer that to the next in-person session.
- Requires cinema WiFi to be on at 3am. If off, the cron silently skips — no damage.
- Logs via syslog: `journalctl -t sns-update -n 20` to review deploy history.
- Does **not** give you live SSH access for debugging. You can push diagnostic code changes
  (e.g. extra logging to a file) that the Pi will pull automatically, then read the output
  next visit (or via Tailscale if that's later set up).

---

## Sign-off

- [ ] Diagnostics from "Before you leave" section captured
- [ ] Remote access option set up (Tailscale or auto-update cron) — or explicitly deferred
- [ ] Service restarted and healthy at end of session
- [ ] Lights in a reasonable state (not stuck full-on)

**Commit on Pi at end of session:** ___________

**Overall result:** PARTIAL — code deployed; sequences 1–3 vaguely working; sequences 4–6
invisible via CLI; Python probes never produced visible output; root causes unknown.

---

## Carry-forward

```text
PRIORITY 1: Remote access
  Set up Tailscale (Option A) or auto-update cron (Option B) before next session.
  Without this, all debugging and code deployment requires a physical visit to the cinema.

PRIORITY 2: Diagnose why sequences 4–6 produce no visible output via CLI
  Key unknowns going into next session:
  - Does `./main 1` work via CLI? (confirms that CLI invocation mode itself works)
  - What does `./main 6` print to stdout/stderr? (did the sequence start, or did it crash?)
  - Was the build fresh (rm CMakeCache.txt + cmake + make) or a relink of old .o files?
    Old .o files may mean new source files (Ember, Breathing478) were silently skipped.
  - Is Ember actually a regression from session 001, or was it never confirmed working?
    Session 001 Phase 3 checkbox for button 4 (Ember) was unticked.

PRIORITY 3: Python I2C probe script
  (Easier to diagnose remotely if Tailscale is set up.)
  - Run: sudo python3 /tmp/pwm_scan.py (service stopped first)
  - If /tmp was cleared (it is after reboots), recreate from session 001 Phase 6b notes.
  - Key question: does it need sudo? Check `groups pi` for 'i2c' group first.
  - Full scan takes ~14 minutes — let it run; don't stop after 30 seconds.

ACTIVE-LOW REMINDER (do not re-derive):
  Buttons 1–3 work → CLEDManager formula `onTime = 4095 - powerScaledUp` is CORRECT.
  LEDs are active-low: pca9685FullOff at brightness=100 is CORRECT — do not "fix" it.
  A previous AI agent applied a wrong "fix" (changing FullOff to FullOn). It was reverted.
  The revert is in git history. Do not re-apply that change.

SESSION 002 (SSH hardening) still pending:
  The full SSH key auth setup and key rotation plan described in session 002 was not done.
  Until a physical revisit, password auth is the only SSH option (or Tailscale if set up today).
```
