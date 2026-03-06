// ai-input
#ifndef CSEQUENCEEMBER_H
#define CSEQUENCEEMBER_H

#include "CSequence.h"
#include "../CLEDManager.h"

// Each LED drifts independently through a narrow low-brightness range on
// its own slow random schedule. Generates 10 minutes of unique content before looping.
// Python source: simulator/sequences.py :: SequenceEmber
class CSequenceEmber : public CSequence {

public:
    CSequenceEmber(CLEDManager* pLEDManager);

private:
    static const int   MIN_BRIGHTNESS = 12;
    static const int   MAX_BRIGHTNESS = 55;
    static constexpr float MIN_FADE        = 3.0f;  // seconds, shortest LED transition
    static constexpr float MAX_FADE        = 8.0f;  // seconds, longest LED transition
    static constexpr float TOTAL_SECONDS   = 600.0f; // 10 minutes before loop
};

#endif
