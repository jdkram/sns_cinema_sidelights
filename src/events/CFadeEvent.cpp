#include "CFadeEvent.h"

#include <iostream>

#include "../sequences/CSequence.h"

using namespace std;

CFadeEvent::CFadeEvent(CSequence* pSequence, int pLED, int pBrightness, float pStartTimeSeconds, float pLength) :
        CEvent(pSequence, pLED, pBrightness, pStartTimeSeconds, pLength),
        mInitialBrightness(0),
        mFinished(false) {
}

void CFadeEvent::reset() {

    mInitialBrightness = 0;
    mFinished = false;

    CEvent::reset();
}

void CFadeEvent::update(float pElapsedSequenceTime) {

    // This seems more complicated than you might expect just to fade, but we
    // need to fade from whatever the brightness was initially so there can be a
    // smoother transition between sequences. The alternative would have been just
    // to set all lights off at the beginning of every sequence which could be somewhat jarring.

    // Note mEndTime < and not <= to prevent overlap of events starting immediately after fade
    if (pElapsedSequenceTime >= mStartTime && pElapsedSequenceTime < mEndTime) {

        if (!mTriggered) {
            mInitialBrightness = mSequence->ledBrightnessGet(mLED);
            mSequence->channelReserve(this, mLED);
            cout << "CFadeEvent trigger: LED=" << mLED
                 << " from=" << mInitialBrightness
                 << " to=" << mTargetBrightness
                 << " at=" << pElapsedSequenceTime << "ms" << endl;
            mTriggered = true;
        }

        float brightnessDiff = mTargetBrightness - mInitialBrightness;
        float timeDiff = mEndTime - mStartTime;

        float changePerMs = brightnessDiff / timeDiff;
        float eventTimeElapsed = pElapsedSequenceTime - mStartTime;

        float totalChange = changePerMs * eventTimeElapsed;

        float newBrightness = mInitialBrightness + totalChange;

        // floatPrint("brightnessDiff", brightnessDiff);
        // floatPrint("timeDiff", timeDiff);
        // floatPrint("changePerMs", changePerMs);
        // floatPrint("eventTimeElapsed", eventTimeElapsed);
        // floatPrint("totalChange", totalChange);
        // floatPrint("newBrightness", newBrightness);
        // floatPrint("pElapsedTime", pElapsedSequenceTime);

        mSequence->ledBrightnessSet(this, mLED, newBrightness);
    }

    if(pElapsedSequenceTime > mEndTime){

        if(!mFinished){

//            cout << "Fade finished: " << " LED: " << mLED << " Brightness: " << mSequence->ledBrightnessGet(mLED) << endl;
            mFinished = true;
            mSequence->ledBrightnessSet(this, mLED, mTargetBrightness);
        }
    }
}