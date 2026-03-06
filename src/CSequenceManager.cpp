// author: Paul?
#include "CSequenceManager.h"

#include <iostream>

#include "sequences/CSequenceHeartBeat.h"
#include "sequences/CSequenceFadeInSparkle.h"
#include "sequences/CSequenceFadeOutSimple.h"
#include "sequences/CSequenceAmbient.h"
#include "sequences/CSequenceKnightRider.h"
#include "sequences/CSequenceEmber.h"
#include "sequences/CSequenceBreathing478.h"

using namespace std;

// Sequence slot assignments (1-based, matches sequenceStart() calls and CLI arg):
//   1 = Ambient        4 = FadeInSparkle
//   2 = FadeOutSimple  5 = KnightRider
//   3 = HeartBeat      6 = Ember          7 = Breathing478
// To add or reorder: push_back in the order you want and update main.cpp's SEQUENCE_NAMES.
CSequenceManager::CSequenceManager(CLEDManager* pLEDManager) : mCurrentSequence(nullptr){

    mSequences.push_back(new CSequenceAmbient(pLEDManager));       // 1
    mSequences.push_back(new CSequenceFadeOutSimple(pLEDManager)); // 2
    mSequences.push_back(new CSequenceHeartBeat(pLEDManager));     // 3
    mSequences.push_back(new CSequenceFadeInSparkle(pLEDManager)); // 4
    mSequences.push_back(new CSequenceKnightRider(pLEDManager));   // 5
    mSequences.push_back(new CSequenceEmber(pLEDManager));         // 6
    mSequences.push_back(new CSequenceBreathing478(pLEDManager));  // 7
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
