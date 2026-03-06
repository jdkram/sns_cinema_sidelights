// ai-input
#include "CSequenceBreathing478.h"

// Port of simulator/sequences.py :: SequenceBreathing478
//
// inhale_order interleaves left panel (outer→centre: 1..12) with right panel
// (outer→centre: 24..13), producing [1,24, 2,23, 3,22, ... 12,13].
// exhale_order is the exact reverse: [13,12, 14,11, ... 24,1].
CSequenceBreathing478::CSequenceBreathing478(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, true, INHALE + HOLD + EXHALE + REST) {

    brightnessSetEventAddAllLeds(BASE, 0.0f);

    // Hard-coded orders match the Python zip/reverse logic exactly -- no runtime surprises.
    const int inhale_order[24] = {
         1, 24,  2, 23,  3, 22,  4, 21,
         5, 20,  6, 19,  7, 18,  8, 17,
         9, 16, 10, 15, 11, 14, 12, 13
    };
    const int exhale_order[24] = {
        13, 12, 14, 11, 15, 10, 16,  9,
        17,  8, 18,  7, 19,  6, 20,  5,
        21,  4, 22,  3, 23,  2, 24,  1
    };

    for (int i = 0; i < 24; i++) {
        fadeEventAdd(inhale_order[i], PEAK, 0.01f + i * INHALE_STAGGER, INHALE_FADE);
    }

    float t_exhale = INHALE + HOLD;
    for (int i = 0; i < 24; i++) {
        fadeEventAdd(exhale_order[i], BASE, t_exhale + i * EXHALE_STAGGER, EXHALE_FADE);
    }
}
