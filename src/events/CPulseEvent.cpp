// author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
#include "CPulseEvent.h"

#include <iostream>

#include "../sequences/CSequence.h"

using namespace std;

CPulseEvent::CPulseEvent(CSequence* pSequence, int pLED, int pBrightness, float pStartTimeSeconds, float pLength) :
CEvent(pSequence, pLED, pBrightness, pStartTimeSeconds, pLength), mFinished(false) {}

void CPulseEvent::reset(){

  mFinished = false;

  CEvent::reset();
}

void CPulseEvent::update(float pElapsedSequenceTime){

  if(mFinished){
    return;
  }

  if(!mTriggered && pElapsedSequenceTime > mStartTime){

    mSequence->channelReserve(this, mLED);
    mSequence->ledBrightnessSet(this, mLED, mTargetBrightness);
    mTriggered = true;

//    cout << "PULSE on " << mLED << " at " << pElapsedSequenceTime << "ms with brightness " << mTargetBrightness << endl;
  }
  else if(mTriggered && pElapsedSequenceTime > mEndTime){
    mSequence->ledBrightnessSet(this, mLED, 0);
    mFinished = true;
  }
}
