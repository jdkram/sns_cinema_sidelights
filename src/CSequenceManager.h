#include "sequences/CSequence.h"
#include <vector>
#include "CLEDManager.h"
// author: Paul?

class CSequenceManager{

  public:
    CSequenceManager(CLEDManager* pLEDManager);

    void update();
    void sequenceStart(int pSequenceIndex);
    void sequenceAdd(CSequence* pSequnce);
  private:
    CSequence* mCurrentSequence;
    std::vector<CSequence*> mSequences;
};
