#ifndef CSEQUENCESTATICBRIGHTNESS_H
#define CSEQUENCESTATICBRIGHTNESS_H
// human-contributors: Jonny Kram; ai-contributors: [Claude Opus 4.6]; status: "#ai-written"

#include "CSequence.h"
#include "../CLEDManager.h"

// Sets all 24 LEDs to a fixed brightness and holds. Useful as a "house lights"
// mode or for quick visual confirmation that the hardware works at a given level.
class CSequenceStaticBrightness : public CSequence {

public:
    CSequenceStaticBrightness(CLEDManager* pLEDManager, int pBrightness);
};

#endif
