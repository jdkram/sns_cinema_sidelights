// author: Paul?, Jonny Kram; ai-model: Claude Haiku; status: "#ai-input"
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
// Current sequence slots:
//   1 = Ambient        2 = FadeOutSimple  3 = HeartBeat
//   4 = FadeInSparkle  5 = KnightRider    6 = Ember
//   7 = Breathing478
//
// To revert to original 1-5 mapping, set BUTTON_SEQUENCE_MAP = {1, 2, 3, 4, 5}.
// To try ember on button 4: change index 3 from 4 to 6.
// ---------------------------------------------------------------------------
static const int BUTTON_SEQUENCE_MAP[] = {1, 2, 3, 6, 5};  // btn4 → Ember (was FadeInSparkle) while diagnosing KnightRider

// Human-readable names printed at startup -- keep in sync with CSequenceManager.cpp.
static const char* SEQUENCE_NAMES[] = {
    "",                // 0 unused (sequences are 1-based)
    "1: Ambient",
    "2: FadeOutSimple",
    "3: HeartBeat",
    "4: FadeInSparkle",
    "5: KnightRider",
    "6: Ember",
    "7: Breathing478",
};
static const int SEQUENCE_COUNT = 7;

#define BUTTON_1 22
#define BUTTON_2 27
#define BUTTON_3 18
#define BUTTON_4 4
#define BUTTON_5 17

CLEDManager* ledManager = nullptr;
CSequenceManager* sequenceManager = nullptr;

vector<CDigitalButton> mButtons;

static void printHelp() {
    cout << "\nAvailable sequences:" << endl;
    for (int i = 1; i <= SEQUENCE_COUNT; i++) {
        cout << "  " << SEQUENCE_NAMES[i] << endl;
    }
    cout << "\nButton map:" << endl;
    for (size_t i = 0; i < sizeof(BUTTON_SEQUENCE_MAP) / sizeof(BUTTON_SEQUENCE_MAP[0]); i++) {
        int seq = BUTTON_SEQUENCE_MAP[i];
        cout << "  Button " << (i + 1) << " -> " << SEQUENCE_NAMES[seq] << endl;
    }
    cout << endl;
    cout << "Usage: ./sns_lights [SEQUENCE_NUMBER]" << endl;
    cout << "  ./sns_lights        -- run normally, buttons active" << endl;
    cout << "  ./sns_lights 6      -- start Ember immediately, buttons active" << endl;
    cout << "  ./sns_lights --help -- print this message" << endl;
    cout << endl;
}

int main(int argc, char** argv) {

    cout << "SNS Lights started" << endl;
    printHelp();

//    usleep(1000000.0f * WAIT_ON_INIT_SECONDS);

    if (argc > 1 && strcmp(argv[1], "--help") == 0) {
        return 0;
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

    // Optional CLI arg: start a sequence immediately (buttons still work).
    if (argc > 1) {
        int seq = atoi(argv[1]);
        if (seq >= 1 && seq <= SEQUENCE_COUNT) {
            cout << "CLI: starting " << SEQUENCE_NAMES[seq] << endl;
            sequenceManager->sequenceStart(seq);
        } else {
            cout << "Unknown sequence number: " << argv[1]
                 << " (valid range: 1-" << SEQUENCE_COUNT << ")" << endl;
        }
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
            cout << "Button " << (i + 1) << " -> " << SEQUENCE_NAMES[seq] << endl;
            sequenceManager->sequenceStart(seq);
        }
    }

    sequenceManager->update();

    // Sleep to prevent I2C bus saturation on tight sequences (e.g. KnightRider overlapping fades).
    // 10ms = 100 updates/sec -- plenty of resolution for all current sequences.
    usleep(10000);
}