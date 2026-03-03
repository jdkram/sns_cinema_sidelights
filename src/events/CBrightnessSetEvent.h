#include "CEvent.h"

//#include "../sequences/CSequence.h"

class CSequence;

class CBrightnessSetEvent : public CEvent {

public:
    CBrightnessSetEvent(CSequence *pSequence, int pLED, int pBrightness, float pStartTimeSeconds);

    void update(float pElapsedSequenceTime);
};