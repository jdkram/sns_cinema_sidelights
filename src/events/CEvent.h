#ifndef ARDUINO_CEVENT_H
#define ARDUINO_CEVENT_H

#include "../CLEDManager.h"
//#include "../sequences/CSequence.h"

class CSequence;

class CEvent{

    public:
      CEvent(CSequence* pSequence, int pLED, int pBrightness, float pStartTimeSeconds, float pLength = 0.0f);

      virtual void update(float pElapsedSequenceTime) = 0;
      virtual void reset();

    protected:
        CSequence* mSequence;
      int mLED;
      int mTargetBrightness;
      float mStartTime;
      float mEndTime;
      bool mTriggered;
};

#endif //ARDUINO_CEVENTMANAGER_H
