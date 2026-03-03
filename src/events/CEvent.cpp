#include "CEvent.h"

CEvent::CEvent(CSequence *pSequence, int pLED, int pBrightness, float pStartTimeSeconds, float pLength) :
        mSequence(pSequence),
        mLED(pLED),
        mTargetBrightness(pBrightness),
        mStartTime(pStartTimeSeconds * 1000.0f),
        mEndTime((pStartTimeSeconds + pLength) * 1000.0f),
        mTriggered(false) {};

void CEvent::reset() {

    mTriggered = false;
}
