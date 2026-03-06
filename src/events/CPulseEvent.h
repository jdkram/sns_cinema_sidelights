// author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
#include "CEvent.h"

//#include "../sequences/CSequence.h"

class CSequence;

class CPulseEvent : public CEvent {

public:

    CPulseEvent(CSequence *pSequence, int pLED, int pBrightness, float pStartTimeSeconds,
                float pLength);

    void update(float pElapsedSequenceTime);

    void reset();

private:
    bool mFinished;
};
