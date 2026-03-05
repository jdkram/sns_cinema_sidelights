#ifndef ARDUINO_CSEQUENCE_H
#define ARDUINO_CSEQUENCE_H

#include <vector>
#include <chrono>

#include "../CLEDManager.h"
#include "../events/CEvent.h"

using namespace std::chrono;

class CSequence {

public:

    CSequence(CLEDManager *pLEDManager, bool pLoop = false, float pLengthSeconds = 0.0f);
    virtual ~CSequence();

    void start();

    void update();

    void ledBrightnessSet(CEvent *pEvent, int pLED, int pBrightness);
    float ledBrightnessGet(int pLED);
    void channelReserve(CEvent *pEvent, int pLED);

protected:

    void fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength);
    void fadeEventAddAllLeds(int pBrightness, float pStartTime, float pLength);
    void brightnessSetEventAdd(int pLED, int pBrightness, float pTime);
    void brightnessSetEventAddAllLeds(int pBrightness, float pTime);
    void pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength);
    void pulseEventAddAllLeds(int pBrightness, float pTime, float pLength);

    float mSequenceLengthSeconds;

private:

    milliseconds millis();

    void eventAdd(CEvent *pEvent);

    CLEDManager *mLEDManager;
    bool mLoopSequence;
    milliseconds mStartTime;

    std::vector<CEvent *> mEvents;
    std::vector<CEvent *> mReservedChannels;
};

#endif
