#include "CSequenceFadeInSparkle.h"

#include <cstdlib>
#include <iostream>

#include <math.h>

using namespace std;

// void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
// void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
// void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);

CSequenceFadeInSparkle::CSequenceFadeInSparkle(CLEDManager *pLEDManager) :
        CSequence(pLEDManager) { // loop every 5 seconds

    const float PULSE_LENGTH_MAX = 0.5f;
    const float DURATION_SECONDS = 60.0f;
    const float START_INTERVAL = 1.0f;
    const float FINISH_INTERVAL = 0.001f;

    const int START_LED = 1;
    const int END_LED = 24;

    float currentTime = 0.0f;
    float lastTime = 0.0f;

    brightnessSetEventAddAllLeds(0, 0);

    while (currentTime < DURATION_SECONDS) {

        float progress = currentTime / DURATION_SECONDS;
        float brightness = progress * 100.0f;
        float intervalRange = FINISH_INTERVAL - START_INTERVAL;
        float interval = START_INTERVAL + (progress * intervalRange);

        for (int led = START_LED; led <= END_LED; led++) {

            if (randomFraction() < .5) {

                float pulseLength = PULSE_LENGTH_MAX * (1-progress) * randomFraction(); // pulses get shorter
                float time = currentTime + (interval * randomFraction());
                pulseEventAdd(led, (int) roundf(brightness * randomFraction()), time, pulseLength);

                float endTime = time + pulseLength;

                if(endTime > lastTime){

                    lastTime = endTime;
                }
            }
        }

        currentTime += interval;
    }

    for (int led = START_LED; led <= END_LED; led++) {

        brightnessSetEventAdd(led, 100, lastTime + randomFraction() * 0.2);
    }
}

float CSequenceFadeInSparkle::randomFraction(){
    return (float) rand() / (float) RAND_MAX;
}