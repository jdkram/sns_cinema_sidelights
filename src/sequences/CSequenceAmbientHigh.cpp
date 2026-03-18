// human-contributors: Jonny Kram; ai-contributors: [Claude Opus 4.6]; status: "#ai-written"
#include "CSequenceAmbientHigh.h"

#include <cstdlib>

#define FADE_TIME 2
#define LOOPS 100

#define SEQUENCE_LENGTH LOOPS * FADE_TIME

CSequenceAmbientHigh::CSequenceAmbientHigh(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true, SEQUENCE_LENGTH) {

    const int LEDS = 24;
    const int MIN_BRIGHTNESS = 30;
    const int MAX_BRIGHTNESS = 100;

    float currentTime = 0.0f;

    for(int loop = 0; loop < LOOPS; loop++){

        for(int led = 1; led <= LEDS; led++){

            int randomBrightness = MIN_BRIGHTNESS + rand() % (MAX_BRIGHTNESS + 1 - MIN_BRIGHTNESS);

            fadeEventAdd(led, randomBrightness, currentTime, FADE_TIME);
        }

        currentTime += FADE_TIME;
    }
}
