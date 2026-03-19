---
human-authors: Jonny Kram
ai-authors: ["Claude Sonnet 4.6"]
session-date: YYYY-MM-DD
session-number: "005"
---

# Session 005: Event engine isolation

**Date:** YYYY-MM-DD
**Location:** Star and Shadow Cinema
**Tester:** Jonny
**Commit on Pi before session:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)
**Commit on dev machine before session:** (run `git rev-parse --short HEAD`)

---

## Background: what we know going in

### The FadeOutSimple "slow to act" finding (new from session 004)

Pressing button 2 (FadeOut) after button 4 (Static 75%) or button 5 (AmbientHigh)
feels very slow to respond. After session 004, we believe this is **expected
behaviour** caused by the 27% hardware brightness threshold interacting with
FadeOutSimple's 10-second linear fade:

- From Static 75%: LEDs only cross the visible threshold at ~second 6.4
  `(75-27)/75 * 10s`. So nothing *appears* to happen for over 6 seconds, then
  lights snap off suddenly.
- From Ambient (5-100%, LEDs often already low): threshold crossed almost
  immediately, fade seems instant.

The fade is working correctly; the visual effect is misleading. Session 005 can
confirm this by timing the button-2 response from different starting sequences.
A fix would be: shorten FadeOutSimple's duration (5s), or bias the curve so the
visible portion of the fade is front-loaded.

### The main open question: why do KnightRider and Ember produce zero output?

Every sequence that works drives **all 24 channels simultaneously**. Every
sequence that addresses panels **individually** via the event engine produces
nothing. DIAG sweep (./main 13) addresses individual LEDs and works, but bypasses
the event engine entirely.

**Hypothesis A (hardware/driver):** The PCA9685 / wiringPi driver reliably
latches values when all 16 channels on a board are written in rapid succession,
but silently drops or ignores writes when only 1-2 channels are written to a
board in a given update cycle.

**Hypothesis B (channel reservation bug):** The `ledBrightnessSet` channel
ownership check (`mReservedChannels[led-1] == pEvent`) is blocking writes for
some edge case in KnightRider/Ember that doesn't occur in Ambient/HeartBeat.

**Hypothesis C (threshold masking):** KnightRider's fade *is* writing values,
but spends ~27% of its ramp time below the visible threshold (27%) and the
tester's 20-second observation window missed the brief visible peak. Less likely
since Ember peaks at 55% and should be clearly visible.

The plan for this session is to isolate the failure with increasing specificity.

---

## Phase 1: Connect and verify

- [ ] SSH in: `ssh pi@<pi-ip>`
- [ ] Check service: `sudo systemctl status sns-sidelights.service`
  - Expected: `active (running)`
- [ ] `i2cdetect -y 1` — confirm `0x40` and `0x60` visible
- [ ] Press buttons 1-5, confirm current state is usable for cinema

**Notes:**

```
[status, anything unexpected]
```

---

## Phase 2: Deploy new code (if any prepared before the session)

If debug logging or a new diagnostic sequence was added before the session:

- [ ] Stop service: `sudo systemctl stop sns-sidelights.service`
- [ ] Pull and rebuild:
  ```bash
  cd /home/pi/sidelights
  git pull
  cmake .
  make -j2
  ```
- [ ] Confirm build succeeded

**Notes:**

```
[build output]
```

---

## Phase 3: Confirm the FadeOutSimple threshold effect

This is a quick sense-check to verify the session 004 analysis. No code change
needed — just observe carefully.

### Test A: FadeOut from Ambient (should feel fast)

```bash
sudo ./main 1   # start Ambient
```

Wait 5-10 seconds for LEDs to reach a random state, then press button 2 (FadeOut).

- [ ] How long until lights visibly start dimming? ______ seconds
- [ ] How long until all lights are off? ______ seconds

### Test B: FadeOut from Static 75% (should feel slow)

```bash
sudo ./main 10  # start Static 75%
```

Wait for LEDs to stabilise at 75%, then press button 2 (FadeOut).

- [ ] How long until lights visibly start dimming? ______ seconds
- [ ] How long until all lights are off? ______ seconds
- [ ] Does the fade feel like "nothing is happening for ages, then sudden darkness"?

**Expected result:** Test B should feel much slower, with the visible fade
beginning ~6 seconds in. If that's what you observe, the threshold theory is
confirmed and FadeOutSimple needs a shorter/curved fade (future code change,
not urgent — cinema can live with this).

**Result:**

```
[observations]
```

---

## Phase 4: Event engine isolation tests

This is the main goal of the session. We need to know: can the event engine
write to a single LED at all?

Stop the service if not already stopped: `sudo systemctl stop sns-sidelights.service`

### Test 1: Single-LED event engine write (seq 12: TestSingle)

```bash
sudo ./main 12
```

Expected: LED 5 (or whichever was chosen) lights up to 100% for 10 seconds via
the event engine, then turns off. Watch for 15 seconds.

- [ ] Did LED 5 light up?
- [ ] Was the response immediate or delayed?

**Decision tree:**
- LED lights up → event engine CAN write individual channels. Bug is specific to
  KnightRider/Ember code (channel reservation, timing, or brightness range).
  Move to Test 2.
- LED does NOT light up → event engine is fundamentally broken for single-channel
  writes. Hypothesis A (driver/hardware) is most likely.

**Result:**

```
[observations]
```

### Test 2: KnightRider with debug logging enabled

*Only if debug cout was re-enabled in CSequenceKnightRider.cpp before the session.*

```bash
sudo ./main 5 2>&1 | tee /tmp/knightrider_log.txt
```

Let it run for 15 seconds, then Ctrl+C.

- [ ] Does the log show "KnightRider sequence length: 47s" (or similar) on startup?
- [ ] Does the log show any fade event firing lines?
- [ ] Does the log show "Looping" — suggesting the sequence is completing and looping?
- [ ] Any LEDs visible?

Copy the log off the Pi afterwards:
```bash
# on your dev machine:
scp pi@<pi-ip>:/tmp/knightrider_log.txt .
```

**Result:**

```
[paste key log lines, or note if log was empty/unexpected]
```

### Test 3: Ember with debug logging

*Same as above, if Ember debug logging was enabled.*

```bash
sudo ./main 6 2>&1 | head -200
```

- [ ] Does the log show events firing?
- [ ] Any LEDs visible?

**Result:**

```
[observations]
```

---

## Phase 5: Complete the LED sweep map

From session 004, only LED 1 was recorded as DEAD. Complete the full map now
while you have the service stopped.

```bash
sudo ./main 14
```

Fill in as the sweep runs:

| LED | Board | Physical position | Status |
|-----|-------|-------------------|--------|
| 1   | 0x40  | Left row 1, #1    | DEAD (confirmed session 004) |
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

**Correct the "Physical position" column if the actual physical layout differs.**

**Result:**

```
[any additional dead/dim LEDs beyond LED 1]
```

---

## Phase 6: Physical inspection (only if two people present — needs ladder)

If a second person is available to hold the ladder:

- [ ] Run `sudo ./main 12` (all LEDs on) and wiggle each connector bundle.
  Note if any LEDs flicker when a connector is moved — this identifies cold joints.
- [ ] Visually inspect LED 1's solder connections on board 0x40
  (the dead channel — look for cracked or dull solder joints).
- [ ] Look for corrosion (green/white deposits) on connectors or PCB.

**Inspection notes:**

```
[physical findings]
```

---

## Sign-off

- [ ] Service restarted: `sudo systemctl start sns-sidelights.service`
- [ ] Service healthy: `sudo systemctl status sns-sidelights.service`
- [ ] All 5 buttons confirmed working
- [ ] Lights in reasonable state for cinema use
- [ ] Any log files copied off Pi

**End commit on Pi:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)

**Overall result:** PASS / FAIL / PARTIAL

**What to carry forward to next session:**

```
[unresolved issues, follow-up experiments]
```
