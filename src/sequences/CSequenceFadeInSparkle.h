#include "CSequence.h"
#include "../CLEDManager.h"

class CSequenceFadeInSparkle : public CSequence {

public:
    CSequenceFadeInSparkle(CLEDManager *pLEDManager);

private:
    float randomFraction();
};
