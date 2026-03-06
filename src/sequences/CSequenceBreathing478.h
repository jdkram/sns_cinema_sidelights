#ifndef CSEQUENCEBREATHING478_H
#define CSEQUENCEBREATHING478_H
// author: Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"

#include "CSequence.h"
#include "../CLEDManager.h"

// Guided 4-7-8 breathing sequence.
//
// Inhale 4 s: LEDs fill from the outer edges toward the centre
//             (left panel 1–12 left→right, right panel 24–13 right→left, interleaved).
// Hold   7 s: all LEDs hold at peak brightness.
// Exhale 8 s: LEDs empty from the centre outward.
// Rest   1 s: brief dark pause before the next breath.
//
// Physical assumption: LEDs 1–12 = left sidelight (outer = 1),
//                      LEDs 13–24 = right sidelight (outer = 24).
//
// Python source: simulator/sequences.py :: SequenceBreathing478
class CSequenceBreathing478 : public CSequence {

public:
    CSequenceBreathing478(CLEDManager* pLEDManager);

private:
    static const int   PEAK            = 70;
    static const int   BASE            = 0;
    static constexpr float INHALE          = 4.0f;
    static constexpr float HOLD            = 7.0f;
    static constexpr float EXHALE          = 8.0f;
    static constexpr float REST            = 1.0f;
    static constexpr float INHALE_FADE     = 2.5f;  // each LED's fade duration during inhale
    static constexpr float INHALE_STAGGER  = 0.05f; // gap between consecutive LED starts
    static constexpr float EXHALE_FADE     = 4.0f;
    static constexpr float EXHALE_STAGGER  = 0.08f;
};

#endif
