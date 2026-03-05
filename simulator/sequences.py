# ai-input
"""
sequences.py -- Python ports of all five light sequences

Each class is a direct translation of its C++ counterpart in src/sequences/.
The constructor schedules events using helper methods inherited from Sequence;
no logic runs in update() itself.

Adding a new sequence:
    1. Create a class inheriting from Sequence.
    2. Schedule events in __init__ using:
           fade_event_add(led, brightness, start_seconds, length_seconds)
           brightness_set_event_add(led, brightness, time_seconds)
           pulse_event_add(led, brightness, time_seconds, length_seconds)
       All-LED variants: fade_event_add_all_leds(...), etc.
    3. If the sequence loops, pass loop=True and set self._length_seconds
       at the end of __init__.
    4. Register it in SEQUENCES at the bottom of this file.

Run `python3 simulator/preview.py <name>` to preview your sequence.
When it looks right, port the constructor logic to a new C++ class in
src/sequences/ following the existing class structure -- the helper method
names map one-to-one (just camelCase them and add the LED manager argument).
"""

import random

from engine import LEDManager, Sequence


# ---------------------------------------------------------------------------
# Sequence 1: ambient
# ---------------------------------------------------------------------------

class SequenceAmbient(Sequence):
    """
    Slow random-brightness fades across all 24 LEDs, looping.

    Each LED independently fades to a random brightness over FADE_TIME
    seconds. All LEDs move together in LOOPS batches, giving a gentle
    undulating effect without co-ordinated patterns.

    Button: 1
    C++ source: CSequenceAmbient.cpp
    """

    FADE_TIME = 2       # seconds per fade step
    LOOPS = 100         # number of fade batches before loop point

    def __init__(self, led_manager: LEDManager) -> None:
        length = self.LOOPS * self.FADE_TIME
        super().__init__(led_manager, loop=True, length_seconds=float(length))

        min_brightness = 5
        max_brightness = 100
        current_time = 0.0

        for _ in range(self.LOOPS):
            for led in range(1, 25):
                brightness = random.randint(min_brightness, max_brightness)
                self.fade_event_add(led, brightness, current_time, self.FADE_TIME)
            current_time += self.FADE_TIME


# ---------------------------------------------------------------------------
# Sequence 2: fade-out simple
# ---------------------------------------------------------------------------

class SequenceFadeOutSimple(Sequence):
    """
    Fades all 24 LEDs to zero over 10 seconds, then stops.

    Used as a clean-exit sequence: press button 2 to gracefully dim the
    lights off. If lights are already off when pressed it will appear to
    do nothing -- that is expected behaviour.

    Button: 2
    C++ source: CSequenceFadeOutSimple.cpp
    """

    FADE_TIME_SECONDS = 10.0

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=False)
        self.fade_event_add_all_leds(0, 0.0, self.FADE_TIME_SECONDS)


# ---------------------------------------------------------------------------
# Sequence 3: heartbeat
# ---------------------------------------------------------------------------

class SequenceHeartBeat(Sequence):
    """
    Slow double-pulse loop mimicking a heartbeat rhythm.

    Two pulses per cycle: a brighter shorter one followed by a softer
    longer one, then a rest. Intentionally gentle transitions to avoid
    photosensitivity risk.

    Brightness and transition times were softened from the original
    (100%/0.1s → 70%/0.3s) after field review flagged the original
    as potentially too abrupt.

    Button: 3
    C++ source: CSequenceHeartBeat.cpp
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        current_time = 0.0
        interval = 2.0

        pulse_1_up = 0.3
        pulse_1_down = 0.3
        pulse_1_brightness = 70

        pulse_2_up = 0.4
        pulse_2_down = 0.4
        pulse_2_brightness = 40

        gap = 0.25

        self.fade_event_add_all_leds(pulse_1_brightness, current_time, pulse_1_up)
        current_time += pulse_1_up

        self.fade_event_add_all_leds(0, current_time, pulse_1_down)
        current_time += pulse_1_down + gap

        self.fade_event_add_all_leds(pulse_2_brightness, current_time, pulse_2_up)
        current_time += pulse_2_up

        self.fade_event_add_all_leds(0, current_time, pulse_2_down)
        current_time += pulse_2_down + interval

        self._length_seconds = current_time


# ---------------------------------------------------------------------------
# Sequence 4: fade-in sparkle
# ---------------------------------------------------------------------------

class SequenceFadeInSparkle(Sequence):
    """
    60-second build from complete darkness to full sustained brightness,
    with random sparkle pulses that increase in density and brightness.

    The effect starts completely invisible for roughly the first 30 seconds
    (pulses exist but their brightness is close to 0 early in the timeline).
    This is intentional: it is a slow reveal. Wait for it.

    Button: 4
    C++ source: CSequenceFadeInSparkle.cpp
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=False)

        pulse_length_max = 0.5
        duration_seconds = 60.0
        start_interval = 1.0
        finish_interval = 0.001

        start_led = 1
        end_led = 24

        current_time = 0.0
        last_time = 0.0

        self.brightness_set_event_add_all_leds(0, 0.0)

        while current_time < duration_seconds:
            progress = current_time / duration_seconds
            brightness = progress * 100.0
            interval_range = finish_interval - start_interval
            interval = start_interval + (progress * interval_range)

            for led in range(start_led, end_led + 1):
                if self.random_fraction() < 0.5:
                    pulse_length = pulse_length_max * (1 - progress) * self.random_fraction()
                    t = current_time + (interval * self.random_fraction())
                    self.pulse_event_add(led, int(round(brightness * self.random_fraction())), t, pulse_length)

                    end_time = t + pulse_length
                    if end_time > last_time:
                        last_time = end_time

            current_time += interval

        for led in range(start_led, end_led + 1):
            self.brightness_set_event_add(led, 100, last_time + self.random_fraction() * 0.2)


# ---------------------------------------------------------------------------
# Sequence 5: Knight Rider
# ---------------------------------------------------------------------------

class SequenceKnightRider(Sequence):
    """
    Sequential sweep of a fade highlight back and forth across all 24 LEDs,
    looping indefinitely.

    Each LED fades up to full brightness then back to zero as the sweep
    passes through it. The stagger overlap creates a smooth trailing effect
    rather than a single hard point of light.

    Pre-generates 1000 sweeps (about 2.3 hours of content) at startup.
    This matches the C++ approach of pre-baking all events into the timeline.

    Button: 5
    C++ source: CSequenceKnightRider.cpp
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        num_leds = 24
        stagger = 0.2       # seconds between consecutive LED starts
        fade_time = 0.3     # seconds per fade up or down

        self.brightness_set_event_add_all_leds(0, 0.0)

        current_time = 0.01

        for _ in range(1000):
            for led in range(1, num_leds):
                self.fade_event_add(led, 100, current_time, fade_time)
                self.fade_event_add(led, 0, current_time + fade_time, fade_time)
                current_time += stagger

            for led in range(num_leds, 0, -1):
                self.fade_event_add(led, 100, current_time, fade_time)
                self.fade_event_add(led, 0, current_time + fade_time, fade_time)
                current_time += stagger

        self._length_seconds = current_time


# ---------------------------------------------------------------------------
# Registry -- add new sequences here
# ---------------------------------------------------------------------------

SEQUENCES: dict[str, type[Sequence]] = {
    "ambient": SequenceAmbient,
    "fadeout": SequenceFadeOutSimple,
    "heartbeat": SequenceHeartBeat,
    "sparkle": SequenceFadeInSparkle,
    "knightrider": SequenceKnightRider,
}

BUTTON_MAP: dict[int, str] = {
    1: "ambient",
    2: "fadeout",
    3: "heartbeat",
    4: "sparkle",
    5: "knightrider",
}
