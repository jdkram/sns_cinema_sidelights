`#ai-input`

# Baseline sign-off checklist (before refactors)

Use this checklist to confirm current behaviour is stable before introducing changes such as pattern config refactors.

## A) Version and environment capture

- [ ] Record private repo commit: `git rev-parse --short HEAD`
- [ ] Record public-export commit (if used): `git -C public-export rev-parse --short HEAD`
- [ ] Record Pi hostname and date/time of test
- [ ] Record tester name/initials

## B) Build verification on target Pi

On the Pi:

```bash
cd /home/pi/sidelights
cmake .
make -j2
```

- [ ] Build succeeds with no compile errors

## C) Manual runtime verification

Run:

```bash
./main
```

- [ ] App starts and does not crash immediately
- [ ] Button 1 behaviour matches docs
- [ ] Button 2 behaviour matches docs
- [ ] Button 3 behaviour matches docs
- [ ] Button 4 behaviour matches docs
- [ ] Button 5 behaviour matches docs
- [ ] No unexpected flicker, freezes, or severe lag

## D) Boot/service verification

- [ ] Service file present at `/etc/systemd/system/sns-sidelights.service`
- [ ] `systemctl status sns-sidelights.service` is healthy
- [ ] Reboot performed
- [ ] Service auto-starts after reboot

## E) Hardware sanity checks

- [ ] `i2cdetect -y 1` shows expected controller addresses (typically `0x40` and `0x60`)
- [ ] Buttons register via app output (or `python test.py` if used)
- [ ] Light outputs are visible on all expected channels/fixtures

## F) Sign-off decision

- [ ] Baseline confirmed stable, safe to begin refactor work
- [ ] If any failure occurred, open issue and stop refactor until resolved

## Notes (fill in)

- Test date/time:
- Location:
- Commit(s) tested:
- Known caveats:
- Sign-off by:
