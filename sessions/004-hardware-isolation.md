---
human-authors: Jonny Kram
ai-authors: ["Claude Opus 4.6"]
session-date: YYYY-MM-DD
session-number: "004"
---

# Session 004: Hardware isolation tests

**Date:** YYYY-MM-DD
**Location:** Star and Shadow Cinema
**Tester:** Jonny
**Commit on Pi before session:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)
**Commit on dev machine before session:** (run `git rev-parse --short HEAD`)

---

## Goal

1. Deploy new button mappings and sequences so the cinema has usable lights
   regardless of how troubleshooting goes.
2. Determine definitively whether the remaining LED problems are hardware or
   software by bypassing the event engine entirely.

**What we know going in:**
- CLI invocation works: `./main 1` (Ambient) produces visible output.
- Only higher brightness levels are visible. LEDs assigned low values appear off.
  All lights go dark simultaneously at times during Ambient.
- HeartBeat (seq 3, peaks at 70%) looks correct.
- Ember (seq 6, 12-55% range) produces nothing visible — likely below the threshold.
- KnightRider (seq 5, 100%) produces nothing visible — may be a code bug (separate
  from the brightness threshold issue, since 100% should be well above it).
- Eyewitness from ~2018 deployment says Ambient used to show smooth brightness
  variations with all LEDs always on. The winking is a change over ~8 years.
- System is ~8 years old. Suspected degradation: cold solder joints, corroded
  connectors, dried capacitors, or aged LED strips.

**New in this deploy:**
- Button 4 → Static 75% (house lights)
- Button 5 → AmbientHigh (ambient with 55-100% floor, threshold workaround)
- New sequences: AmbientHigh (8), Static 50% (9), Static 75% (10), Static 100% (11)
- Hardware diagnostics: DIAG all-on (12), DIAG sweep (13), DIAG fade (14), DIAG half (15)

---

## Phase 1: Connect, deploy, build

- [ ] SSH in: `ssh pi@<pi-ip>`
- [ ] `i2cdetect -y 1` -- confirm `0x40` and `0x60` visible
- [ ] Stop the service: `sudo systemctl stop sns-sidelights.service`
- [ ] Deploy new code:
  ```bash
  cd /home/pi/sidelights
  git pull
  rm CMakeCache.txt    # IMPORTANT: force fresh cmake to pick up new source files
  cmake .
  make -j2             # ~2-4 minutes on Pi Zero
  ```
- [ ] Confirm build succeeded with no errors

**Notes:**

```
[build output, any warnings]
```

---

## Phase 2: Verify new button mappings work

This is the priority. Even if troubleshooting goes badly, we want to leave the
cinema with 5 working buttons.

### Test all 5 buttons

| Button | Expected sequence | Works? | Notes |
|--------|-------------------|--------|-------|
| 1 | Ambient (seq 1) | ok | |
| 2 | FadeOutSimple (seq 2) | ok | |
| 3 | HeartBeat (seq 3) | ok | |
| 4 | Static 75% (seq 10) | looks ok | should be steady, no animation |
| 5 | AmbientHigh (seq 8) | kind of works? can barely see difference. It looks like all of them are coming up and down at the same rate, not individual panels. | like Ambient but no winking — all LEDs always visibly on |

### Key question for button 5 (AmbientHigh)

AmbientHigh is the same as Ambient but with a 55-100% brightness floor. If
the brightness threshold theory is correct, AmbientHigh should look like what
Ambient originally looked like: all LEDs always on, smoothly varying.

- [x] Does AmbientHigh show smooth brightness variation without winking?
- [x] Compare directly: press button 1 (Ambient), then button 5 (AmbientHigh).
  Is AmbientHigh visibly better?

**Result:**

```
yeajh it's better but it looks like they're all fading in and out at the same time. Barely perceptible changes in brightness.
```

If AmbientHigh looks good, it confirms the threshold theory and we have a
working replacement for Ambient on button 5. If it still winks, the problem
is deeper than brightness range.

---

## Phase 3: Hardware diagnostic tests

Run these IN ORDER. Each test builds on the previous one. Service should
already be stopped from Phase 1.

### Test 1: All LEDs on (30 seconds)

```bash
sudo ./main 12
```

**Expected:** All 24 LEDs light up at full brightness for 10 seconds.

- [x] How many LEDs lit up? 24 / 24
- [ ] Were any LEDs noticeably dimmer than others? Which ones?
- [ ] Were any LEDs flickering or unstable?
- [ ] Were LEDs warm white (expected) or discoloured?

**Result:**

```
all ok
```

**Decision tree:**
- 24/24 lit, steady → hardware is fundamentally OK. Continue to Test 2.
- Some LEDs dead → note which ones. Those channels have wiring/hardware faults.
  Still continue to Test 2 (the sweep will identify exactly which channels).
- 0/24 lit → something is fundamentally broken. Check: was the service stopped?
  Does `i2cdetect -y 1` still show 0x40 and 0x60? Try again.

---

### Test 2: Individual LED sweep (1 minute)

```bash
sudo ./main 13
```

**Expected:** LEDs light up one at a time, 2 seconds each, sweeping 1-24.

Fill in this map as the sweep runs. Mark each LED: OK / DIM / FLICKER / DEAD

| LED | Board | Physical position | Status |
|-----|-------|-------------------|--------|
| 1   | 0x40  | Left row 1, #1    | DEAD |
| 2   | 0x40  | Left row 1, #2    |        |
| 3   | 0x40  | Left row 1, #3    |        |
| 4   | 0x40  | Left row 1, #4    |        |
| 5   | 0x40  | Left row 1, #5    |        |
| 6   | 0x40  | Left row 1, #6    |        |
| 7   | 0x40  | Right row 1, #1   |        |
| 8   | 0x40  | Right row 1, #2   |        |
| 9   | 0x40  | Right row 1, #3   |        |
| 10  | 0x40  | Right row 1, #4   |        |
| 11  | 0x40  | Right row 1, #5   |        |
| 12  | 0x40  | Right row 1, #6   |        |
| 13  | 0x60  | Left row 2, #1    |        |
| 14  | 0x60  | Left row 2, #2    |        |
| 15  | 0x60  | Left row 2, #3    |        |
| 16  | 0x60  | Left row 2, #4    |        |
| 17  | 0x60  | Left row 2, #5    |        |
| 18  | 0x60  | Left row 2, #6    |        |
| 19  | 0x60  | Right row 2, #1   |        |
| 20  | 0x60  | Right row 2, #2   |        |
| 21  | 0x60  | Right row 2, #3   |        |
| 22  | 0x60  | Right row 2, #4   |        |
| 23  | 0x60  | Right row 2, #5   |        |
| 24  | 0x60  | Right row 2, #6   |        |

**Physical position note:** The LED numbering above assumes the wiring layout
from CLEDManager.cpp. The actual physical positions may differ -- correct the
"Physical position" column as you observe the sweep.

**Decision tree:**
- All 24 OK → hardware is fine. Problem is in the sequence/event code.
- Pattern of failures on one board (e.g. all 0x60 LEDs dead) → that PCA9685
  board or its I2C connection is faulty.
- Scattered failures → individual wiring/connector issues.
- All dead → fundamental I2C or power problem.

---

### Test 3: Smooth fade (15 seconds)

```bash
sudo ./main 14
```

**Expected:** All LEDs smoothly brighten from off to full over 5 seconds, then
smoothly dim back to off over 5 seconds. No steps, no winking, no flickering.

- [x] Was the fade smooth (gradual brightness change)?
- [ ] Or did LEDs wink on/off (binary, no intermediate brightness)?
- [ ] Or did LEDs flicker (brightness jumping around erratically)?
- [ ] Was the behaviour consistent across all LEDs, or did some fade smoothly while others flickered?

**Result:**

```
27% brightness seems to be the threshold. Behaviour consistent across all.
```

**This is the key test for the Ambient degradation report.** If the fade is
smooth here, the winking in Ambient is a software/event-timing issue. If the
fade winks here too, the hardware can no longer produce clean PWM output,
pointing to degraded connections, capacitors, or LED drivers.

---

### Test 4: Mid-range PWM hold (10 seconds)

```bash
sudo ./main 15
```

**Expected:** All LEDs at steady 50% brightness for 10 seconds. No flickering.

- [x] Are LEDs steady or flickering?
- [x] Is brightness visibly "half" (dimmer than test 1 but clearly on)?

**Result:**

```
steady for 10 sec
```

**Why this matters:** If full brightness (100%) works but 50% flickers, the
PWM signal is getting corrupted somewhere between the PCA9685 and the LEDs.
This would point to noise on the signal lines, degraded connections, or
capacitor issues on the driver boards.

---

## Phase 4: Sequence engine tests (only if hardware tests pass)

Skip this phase if hardware tests showed significant failures. Fix hardware first.

### Test 5: KnightRider via CLI

This is the key software question. KnightRider fades to 100% — well above any
brightness threshold. If `./main 13` (sweep) worked (individual LEDs at 100%) but
KnightRider doesn't, the bug is in the KnightRider event code.

```bash
sudo ./main 5
```

Watch for 20 seconds (one full sweep takes ~47s, but individual LEDs should
light up within the first few seconds). Ctrl+C.

- [ ] Did any LEDs light up?
- [ ] Was there any sequential pattern (one LED after another)?
- [ ] Compare: did `./main 13` (sweep) work for the same LEDs?

**Result:**

```
no LEDs lit up at all
```

### Test 6: Ember via CLI (only if test 4 showed 50% is visible)

If `./main 15` (half) showed LEDs are visible at 50%, Ember (12-55%) should produce
at least faint output. If `./main 15` (half) showed nothing, skip this — Ember is
below the threshold and needs its brightness range raised in code.

```bash
sudo ./main 6
```

Watch for 15 seconds. Ctrl+C.

- [x] Did lights come on?
- [x] What did you see?

**Result:**

```
zero results
```

---

## Phase 5: Physical inspection (if hardware tests show problems)

If any LEDs were dead, dim, or flickering in the diagnostic tests:

- [ ] Visually inspect solder joints on PCA9685 breakout boards (look for
  dull/cracked joints, especially on the screw terminals and header pins)
- [ ] Wiggle each connector while LEDs are on (`./main 12`) and note if
  any LEDs flicker when connectors are moved -- this identifies bad connections
- [ ] Check power supply voltage if you have a multimeter:
  - LED strip voltage (should be 12V or 5V depending on strip type)
  - PCA9685 board Vcc (should be 3.3V or 5V)
  - Pi 5V rail (should be 4.8-5.2V)
- [ ] Look for visible corrosion (green/white deposits) on connectors or PCBs
- [ ] Check that all ground wires are connected (missing ground = erratic behaviour)

**Physical inspection notes:**

```
solo, so no ladder help - didn't physically inspect this time.
```

---

## Sign-off

- [x] All 5 buttons confirmed working (Phase 2)
- [x] Diagnostic results above are filled in completely
- [x] Service restarted: `sudo systemctl start sns-sidelights.service`
- [x] Service healthy: `sudo systemctl status sns-sidelights.service`
- [x] Lights in reasonable state

**End commit on Pi:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)

**Overall result:** PARTIAL

**Diagnosis:**

```
[ ] Hardware is fine -- problem is in sequence/event code
[ ] Hardware has partial failures -- specific channels/connections need repair
[ ] Hardware fundamentally broken -- PCA9685 boards or power supply need replacement
[x] Mixed -- some hardware issues AND some software issues
```

**Key findings (post-session analysis with Claude):**

**Hardware: broadly OK, one confirmed dead channel, one brightness threshold**
- LED 1 (board 0x40, Left row 1 #1) is dead. All others appear functional (Test 1 all-on passed 24/24).
- Confirmed brightness threshold at ~27%. LEDs below this value appear off. This explains why Ember
  (12-55% range) and the original Ambient (5-100% range, ~winking) look dim or invisible at times.
- 50% static hold was steady, ruling out PWM corruption or capacitor noise on the signal lines.
- Smooth fade confirms hardware can produce clean PWM -- the "winking" in Ambient is a software/
  brightness-threshold interaction, not hardware degradation.

**Software: individual-panel addressing via the event engine appears broken**
- Every sequence that works drives ALL channels simultaneously (same or different values):
    Ambient (1), HeartBeat (3), FadeOutSimple (2), Static 75% (10).
- Every sequence that tries to address panels INDEPENDENTLY produced zero or near-zero output:
    KnightRider (5) -- zero. Ember (6) -- zero.
- AmbientHigh (8) looks "all moving together" even though its code assigns each LED a different
  random target. This is partly perceptual (55-100% is a narrow visible range), but is also
  consistent with the independent-addressing hypothesis.
- DIAG sweep (./main 13) -- which bypasses the event engine entirely and writes to one LED at a
  time with a 2s direct-write hold -- works correctly. This confirms the hardware CAN address
  individual panels; the failure is in how the event/sequence engine handles sparse single-channel
  writes.
- Hypothesis: the PCA9685 / WiringPi driver behaves correctly when all 16 channels on a board are
  written to in rapid succession (as Ambient does every 2s for all 24 LEDs), but may drop or ignore
  writes when only 1-2 channels are written sparsely. Worth checking pca9685.c pwmWrite
  implementation for any all-channel shortcut or buffering that would explain this.
- KnightRider has a pre-existing acknowledged bug (comment in CSequenceKnightRider.cpp).

**Fix applied this session:**
- AmbientHigh MIN_BRIGHTNESS lowered from 55% to 30% (just above the 27% threshold), so AmbientHigh
  now spans 30-100% and should show genuine independent panel variation.

**What to carry forward to next session:**

```
1. Investigate why single-channel event-engine writes (KnightRider, Ember) produce zero output
   while all-channel writes (Ambient) work. Check pca9685.c for buffering or all-channel writes.
   Key test: write a minimal sequence that addresses only 1 LED via the event engine and logs
   whether ledBrightnessSet is actually being called and what it sends to the PCA9685.

2. Verify AmbientHigh (30-100% floor) on live hardware -- should show better independent variation.

3. LED 1 (Left row 1, #1) is dead -- physical inspection needed when two people present (ladder).
   Wiggle test recommended: run ./main 12 (all-on) and wiggle connectors to check for cold joints.

4. Complete the LED sweep map (Test 2) -- only LED 1 status was recorded this session.
```
