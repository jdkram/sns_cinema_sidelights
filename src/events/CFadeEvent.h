#include "CEvent.h"

//#include "../sequences/CSequence.h"

#include "../CLEDManager.h"

class CSequence;

class CFadeEvent : public CEvent{

  public:
      CFadeEvent(CSequence* pSequence, int pLED, int pBrightness, float pStartTimeSeconds, float pLength);
      void update(float pElapsedSequenceTime);
      void reset();
  private:
      float mInitialBrightness;
    bool mFinished;
};
