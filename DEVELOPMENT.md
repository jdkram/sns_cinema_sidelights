---
human-authors: Jonny Kram
ai-authors: ["Claude Haiku"]
---

# Development guide: adding or changing light patterns

This guide explains how to safely create new light sequences.

## Safety first

Before changing patterns for live use:

- avoid fast strobe effects
- avoid full-brightness rapid flashing
- review for photosensitivity risk
- test thoroughly before audience use (try funky things)

## How patterns are structured in code

Core flow:

- button press handled in `src/main.cpp`
- selected sequence started by `src/CSequenceManager.cpp`
- each sequence is a class in `src/sequences/`
- sequence classes schedule events (`fade`, `pulse`, `set brightness`) on LEDs

Current button mapping is created in `CSequenceManager` constructor order.

Current mapping in this snapshot:

| Button | Sequence | Slot |
|--------|----------|------|
| 1 | `CSequenceAmbient` | 1 |
| 2 | `CSequenceFadeOutSimple` | 2 |
| 3 | `CSequenceHeartBeat` | 3 |
| 4 | `CSequenceFadeInSparkle` | 4 |
| 5 | `CSequenceKnightRider` | 5 |
| — | `CSequenceEmber` | 6 |
| — | `CSequenceBreathing478` | 7 |

Slots 6 and 7 exist in the binary but are not currently assigned to a physical button. To assign them, edit `BUTTON_SEQUENCE_MAP` in `src/main.cpp` -- no cmake needed, just `make -j2`. See DEPLOYMENT.md for the full remap workflow.

## Make a small change (easiest path)

If you want gentler behaviour, start by editing constants in an existing sequence file, for example:

- timings (`FADE_TIME`, interval values)
- max brightness levels
- randomisation range

Then rebuild and test:

```bash
cmake .
make -j2
./main
```

## Add a new sequence (structured path)

1. Copy an existing sequence pair in `src/sequences/` (for example `CSequenceAmbient.*`).
2. Rename class and files (for example `CSequenceCalmWave.*`).
3. Implement constructor scheduling using existing event helpers from `CSequence`:
   - `fadeEventAdd(...)`
   - `pulseEventAdd(...)`
   - `brightnessSetEventAdd(...)`
4. Register new files in `src/sequences/CMakeLists.txt`.
5. Include and add sequence in `src/CSequenceManager.cpp`.
6. Rebuild and test manually.

## Testing checklist before deployment

1. startup works from command line (`./main`)
2. each button starts expected sequence
3. no sequence causes long freezes/high CPU spikes
4. boot service still starts cleanly
5. behaviour is acceptable for audience comfort

## Suggested workflow for reliability

- keep production branch stable
- develop new patterns in a separate branch
- bench test first (not in live booth)
- create release notes with button mapping changes
- deploy during maintenance window
- keep rollback SD card/image ready

## Versioning suggestion for non-technical teams

Use simple tags in release notes:

- `v2026.03-calm1`
- include one-line change summary per button

Example:

- Button 5 changed from fast sweep to slower gentle sweep

## Documentation discipline

Whenever pattern behaviour changes, update:

- `README.md` (button mapping summary)
- `USER_SETUP.md` only if user-facing operation changed
- maintenance notes with test date and tester initials
