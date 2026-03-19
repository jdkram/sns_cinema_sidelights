#ifndef CSEQUENCETESTSINGLE_H
#define CSEQUENCETESTSINGLE_H
// Diagnostic sequence: sets ONE LED to 100% via the event engine and holds.
// Use to confirm whether the event engine can drive individual channels.
// Callable via: ./main 12
// If LED 5 lights up: event engine works for single-channel writes.
// If nothing lights up: the event engine is broken for sparse writes (see session 005 notes).

#include "CSequence.h"
#include "../CLEDManager.h"

class CSequenceTestSingle : public CSequence {

public:
    CSequenceTestSingle(CLEDManager* pLEDManager);
};

#endif
