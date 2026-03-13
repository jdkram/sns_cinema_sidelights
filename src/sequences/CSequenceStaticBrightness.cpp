// human-contributors: Jonny Kram; ai-contributors: [Claude Opus 4.6]; status: "#ai-written"
#include "CSequenceStaticBrightness.h"

CSequenceStaticBrightness::CSequenceStaticBrightness(CLEDManager *pLEDManager, int pBrightness) :
        CSequence(pLEDManager) {

    brightnessSetEventAddAllLeds(pBrightness, 0.0f);
}
