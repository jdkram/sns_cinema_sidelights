// author: Paul?, Jonny Kram; ai-model: Claude Haiku, Claude Opus 4.6; status: "#ai-input"
#include <iostream>
#include <vector>
#include <wiringPi.h>
#include <unistd.h> // has usleep()
#include <ctime> // Needed for the true randomization
#include <cstdlib>
#include <cstring>

#include "CDigitalButton.h"
#include "CLEDManager.h"
#include "CSequenceManager.h"

#include "main.h"

#include <chrono>

using namespace std;

// ---------------------------------------------------------------------------
// Button-to-sequence mapping
// Edit BUTTON_SEQUENCE_MAP to change what each physical button triggers.
// Indices are 0-based (index 0 = button 1), values are 1-based sequence numbers.
//
// Current sequence slots (see also ENTRY_NAMES array below):
//   1 = Ambient        5 = KnightRider     9 = Static 50%
//   2 = FadeOutSimple  6 = Ember           10 = Static 75%
//   3 = HeartBeat      7 = Breathing478    11 = Static 100%
//   4 = FadeInSparkle  8 = AmbientHigh     12 = TestSingle (event engine diagnostic)
//
// To revert to original 1-5 mapping, set BUTTON_SEQUENCE_MAP = {1, 2, 3, 4, 5}.
// To try ember on button 4: change index 3 from 4 to 6.
// ---------------------------------------------------------------------------
static const int BUTTON_SEQUENCE_MAP[] = {1, 2, 3, 10, 8};  // btn4 → Static 75%, btn5 → AmbientHigh

// All callable entries: sequences 1-12, then hardware diagnostics 13-16.
static const char* ENTRY_NAMES[] = {
    "",                       // 0 unused (1-based)
    "1: Ambient",
    "2: FadeOutSimple",
    "3: HeartBeat",
    "4: FadeInSparkle",
    "5: KnightRider",
    "6: Ember",
    "7: Breathing478",
    "8: AmbientHigh",         // ambient with 30-100% floor (threshold workaround)
    "9: Static 50%",
    "10: Static 75%",
    "11: Static 100%",
    "12: TestSingle",         // event engine diagnostic: 1 LED via event engine (LED 5, 100%)
    "13: DIAG all-on",        // all LEDs 100% for 10s (bypasses event engine)
    "14: DIAG sweep",         // each LED individually, 2s each (bypasses event engine)
    "15: DIAG fade",          // smooth 0->100->0 on all LEDs (bypasses event engine)
    "16: DIAG half",          // all LEDs 50% for 10s (bypasses event engine)
};
static const int SEQUENCE_COUNT = 12;
static const int DIAG_START = 13;
static const int ENTRY_COUNT = 16;

#define BUTTON_1 22
#define BUTTON_2 27
#define BUTTON_3 18
#define BUTTON_4 4
#define BUTTON_5 17

CLEDManager* ledManager = nullptr;
CSequenceManager* sequenceManager = nullptr;

vector<CDigitalButton> mButtons;

static void printHelp() {
    cout << "\nSequences:" << endl;
    for (int i = 1; i <= SEQUENCE_COUNT; i++) {
        cout << "  " << ENTRY_NAMES[i] << endl;
    }
    cout << "\nHardware diagnostics (bypass event engine, test LEDs directly):" << endl;
    for (int i = DIAG_START; i <= ENTRY_COUNT; i++) {
        cout << "  " << ENTRY_NAMES[i] << endl;
    }
    cout << "\nButton map:" << endl;
    for (size_t i = 0; i < sizeof(BUTTON_SEQUENCE_MAP) / sizeof(BUTTON_SEQUENCE_MAP[0]); i++) {
        int seq = BUTTON_SEQUENCE_MAP[i];
        cout << "  Button " << (i + 1) << " -> " << ENTRY_NAMES[seq] << endl;
    }
    cout << endl;
    cout << "Usage: ./main [NUMBER]" << endl;
    cout << "  ./main        -- run normally, buttons active" << endl;
    cout << "  ./main 6      -- start Ember immediately, buttons active" << endl;
    cout << "  ./main 13     -- run LED sweep diagnostic" << endl;
    cout << "  ./main --help -- print this message" << endl;
    cout << endl;
}

// ---------------------------------------------------------------------------
// Hardware diagnostic tests (entries 8-11)
// These bypass the event/sequence engine entirely and write directly to the
// PCA9685 via CLEDManager. If these work but sequences don't, the problem
// is in software. If these fail, the problem is hardware/wiring.
// ---------------------------------------------------------------------------

static int runDiagnostic(int diagNumber) {
    cout << "\n=== DIAGNOSTIC: " << ENTRY_NAMES[diagNumber] << " ===" << endl;

    wiringPiSetupGpio();
    ledManager = new CLEDManager();

    if (diagNumber == 13) {
        // All LEDs to 100% for 10 seconds.
        cout << "Setting all 24 LEDs to 100%..." << endl;
        for (int led = 1; led <= 24; led++) {
            ledManager->ledBrightnessSet(led, 100);
        }
        cout << "All LEDs should now be ON. Waiting 10 seconds..." << endl;
        cout << "Count how many of the 24 LEDs are lit." << endl;
        usleep(10000000);

        cout << "Turning all LEDs off..." << endl;
        for (int led = 1; led <= 24; led++) {
            ledManager->ledBrightnessSet(led, 0);
        }
        cout << "Done. How many LEDs were on? (Expected: 24)" << endl;

    } else if (diagNumber == 14) {
        // Light each LED individually, 2 seconds each.
        cout << "Sweeping through LEDs 1-24, one at a time (2s each)..." << endl;
        cout << "Note which LEDs light up and which don't." << endl;
        for (int led = 1; led <= 24; led++) {
            cout << "  LED " << led << " ON" << endl;
            ledManager->ledBrightnessSet(led, 100);
            usleep(2000000);
            ledManager->ledBrightnessSet(led, 0);
        }
        cout << "Sweep complete. Which LEDs were dead?" << endl;

    } else if (diagNumber == 15) {
        // Smooth fade 0 -> 100 -> 0 on all LEDs, direct writes.
        cout << "Fading all LEDs: 0 -> 100 over 5s, then 100 -> 0 over 5s." << endl;
        cout << "Watch for SMOOTH brightness change vs winking/flickering." << endl;

        for (int step = 0; step <= 100; step++) {
            for (int led = 1; led <= 24; led++) {
                ledManager->ledBrightnessSet(led, step);
            }
            cout << "  brightness: " << step << "%" << "\r" << flush;
            usleep(50000);
        }
        cout << endl;

        for (int step = 100; step >= 0; step--) {
            for (int led = 1; led <= 24; led++) {
                ledManager->ledBrightnessSet(led, step);
            }
            cout << "  brightness: " << step << "%" << "\r" << flush;
            usleep(50000);
        }
        cout << endl << "Done. Was the fade smooth or did LEDs wink/flicker?" << endl;

    } else if (diagNumber == 16) {
        // All LEDs to 50%, hold.
        cout << "Setting all 24 LEDs to 50%..." << endl;
        for (int led = 1; led <= 24; led++) {
            ledManager->ledBrightnessSet(led, 50);
        }
        cout << "LEDs should be at half brightness. Waiting 10 seconds..." << endl;
        cout << "Are they steady or flickering?" << endl;
        usleep(10000000);

        cout << "Turning all LEDs off..." << endl;
        for (int led = 1; led <= 24; led++) {
            ledManager->ledBrightnessSet(led, 0);
        }
        cout << "Done." << endl;
    }

    delete ledManager;
    return 0;
}

int main(int argc, char** argv) {

    cout << "SNS Lights started" << endl;
    printHelp();

//    usleep(1000000.0f * WAIT_ON_INIT_SECONDS);

    if (argc > 1 && strcmp(argv[1], "--help") == 0) {
        return 0;
    }

    // Parse the entry number from CLI arg (sequence or diagnostic).
    int entry = 0;
    if (argc > 1) {
        entry = atoi(argv[1]);
    }

    // Diagnostics (8-11) bypass the event engine entirely.
    if (entry >= DIAG_START && entry <= ENTRY_COUNT) {
        return runDiagnostic(entry);
    }

    srand(time(0)); // Seed RNG used by random-pattern sequences (Ember, Ambient, etc.)

    wiringPiSetupGpio();

    ledManager = new CLEDManager();
    sequenceManager = new CSequenceManager(ledManager);

    mButtons.push_back(CDigitalButton(BUTTON_1));
    mButtons.push_back(CDigitalButton(BUTTON_2));
    mButtons.push_back(CDigitalButton(BUTTON_3));
    mButtons.push_back(CDigitalButton(BUTTON_4));
    mButtons.push_back(CDigitalButton(BUTTON_5));

    // Start a sequence immediately if requested (buttons still work).
    if (entry >= 1 && entry <= SEQUENCE_COUNT) {
        cout << "CLI: starting " << ENTRY_NAMES[entry] << endl;
        sequenceManager->sequenceStart(entry);
    } else if (entry != 0) {
        cout << "Unknown entry: " << argv[1]
             << " (valid range: 1-" << ENTRY_COUNT << ")" << endl;
    }

    while(1){
        update();
    }

    return 0;
}

void update(){

    for(size_t i = 0; i < mButtons.size(); i++){

        CDigitalButton* button = &mButtons[i];

        button->update();

        if(button->wasPressed()){
            int seq = BUTTON_SEQUENCE_MAP[i];
            cout << "Button " << (i + 1) << " -> " << ENTRY_NAMES[seq] << endl;
            sequenceManager->sequenceStart(seq);
        }
    }

    sequenceManager->update();

    // Sleep to prevent I2C bus saturation on tight sequences (e.g. KnightRider overlapping fades).
    // 10ms = 100 updates/sec -- plenty of resolution for all current sequences.
    usleep(10000);
}
