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
#include "sequences/CSequenceStaticBrightness.h"
#include "sequences/CSequenceAmbientHigh.h"
#include "sequences/CSequenceTestSingle.h"

using namespace std;

// Sequence slot assignments (1-based, matches sequenceStart() calls and CLI arg):
//   1 = Ambient          5 = KnightRider      9 = Static 50%
//   2 = FadeOutSimple     6 = Ember           10 = Static 75%
//   3 = HeartBeat         7 = Breathing478    11 = Static 100%
//   4 = FadeInSparkle     8 = AmbientHigh     12 = TestSingle (event engine diagnostic)
// To add or reorder: push_back in the order you want and update main.cpp's ENTRY_NAMES.
CSequenceManager::CSequenceManager(CLEDManager* pLEDManager) : mCurrentSequence(nullptr){

    mSequences.push_back(new CSequenceAmbient(pLEDManager));              //  1
    mSequences.push_back(new CSequenceFadeOutSimple(pLEDManager));        //  2
    mSequences.push_back(new CSequenceHeartBeat(pLEDManager));            //  3
    mSequences.push_back(new CSequenceFadeInSparkle(pLEDManager));        //  4
    mSequences.push_back(new CSequenceKnightRider(pLEDManager));          //  5
    mSequences.push_back(new CSequenceEmber(pLEDManager));                //  6
    mSequences.push_back(new CSequenceBreathing478(pLEDManager));         //  7
    mSequences.push_back(new CSequenceAmbientHigh(pLEDManager));          //  8
    mSequences.push_back(new CSequenceStaticBrightness(pLEDManager, 50)); //  9
    mSequences.push_back(new CSequenceStaticBrightness(pLEDManager, 75)); // 10
    mSequences.push_back(new CSequenceStaticBrightness(pLEDManager, 100));// 11
    mSequences.push_back(new CSequenceTestSingle(pLEDManager));           // 12
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
