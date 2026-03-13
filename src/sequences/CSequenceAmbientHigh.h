#ifndef CSEQUENCEAMBIENTHIGH_H
#define CSEQUENCEAMBIENTHIGH_H
// human-contributors: Jonny Kram; ai-contributors: [Claude Opus 4.6]; status: "#ai-written"

#include "CSequence.h"
#include "../CLEDManager.h"

// Ambient with a raised brightness floor. Identical to CSequenceAmbient but
// MIN_BRIGHTNESS is 55% instead of 5%, keeping all values well above the
// suspected hardware visibility threshold. If the original Ambient shows
// lights winking on and off, this version should show smooth continuous
// variation -- confirming the threshold theory.
class CSequenceAmbientHigh : public CSequence {

public:
    CSequenceAmbientHigh(CLEDManager* pLEDManager);
};

#endif
