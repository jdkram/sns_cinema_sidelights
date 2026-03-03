#include "CSequenceFadeOutSimple.h"

// void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
// void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
// void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);

CSequenceFadeOutSimple::CSequenceFadeOutSimple(CLEDManager *pLEDManager) :
        CSequence(pLEDManager) { // loop every 5 seconds

    const float FADE_TIME_SECONDS = 10.0f;

    fadeEventAddAllLeds(0, 0, FADE_TIME_SECONDS);
}
