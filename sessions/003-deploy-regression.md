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

**Net result: code deployed. Buttons 1–3 produce some visible output (only at higher
brightness levels). Sequences 4–6 produce nothing visible via CLI. Root cause: suspected
hardware degradation raising the minimum visible brightness threshold. See session 004 for
the isolation tests that will confirm this.**

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
- "Vaguely work" for buttons 1–3: further testing (post-session) confirmed that Ambient
  via CLI produces visible output, but **only at higher brightness levels**. LEDs assigned
  low brightness values appear completely off. All lights go dark simultaneously at times.
  HeartBeat (seq 3) looks like a correct heartbeat pattern (peaks at 70%).
- **Brightness threshold hypothesis:** the hardware can no longer produce visible output
  below some brightness threshold (estimated 40-60%). This explains all observations:
  - Ambient (5-100%): only the upper range is visible, lower values look "off"
  - Ember (12-55%): entire range likely below threshold → nothing visible
  - FadeInSparkle (8-82%): sparkles far below threshold; final 82% might show if you wait 60s
  - KnightRider (100%): should be above threshold — its failure may be a separate code bug
- Eyewitness from original deployment (~2018) reports Ambient used to show smooth brightness
  variations with all LEDs always on. The current winking behaviour is a change, not by design.
- Both `./main 1` and `./main 6` print "Starting sequence" with no errors. The sequences
  start correctly; the issue is output visibility, not code crashes.

---

## Phase 4: Python I2C probe

Python probe scripts from session 001 produced no visible output. Low priority now —
session 004's C++ diagnostic tests (`--test-all-on` etc.) bypass the event engine
directly via CLEDManager, making the Python probes redundant for hardware diagnosis.

The scripts are in `/tmp` (cleared on reboot) and documented in session 001 Phase 6b
if ever needed again.

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

## Remote access

Deferred. See session 002 for the full Tailscale/SSH hardening plan. Not the
priority while hardware is producing degraded output.

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
RESOLVED since this session:
  - CLI invocation works: ./main 1 produces visible output (high brightness only).
  - ./main 6 (Ember) starts without errors — "nothing visible" is a brightness threshold
    issue, not a code crash.
  - pi user is in i2c group (confirmed in "Before you leave" output).

NEXT SESSION: 004 — Hardware isolation tests
  Diagnostic test modes added to main.cpp (--test-all-on, --test-sweep, --test-fade,
  --test-half). These bypass the event engine and write directly to PCA9685. Will
  definitively separate hardware from software issues. See sessions/004-hardware-isolation.md.

  Must do a clean build on Pi: rm CMakeCache.txt && cmake . && make -j2

STILL PENDING:
  - Remote access (Tailscale or auto-update cron) — deferred until hardware is diagnosed.
  - RPi.GPIO force-reinstall — blocked; low priority vs hardware diagnosis.
  - Button 4 still remapped to Ember (should be FadeInSparkle). Low priority.

ACTIVE-LOW REMINDER (do not re-derive):
  CLEDManager formula `onTime = 4095 - powerScaledUp` is CORRECT.
  pca9685FullOff at brightness=100 is CORRECT — do NOT change to pca9685FullOn.
```
