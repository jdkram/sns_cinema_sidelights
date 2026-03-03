#include "CSequenceManager.h"

#include <iostream>

#include "sequences/CSequenceHeartBeat.h"
#include "sequences/CSequenceFadeInSparkle.h"
#include "sequences/CSequenceFadeOutSimple.h"
#include "sequences/CSequenceAmbient.h"
#include "sequences/CSequenceKnightRider.h"

using namespace std;

CSequenceManager::CSequenceManager(CLEDManager* pLEDManager) : mCurrentSequence(nullptr){

    mSequences.push_back(new CSequenceAmbient(pLEDManager));
    mSequences.push_back(new CSequenceFadeOutSimple(pLEDManager));
    mSequences.push_back(new CSequenceHeartBeat(pLEDManager));
    mSequences.push_back(new CSequenceFadeInSparkle(pLEDManager));
    mSequences.push_back(new CSequenceKnightRider(pLEDManager));
}

void CSequenceManager::sequenceStart(int pSequenceIndex){

    cout << "Starting sequence" << endl;

    int sequenceIndex = pSequenceIndex - 1; // take away 1 to match number on button box

    if(sequenceIndex < mSequences.size()){

        mCurrentSequence = mSequences[sequenceIndex];

        mCurrentSequence->start();
    }
}

void CSequenceManager::update(){

  if(mCurrentSequence){
      mCurrentSequence->update();
  }
}
