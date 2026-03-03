#include "CBrightnessSetEvent.h"

#include <iostream>

#include "../sequences/CSequence.h"

using namespace std;

CBrightnessSetEvent::CBrightnessSetEvent(CSequence* pSequence, int pLED, int pBrightness, float pStartTimeSeconds) :
CEvent(pSequence, pLED, pBrightness, pStartTimeSeconds) {}

void CBrightnessSetEvent::update(float pElapsedSequenceTime){

  if(!mTriggered && pElapsedSequenceTime > mStartTime){

    mSequence->channelReserve(this, mLED);
    mSequence->ledBrightnessSet(this, mLED, mTargetBrightness);
    mTriggered = true;

//    cout << "BRIGHTNESS_SET on " << mLED << " at " << pElapsedSequenceTime << "ms with brightness " << mTargetBrightness << endl;
  }
}
