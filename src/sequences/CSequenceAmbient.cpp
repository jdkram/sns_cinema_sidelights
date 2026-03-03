#include "CSequenceAmbient.h"

#include <cstdlib>
#include <iostream>

#define FADE_TIME 2
#define LOOPS 100

#define SEQUENCE_LENGTH LOOPS * FADE_TIME

using namespace std;

// void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
// void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
// void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);

CSequenceAmbient::CSequenceAmbient(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true, SEQUENCE_LENGTH) { // looping sequence

//    cout << "--- Creating Ambient Sequence ---" << endl;

    const int LEDS = 24;
    const int MIN_BRIGHTNESS = 5;
    const int MAX_BRIGHTNESS = 100;

    float currentTime = 0.0f;

    for(int loop = 0; loop < LOOPS; loop++){

        for(int led = 1; led <= LEDS; led++){

            int randomBrightness = MIN_BRIGHTNESS + rand() % (MAX_BRIGHTNESS + 1 - MIN_BRIGHTNESS); // 0 - 100

            fadeEventAdd(led, randomBrightness, currentTime, FADE_TIME);
        }

        currentTime += FADE_TIME;
    }
}
