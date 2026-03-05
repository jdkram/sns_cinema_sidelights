`#ai-input`

# Sequence simulator

A Python tool for writing and previewing new light sequences on your laptop,
without needing the Pi or hardware.

Sequences are defined in Python and rendered live in the terminal as a grid of
24 warm-amber LED blocks. When a sequence looks right, it can be ported to C++
for deployment -- the Python API maps directly to the C++ one.

---

## Requirements

Python 3.10+ on any machine. No extra libraries needed. A terminal with ANSI
true-colour support (this includes most terminals on Linux, macOS, and
Windows Terminal).

---

## Quick start

From the project root:

```bash
python3 simulator/preview.py                # interactive picker
python3 simulator/preview.py heartbeat      # by name
python3 simulator/preview.py 3              # by button number (1-5)
python3 simulator/preview.py --list         # see all sequences
```

The display updates in real time. Press `Ctrl+C` to stop.

---

## What the display shows

```
SNS Sidelight Simulator
────────────────────────────────────────────────────────────
01   02   03   [  SCREEN  ]   04   05   06
07   08   09   [  SCREEN  ]   10   11   12
13   14   15   [  SCREEN  ]   16   17   18
19   20   21   [  SCREEN  ]   22   23   24
────────────────────────────────────────────────────────────
Sequence: heartbeat      Elapsed: 0:03
Press 1-5 to switch sequence, or Ctrl+C to quit
```

Each numbered block represents a physical LED. The colour indicates brightness:
- Dark brown/black = off
- Bright amber/yellow = full brightness

The layout mirrors the physical hardware: LEDs 1-3 on the left, 4-6 on the right,
with the cinema screen in the middle.

### Interactive switching

While a sequence is playing, press **1, 2, 3, 4, or 5** on your keyboard to
instantly jump to that button's sequence. No need to Ctrl+C and restart. This
is useful for testing transitions or comparing how different patterns look.

---

## Adding a new sequence

### Step 1: write the Python version

Open `simulator/sequences.py` and add a new class at the bottom, before
the `SEQUENCES` registry:

```python
class SequenceMyThing(Sequence):
    """
    One-line description (shown in --list output).

    Longer explanation of the effect and intent.
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)  # loop=False for one-shots

        # Schedule events here. All times are in seconds.
        #
        # Fade LED 1 to brightness 80 over 2 seconds starting at t=0:
        #   self.fade_event_add(led=1, brightness=80, start=0.0, length=2.0)
        #
        # Fade all 24 LEDs to 0 starting at t=5, over 3 seconds:
        #   self.fade_event_add_all_leds(brightness=0, start=5.0, length=3.0)
        #
        # Snap LED 12 to brightness 50 at t=1.5:
        #   self.brightness_set_event_add(led=12, brightness=50, time_s=1.5)
        #
        # Snap all LEDs to 0 immediately (often used to reset at start):
        #   self.brightness_set_event_add_all_leds(brightness=0, time_s=0.0)
        #
        # Flash LED 7 to brightness 90 at t=2.0, hold for 0.1s then snap off:
        #   self.pulse_event_add(led=7, brightness=90, time_s=2.0, length=0.1)

        # For looping sequences, set the loop point at the end:
        self._length_seconds = 5.0  # loop every 5 seconds
```

### Step 2: register it

Add it to the `SEQUENCES` dict at the bottom of `sequences.py`:

```python
SEQUENCES: dict[str, type[Sequence]] = {
    ...
    "mything": SequenceMyThing,
}
```

If it is replacing an existing button, also update `BUTTON_MAP`.

### Step 3: preview it

```bash
python3 simulator/preview.py mything
```

Iterate on the constants until it looks right.

---

## Event types explained

There are three building blocks. All coordinates are in seconds.

### `fade_event_add(led, brightness, start, length)`

Smoothly interpolates an LED from whatever brightness it is currently at
to `brightness` over `length` seconds, starting at `start`.

Use this for: most things -- ambient fades, slow reveals, gradual dimming.

### `brightness_set_event_add(led, brightness, time_s)`

Instantly sets an LED to `brightness` at `time_s`. No transition.

Use this for: reset to black at the start of a sequence, or hard cuts.

### `pulse_event_add(led, brightness, time_s, length)`

Snaps an LED to `brightness` at `time_s`, holds it, then snaps back to 0
at `time_s + length`.

Use this for: sparkle and twinkle effects. The sparkle build-up (button 4)
generates thousands of these at varying times and densities to create its
effect.

All-LED variants (`_all_leds`) are available for each type.

---

## Notes on timing

- Sequences are 100% pre-baked in the constructor. `update()` just plays
  them back; no logic or decisions happen during playback.
- Times are always in seconds (the engine converts to milliseconds internally).
- For looping sequences, set `self._length_seconds` at the end of `__init__`.
- Non-looping sequences play once and hold their final state.

---

## Porting to C++

When a sequence is ready to deploy, port it to a C++ class in `src/sequences/`:

| Python method | C++ equivalent |
|---|---|
| `fade_event_add(led, b, s, l)` | `fadeEventAdd(led, b, s, l)` |
| `fade_event_add_all_leds(b, s, l)` | `fadeEventAddAllLeds(b, s, l)` |
| `brightness_set_event_add(led, b, t)` | `brightnessSetEventAdd(led, b, t)` |
| `brightness_set_event_add_all_leds(b, t)` | `brightnessSetEventAddAllLeds(b, t)` |
| `pulse_event_add(led, b, t, l)` | `pulseEventAdd(led, b, t, l)` |
| `self._length_seconds = x` | `mSequenceLengthSeconds = x;` |
| `self.random_fraction()` | `(float) rand() / (float) RAND_MAX` |
| `random.randint(a, b)` | `a + rand() % (b + 1 - a)` |

Copy an existing sequence class (e.g. `CSequenceAmbient.*`) as a template,
rename it, and replace the constructor body with your logic.

Then register it in `src/CSequenceManager.cpp` and add it to
`src/sequences/CMakeLists.txt`. See [DEVELOPMENT.md](../DEVELOPMENT.md) for
the full walkthrough.
