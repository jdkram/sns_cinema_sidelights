#include "CSequence.h"

#include <iostream>
#include <chrono>
#include <random>

#include "../events/CFadeEvent.h"
#include "../events/CBrightnessSetEvent.h"
#include "../events/CPulseEvent.h"

#define NUMBER_OF_PINS 24

using namespace std;
using namespace std::chrono;

CSequence::CSequence(CLEDManager *pLEDManager, bool pLoop, float pLengthSeconds) :
        mSequenceLengthSeconds(pLengthSeconds),
        mLEDManager(pLEDManager),
        mLoopSequence(pLoop),
        mStartTime(0) {

    for (int i = 0; i < NUMBER_OF_PINS; i++) {
        mReservedChannels.push_back(nullptr);
    }
}

CSequence::~CSequence() {
    for (vector<CEvent *>::iterator it = mEvents.begin(); it != mEvents.end(); ++it) {
        delete *it;
    }
    mEvents.clear();
}

void CSequence::channelReserve(CEvent *pEvent, int pLED) {

    // Events reserve a channel when they begin. Later events can then override this and we only
    // allow the latest event to set the brightness. See ledBrightnessSet.

    if (pLED - 1 < mReservedChannels.size()) {

        mReservedChannels[pLED - 1] = pEvent;
    }
}

void CSequence::ledBrightnessSet(CEvent *pEvent, int pLED, int pBrightness) {

    if (pLED - 1 < mReservedChannels.size()) {

        if (mReservedChannels[pLED - 1] && pEvent == mReservedChannels[pLED - 1]) {

            mLEDManager->ledBrightnessSet(pLED, pBrightness);
        }
    }
}

float CSequence::ledBrightnessGet(int pLED) {

    return mLEDManager->ledBrightnessGet(pLED);
}

void CSequence::fadeEventAdd(int pLED, int pBrightness, float pStartTime, float pLength) {

//    cout << "Adding Fade Event - LED: " << pLED << ", Time: " << pStartTime << ", Brightness: " << pBrightness << endl;

    eventAdd(new CFadeEvent(this, pLED, pBrightness, pStartTime, pLength));
}

void CSequence::fadeEventAddAllLeds(int pBrightness, float pStartTime, float pLength) {

    for (int i = 1; i <= 24; i++) {
        fadeEventAdd(i, pBrightness, pStartTime, pLength);
    }
}

void CSequence::brightnessSetEventAdd(int pLED, int pBrightness, float pTime) {

    eventAdd(new CBrightnessSetEvent(this, pLED, pBrightness, pTime));
}

void CSequence::brightnessSetEventAddAllLeds(int pBrightness, float pTime) {

    for (int i = 1; i <= 24; i++) {
        brightnessSetEventAdd(i, pBrightness, pTime);
    }
}

void CSequence::pulseEventAdd(int pLED, int pBrightness, float pTime, float pLength) {

    eventAdd(new CPulseEvent(this, pLED, pBrightness, pTime, pLength));
}

void CSequence::pulseEventAddAllLeds(int pBrightness, float pTime, float pLength) {

    for (int i = 1; i <= 24; i++) {
        pulseEventAdd(i, pBrightness, pTime, pLength);
    }
}

void CSequence::eventAdd(CEvent *pEvent) {

    mEvents.push_back(pEvent);
}

void CSequence::start() {

    for (vector<CEvent *>::iterator it = mEvents.begin(); it != mEvents.end(); ++it) {

        CEvent *event = *it;

        event->reset();
    }

    mStartTime = millis();
}

milliseconds CSequence::millis() {

    // steady_clock is monotonic and unaffected by NTP adjustments.
    // system_clock can jump forward or backward when NTP corrects the Pi's clock
    // after boot (the Zero has no RTC), which would corrupt elapsed-time calculations.
    milliseconds ms = duration_cast<milliseconds>(steady_clock::now().time_since_epoch());

    return ms;
}

void CSequence::update() {

    milliseconds elapsedTime = millis() - mStartTime;

    float elapsedTimeFloat = (float) elapsedTime.count();

//    milliseconds frameStart = millis();

    for (vector<CEvent *>::iterator it = mEvents.begin(); it != mEvents.end(); ++it) {

        CEvent *event = *it;

        event->update(elapsedTimeFloat);
    }

//    milliseconds frameLength = millis() - frameStart;

//    if(frameLength.count() > 20){
//
//        cout << "Frame Length: " << frameLength.count() << endl;
//    }

    float sequenceLengthMs = mSequenceLengthSeconds * 1000.0f;

    if (mLoopSequence && elapsedTimeFloat > sequenceLengthMs) {
        cout << "Looping" << endl;
        start();
    }
}
