// Diagnostic: exercises the event engine with a single-channel write.
// Sets LED 5 to 100% via brightnessSetEventAdd (the simplest possible event),
// then holds for 10 seconds. Non-looping so it stops cleanly.
//
// Expected: LED 5 (board 0x40, left row 1, #5) lights up immediately and stays on.
// If it doesn't: the event engine cannot drive individual channels -- hardware/driver bug.
// Compare with ./main 13 (DIAG sweep) which writes the same LED directly, bypassing the engine.
#include "CSequenceTestSingle.h"

#include <iostream>
using namespace std;

CSequenceTestSingle::CSequenceTestSingle(CLEDManager *pLEDManager) :
        CSequence(pLEDManager, false, 10.0f) { // non-looping, 10 seconds

    cout << "TestSingle: will set LED 5 to 100% via event engine at t=0." << endl;
    cout << "Watch LED 5 (board 0x40, left row 1 #5) for 10 seconds." << endl;

    brightnessSetEventAdd(5, 100, 0.0f);
}
