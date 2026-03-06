// author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
#include "CSequenceEmber.h"

#include <cstdlib>

// Port of simulator/sequences.py :: SequenceEmber
//
// Each LED independently fades to a random brightness at a random pace,
// starting at a random offset so no two LEDs are synchronised from the first
// frame. rand() is seeded in main.cpp with srand(time(0)) before construction,
// so each run produces a different pattern.
CSequenceEmber::CSequenceEmber(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true, TOTAL_SECONDS) {

    const float fade_range = MAX_FADE - MIN_FADE;
    const int brightness_range = MAX_BRIGHTNESS - MIN_BRIGHTNESS;

    for (int led = 1; led <= 24; led++) {

        // Stagger the first event so LEDs start out of phase.
        float t = ((float)rand() / (float)RAND_MAX) * MAX_FADE;

        while (t < TOTAL_SECONDS) {
            int brightness = MIN_BRIGHTNESS + (rand() % (brightness_range + 1));
            float fade_time = MIN_FADE + ((float)rand() / (float)RAND_MAX) * fade_range;
            fadeEventAdd(led, brightness, t, fade_time);
            t += fade_time;
        }
    }
}
