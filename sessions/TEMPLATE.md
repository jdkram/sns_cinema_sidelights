---
human-authors: Jonny Kram
ai-authors: ["Claude Sonnet 4.6"]
session-date: YYYY-MM-DD
session-number: NNN
---

# Session NNN: [Short title]

**Date:** YYYY-MM-DD
**Location:** Star and Shadow Cinema
**Tester:**
**Commit on Pi before session:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)
**Commit on dev machine before session:** (run `git rev-parse --short HEAD`)

---

## Phase 1: Connect and verify (always do this)

These steps confirm the device is alive before touching anything.

- [ ] Connect to Pi over SSH: `ssh pi@<pi-ip>`
  - Note: find IP via router, `arp -a`, or try `raspberrypi.local`
- [ ] Check service is running: `sudo systemctl status sns-sidelights.service`
  - Expected: `active (running)`
  - If not running, check logs: `journalctl -u sns-sidelights.service -n 30`
- [ ] Check I2C devices are visible: `i2cdetect -y 1`
  - Expected: addresses `0x40` and `0x60`
  - If not found: power cycle the Pi, check I2C cable, re-run
- [ ] Visually confirm lights are behaving (not stuck on full/off/wrong pattern)
- [ ] Press each button 1-5 and confirm it triggers the expected sequence

**Notes:**

```
[status, anything unusual]
```

---

## Phase 2: Deploy recent changes (skip if no new code)

Only needed if changes have been committed since last visit.

- [ ] On Pi: `cd /home/pi/sidelights && git pull`
  - If git not set up on Pi, copy files manually: `rsync -av . pi@<pi-ip>:/home/pi/sidelights/`
- [ ] Rebuild: `make -j2` (or `cmake . && make -j2` if CMakeLists.txt changed)
  - Pi Zero build takes 2-4 minutes, this is normal
- [ ] Stop service before testing manually: `sudo systemctl stop sns-sidelights.service`
- [ ] Test manually: `./main`
  - Confirm it starts without errors
  - Test key sequences
  - Ctrl+C when done
- [ ] Restart service: `sudo systemctl start sns-sidelights.service`
- [ ] Confirm service recovered: `sudo systemctl status sns-sidelights.service`
- [ ] Note commit deployed:

**Notes:**

```
[any errors, unexpected output, timing issues]
```

---

## Phase 3: Verify everything still works

Quick pass after any deployment (or as a baseline if skipping Phase 2).

- [ ] Button 1 (Ambient): slow random fades visible
- [ ] Button 2 (FadeOutSimple): lights fade down to off
- [ ] Button 3 (HeartBeat): double-pulse loop
- [ ] Button 4 (FadeInSparkle): sparkle, then full brightness
- [ ] Button 5 (KnightRider): back-and-forth sweep
- [ ] No obvious flicker, freeze, or lag
- [ ] Service still running after manual tests: `sudo systemctl status sns-sidelights.service`

**Notes:**

```
[any failures, unexpected behaviour]
```

---

## Phase 4: [Session-specific goal]

_Replace this section with the specific experiment or troubleshooting task for this session._

---

## Sign-off

- [ ] Service is running and healthy at end of session
- [ ] Lights are in an appropriate state for leaving (not stuck on full brightness)
- [ ] Any log files or test outputs copied off the Pi if needed
- [ ] Notes above are complete enough to reconstruct what happened

**End commit on Pi:** (run `git -C /home/pi/sidelights rev-parse --short HEAD`)

**Overall result:** PASS / FAIL / PARTIAL

**What to carry forward to next session:**

```
[unresolved issues, follow-up experiments]
```
