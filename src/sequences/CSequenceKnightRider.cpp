#include "CSequenceKnightRider.h"

#include <cstdlib>
#include <iostream>

using namespace std;

//void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
//void fadeEventAddAllLeds(int pBrightness, float pStartTime, float pLength);
//void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
//void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);
//void pulseEventAddAllLeds(int pBrightness, float pTime, float pLength);

CSequenceKnightRider::CSequenceKnightRider(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true) { // looping sequence

//    cout << "--- Creating KnightRider Sequence ---" << endl;

    brightnessSetEventAddAllLeds(0, 0);

    const int LEDS = 24;
    const float STAGGER = 0.2f;
    const float FADE_TIME = 0.3f;

    float currentTime = 0.01f;

    // A single sweep (one pass forward, one pass back). mLoopSequence = true handles
    // repetition automatically. Previously 1000 iterations pre-baked ~94,000 events
    // for a 2.6-hour sequence, forcing every update() frame to iterate all of them
    // even though only ~4 are ever active -- this pegged the Pi Zero CPU continuously.
    
    for (int led = 1; led < LEDS; led++) {

        fadeEventAdd(led, 100, currentTime, FADE_TIME);
        fadeEventAdd(led, 0, currentTime + FADE_TIME, FADE_TIME);

        currentTime += STAGGER; // next one overlaps
    }

    for (int led = LEDS; led >= 1; led--) {

        fadeEventAdd(led, 100, currentTime, FADE_TIME);
        fadeEventAdd(led, 0, currentTime + FADE_TIME, FADE_TIME);

        currentTime += STAGGER; // next one overlaps
    }

    mSequenceLengthSeconds = currentTime;
    cout << "KnightRider sequence length: " << mSequenceLengthSeconds << "s" << endl;
}
