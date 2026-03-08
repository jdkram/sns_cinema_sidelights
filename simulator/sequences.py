# author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
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
# Sequence 6: breathing
# ---------------------------------------------------------------------------

class SequenceBreathing(Sequence):
    """
    All 24 LEDs rise and fall together in a slow, regular breath.

    The exhale (FALL) is deliberately longer than the inhale (RISE), and the
    rest at low brightness gives the cycle a settled, unhurried quality.
    A full breath takes about 14 seconds.

    Button: 6
    """

    PEAK = 60       # brightness at top of inhale
    BASE = 8        # resting brightness between breaths
    RISE = 4.0      # seconds to inhale
    HOLD_HIGH = 1.5 # seconds to hold at peak
    FALL = 5.5      # seconds to exhale
    REST = 3.0      # seconds to rest before the next breath

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        self.fade_event_add_all_leds(self.PEAK, 0.0, self.RISE)
        t = self.RISE + self.HOLD_HIGH
        self.fade_event_add_all_leds(self.BASE, t, self.FALL)

        self._length_seconds = t + self.FALL + self.REST


# ---------------------------------------------------------------------------
# Sequence 7: drift
# ---------------------------------------------------------------------------

class SequenceDrift(Sequence):
    """
    A slow wave of light sweeps across all 24 LEDs, then leaves them dark
    for a long rest before the next pass.

    Each LED fades up as the wave front reaches it, then fades back to zero.
    The stagger between consecutive LEDs (STAGGER seconds) determines wave
    speed. One full pass takes about 16 seconds; the cycle including the rest
    is about 23 seconds.

    Button: 7
    """

    STAGGER = 0.45      # seconds between each consecutive LED's fade start
    RISE_TIME = 2.5     # seconds for each LED to reach peak
    FALL_TIME = 3.5     # seconds for each LED to fade out
    PEAK = 55
    GAP = 7.0           # dark pause after the last LED finishes

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        self.brightness_set_event_add_all_leds(0, 0.0)

        for i in range(24):
            t_up = 0.01 + i * self.STAGGER
            t_down = t_up + self.RISE_TIME
            self.fade_event_add(i + 1, self.PEAK, t_up, self.RISE_TIME)
            self.fade_event_add(i + 1, 0, t_down, self.FALL_TIME)

        last_fall_end = 0.01 + 23 * self.STAGGER + self.RISE_TIME + self.FALL_TIME
        self._length_seconds = last_fall_end + self.GAP


# ---------------------------------------------------------------------------
# Sequence 8: ember
# ---------------------------------------------------------------------------

class SequenceEmber(Sequence):
    """
    Each LED drifts independently through a narrow low-brightness range on
    its own slow, random schedule. No two LEDs are ever in sync.

    The effect is like dying embers or very distant, gentle firelight:
    organic, unhurried, and quiet. Generates 10 minutes of unique content
    before looping.

    Button: 8
    """

    MIN_BRIGHTNESS = 12
    MAX_BRIGHTNESS = 55
    MIN_FADE = 3.0      # seconds, shortest LED transition
    MAX_FADE = 8.0      # seconds, longest LED transition
    TOTAL_SECONDS = 600.0

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True, length_seconds=self.TOTAL_SECONDS)

        fade_range = self.MAX_FADE - self.MIN_FADE

        for led in range(1, 25):
            # Stagger each LED's start so they're out of phase from the first frame.
            t = self.random_fraction() * self.MAX_FADE
            while t < self.TOTAL_SECONDS:
                brightness = random.randint(self.MIN_BRIGHTNESS, self.MAX_BRIGHTNESS)
                fade_time = self.MIN_FADE + self.random_fraction() * fade_range
                self.fade_event_add(led, brightness, t, fade_time)
                t += fade_time


# ---------------------------------------------------------------------------
# Sequence 9: 4-7-8 breathing
# ---------------------------------------------------------------------------

class SequenceBreathing478(Sequence):
    """
    Guided 4-7-8 breathing sequence.

    Phases:
        Inhale   4 s  LEDs fill from the outer edges toward the centre,
                      like two lungs expanding together.
        Hold     7 s  All LEDs glow steadily at peak brightness.
        Exhale   8 s  LEDs empty from the centre outward.
        Rest     1 s  Brief dark pause before the next breath.

    Assumes LEDs 1-12 are the left sidelight (outer = LED 1) and LEDs
    13-24 are the right sidelight (outer = LED 24). If the physical layout
    differs, reorder inhale_order.

    Button: 9
    """

    PEAK = 70
    BASE = 0

    INHALE = 4.0
    HOLD = 7.0
    EXHALE = 8.0
    REST = 1.0

    INHALE_FADE = 2.5   # each LED's individual fade duration during inhale
    INHALE_STAGGER = 0.05   # gap between consecutive LEDs' fade starts

    EXHALE_FADE = 4.0
    EXHALE_STAGGER = 0.08

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        self.brightness_set_event_add_all_leds(self.BASE, 0.0)

        # Fill order: outer edges to centre (left lung left→right, right lung right→left)
        left_in = list(range(1, 13))         # 1 … 12
        right_in = list(range(24, 12, -1))   # 24 … 13
        inhale_order = [led for pair in zip(left_in, right_in) for led in pair]
        exhale_order = list(reversed(inhale_order))  # centre outward

        for i, led in enumerate(inhale_order):
            self.fade_event_add(led, self.PEAK, 0.01 + i * self.INHALE_STAGGER, self.INHALE_FADE)

        t_exhale = self.INHALE + self.HOLD
        for i, led in enumerate(exhale_order):
            self.fade_event_add(led, self.BASE, t_exhale + i * self.EXHALE_STAGGER, self.EXHALE_FADE)

        self._length_seconds = self.INHALE + self.HOLD + self.EXHALE + self.REST


# ---------------------------------------------------------------------------
# Sequence 10: Projector
# ---------------------------------------------------------------------------

class SequenceProjector(Sequence):
    """
    Mimics the flickering light of a vintage film projector reflecting off
    the screen.

    Creates a nostalgic atmosphere using rapid, random brightness fluctuations
    typical of old film stock or shutter flicker.
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        current_time = 0.0
        # Generate 10 seconds of flicker loop
        while current_time < 10.0:
            # Random brightness between 20% and 80%
            brightness = 20 + self.random_fraction() * 60
            # Hold for a short random duration (frame/scene duration)
            duration = 0.05 + self.random_fraction() * 0.15

            self.brightness_set_event_add_all_leds(brightness, current_time)
            current_time += duration

        self._length_seconds = current_time


# ---------------------------------------------------------------------------
# Sequence 11: Sunrise
# ---------------------------------------------------------------------------

class SequenceSunrise(Sequence):
    """
    A slow, gentle brightening to wake the audience after a film.

    Starts from black and gradually fades up to full brightness over 2 minutes.
    Useful for post-credits or cleaning lighting.
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=False)

        # Start black
        self.brightness_set_event_add_all_leds(0, 0.0)

        # Phase 1: Very slow dawn (0% -> 20% over 60s)
        self.fade_event_add_all_leds(20, 0.1, 60.0)

        # Phase 2: Brightening (20% -> 100% over 60s)
        self.fade_event_add_all_leds(100, 60.1, 60.0)


# ---------------------------------------------------------------------------
# Sequence 12: Countdown
# ---------------------------------------------------------------------------

class SequenceCountdown(Sequence):
    """
    Visual countdown (5-4-3-2-1) for starting a film.

    Flashes all lights bright on the second, then fades them out, mimicking
    old film leader countdowns.
    """

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=False)

        current_time = 0.0

        # 5 seconds countdown
        for _ in range(5):
            # Flash on
            self.brightness_set_event_add_all_leds(100, current_time)
            # Fast fade out
            self.fade_event_add_all_leds(0, current_time + 0.1, 0.8)
            current_time += 1.0

        # Final flash at 0 (Go!)
        self.brightness_set_event_add_all_leds(100, current_time)
        self.fade_event_add_all_leds(0, current_time + 0.5, 2.0)


# ---------------------------------------------------------------------------
# Sequence 13: Block Tower
# ---------------------------------------------------------------------------

class SequenceBlockTower(Sequence):
    """
    Rows sweep in horizontally from top to bottom, stacking like floors.
    Once all rows are lit, columns clear one at a time left to right,
    like a building coming down floor by floor.

    Button: 13
    """
    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)
        num_cols = 6
        num_rows = 4
        leds_per_col = num_rows
        fill_time = 0.3   # seconds per row
        hold_time = 1.0   # pause at full before clearing
        clear_time = 0.4  # seconds per column
        current_time = 0.0

        # Fill rows horizontally (top to bottom)
        for row in range(num_rows):
            for col in range(num_cols):
                led = col * leds_per_col + row + 1
                self.brightness_set_event_add(led, 100, current_time)
            current_time += fill_time

        # Hold at full brightness
        current_time += hold_time

        # Clear columns vertically (left to right)
        for col in range(num_cols):
            for row in range(num_rows):
                led = col * leds_per_col + row + 1
                self.brightness_set_event_add(led, 0, current_time)
            current_time += clear_time

        self._length_seconds = current_time

# ---------------------------------------------------------------------------
# Sequence 14: Snake
# ---------------------------------------------------------------------------

class SequenceSnake(Sequence):
    """
    A single bright "snake" moves through the LEDs, wrapping at the end.
    The snake is 4 LEDs long and moves one step at a time.
    """
    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)
        num_leds = 24
        snake_length = 4
        step_time = 0.15
        current_time = 0.0
        for step in range(num_leds):
            # Turn all off
            for led in range(1, num_leds + 1):
                self.brightness_set_event_add(led, 0, current_time)
            # Turn on snake
            for i in range(snake_length):
                led = ((step + i) % num_leds) + 1
                self.brightness_set_event_add(led, 100, current_time)
            current_time += step_time
        self._length_seconds = current_time

# ---------------------------------------------------------------------------
# Sequence 15: Columns and Rows
# ---------------------------------------------------------------------------

class SequenceColumnsRows(Sequence):
    """
    Columns fill in from the sides, then rows drop in from the top.
    """
    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)
        num_cols = 6
        num_rows = 4
        leds_per_col = num_rows
        fill_time = 0.12
        current_time = 0.0
        # Columns in from sides (outer to centre)
        col_order = [0, 5, 1, 4, 2, 3]
        for col in col_order:
            for row in range(num_rows):
                led = col * leds_per_col + row + 1
                self.brightness_set_event_add(led, 100, current_time)
            current_time += fill_time
        # Clear
        for led in range(1, num_cols * num_rows + 1):
            self.brightness_set_event_add(led, 0, current_time)
        current_time += 0.3
        # Rows in from top
        for row in range(num_rows):
            for col in range(num_cols):
                led = col * leds_per_col + row + 1
                self.brightness_set_event_add(led, 100, current_time)
            current_time += fill_time
        # Clear
        for led in range(1, num_cols * num_rows + 1):
            self.brightness_set_event_add(led, 0, current_time)
        self._length_seconds = current_time


# ---------------------------------------------------------------------------
# Sequence 16: Dim On
# ---------------------------------------------------------------------------

class SequenceDimOn(Sequence):
    """
    All 24 LEDs held at a steady low brightness. No movement, no pulse.

    A simple "house lights at low" state. Useful as a holding pattern
    between films, or for anyone who finds the other sequences too distracting.

    Button: 16
    """

    BRIGHTNESS = 22  # percent -- warm and visible but not glaring

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=False)
        self.brightness_set_event_add_all_leds(self.BRIGHTNESS, 0.0)


# ---------------------------------------------------------------------------
# Sequence 17: Slow Glow
# ---------------------------------------------------------------------------

class SequenceSlowGlow(Sequence):
    """
    Extremely gentle, unhurried ambience. Each LED drifts independently
    through a very narrow low-brightness range on a long, slow schedule.

    For people who find the other sequences too flickery or distracting.
    Transitions take 10-25 seconds each -- almost imperceptible moment-to-moment,
    but alive over longer periods. Generates 10 minutes before looping.

    Button: 17
    """

    MIN_BRIGHTNESS = 8
    MAX_BRIGHTNESS = 22
    MIN_FADE = 10.0
    MAX_FADE = 25.0
    TOTAL_SECONDS = 600.0

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True, length_seconds=self.TOTAL_SECONDS)

        fade_range = self.MAX_FADE - self.MIN_FADE

        for led in range(1, 25):
            t = self.random_fraction() * self.MAX_FADE
            while t < self.TOTAL_SECONDS:
                brightness = random.randint(self.MIN_BRIGHTNESS, self.MAX_BRIGHTNESS)
                fade_time = self.MIN_FADE + self.random_fraction() * fade_range
                self.fade_event_add(led, brightness, t, fade_time)
                t += fade_time


# ---------------------------------------------------------------------------
# Sequence 18: Bass Wub
# ---------------------------------------------------------------------------

class SequenceBassWub(Sequence):
    """
    Simulates a musical build: rapid dim flashes at the start, gradually
    slowing and brightening into heavy, punchy flashes.

    Loosely models the shape of a club music drop -- quick stutters
    giving way to slow, weighty beats. Loops the full build every ~20 seconds.

    Button: 18
    """

    # (phase_duration_s, interval_s, brightness_pct, flash_hold_s)
    PHASES = [
        (4.0, 0.10, 22, 0.05),   # rapid dim stutter
        (3.0, 0.18, 38, 0.08),
        (3.0, 0.30, 55, 0.12),
        (3.0, 0.60, 72, 0.25),
        (3.0, 1.10, 88, 0.45),
        (4.0, 2.00, 100, 0.75),  # slow heavy thud
    ]

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True)

        self.brightness_set_event_add_all_leds(0, 0.0)
        current_time = 0.0

        for phase_duration, interval, brightness, flash_hold in self.PHASES:
            phase_end = current_time + phase_duration
            t = current_time
            while t < phase_end:
                self.brightness_set_event_add_all_leds(brightness, t)
                self.brightness_set_event_add_all_leds(0, t + flash_hold)
                t += interval
            current_time = phase_end

        self._length_seconds = current_time


# ---------------------------------------------------------------------------
# Sequence 19: Rave
# ---------------------------------------------------------------------------

class SequenceRave(Sequence):
    """
    Fast, sporadic individual LED flashing for loud/energetic music events.

    Random subsets of LEDs strobe independently at varying speeds.
    Short 4-second loop pre-baked at startup -- each run of the sequence
    plays the same loop, but it feels unpredictable in context.

    Button: 19
    """

    TOTAL_SECONDS = 4.0

    def __init__(self, led_manager: LEDManager) -> None:
        super().__init__(led_manager, loop=True, length_seconds=self.TOTAL_SECONDS)

        self.brightness_set_event_add_all_leds(0, 0.0)

        t = 0.01
        while t < self.TOTAL_SECONDS:
            num_on = random.randint(4, 14)
            leds_on = random.sample(range(1, 25), num_on)
            hold = 0.03 + self.random_fraction() * 0.07
            for led in leds_on:
                self.brightness_set_event_add(led, 100, t)
                self.brightness_set_event_add(led, 0, t + hold)
            t += 0.05 + self.random_fraction() * 0.09


# ---------------------------------------------------------------------------
# Registry -- add new sequences here
# ---------------------------------------------------------------------------

SEQUENCES: dict[str, type[Sequence]] = {
    "ambient": SequenceAmbient,
    "fadeout": SequenceFadeOutSimple,
    "heartbeat": SequenceHeartBeat,
    "sparkle": SequenceFadeInSparkle,
    "knightrider": SequenceKnightRider,
    "breathing": SequenceBreathing,
    "drift": SequenceDrift,
    "ember": SequenceEmber,
    "breathing478": SequenceBreathing478,
    "projector": SequenceProjector,
    "sunrise": SequenceSunrise,
    "countdown": SequenceCountdown,
    "blocktower": SequenceBlockTower,
    "snake": SequenceSnake,
    "columnsrows": SequenceColumnsRows,
    "dimon": SequenceDimOn,
    "slowglow": SequenceSlowGlow,
    "basswub": SequenceBassWub,
    "rave": SequenceRave,
}

BUTTON_MAP: dict[int, str] = {
    1: "ambient",
    2: "fadeout",
    3: "heartbeat",
    4: "sparkle",
    5: "knightrider",
    6: "breathing",
    7: "drift",
    8: "ember",
    9: "breathing478",
    10: "projector",
    11: "sunrise",
    12: "countdown",
    13: "blocktower",
    14: "snake",
    15: "columnsrows",
    16: "dimon",
    17: "slowglow",
    18: "basswub",
    19: "rave",
}
