#include "CSequenceHeartBeat.h"

// void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
// void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
// void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);

CSequenceHeartBeat::CSequenceHeartBeat(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true) { // loop every 5 seconds

    float currentTime = 0.0f;

    const float INTERVAL = 2.0f;

    const float PULSE_1_UP_LENGTH = 0.1f;
    const float PULSE_1_DOWN_LENGTH = 0.1f;
    const int PULSE_1_BRIGHTNESS = 100;
    const float PULSE_2_UP_LENGTH = 0.2f;
    const float PULSE_2_DOWN_LENGTH = 0.2f;
    const int PULSE_2_BRIGHTNESS = 50;

    const float GAP_BETWEEN_PULSES = 0.25f;

    fadeEventAddAllLeds(PULSE_1_BRIGHTNESS, currentTime, PULSE_1_UP_LENGTH);

    currentTime += PULSE_1_UP_LENGTH;

    fadeEventAddAllLeds(0, currentTime, PULSE_1_DOWN_LENGTH);

    currentTime += PULSE_1_DOWN_LENGTH + GAP_BETWEEN_PULSES;

    fadeEventAddAllLeds(PULSE_2_BRIGHTNESS, currentTime, PULSE_2_UP_LENGTH);

    currentTime += PULSE_2_UP_LENGTH;

    fadeEventAddAllLeds(0, currentTime, PULSE_2_DOWN_LENGTH);

    currentTime += PULSE_2_DOWN_LENGTH + INTERVAL;

    mSequenceLengthSeconds = currentTime;
}
