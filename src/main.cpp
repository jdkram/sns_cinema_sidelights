#include <iostream>
#include <vector>
#include <wiringPi.h>
#include <unistd.h> // has usleep()
#include <ctime> // Needed for the true randomization
#include <cstdlib>

#include "CDigitalButton.h"
#include "CLEDManager.h"
#include "CSequenceManager.h"

#include "main.h"

#include <chrono>

using namespace std;

//#define WAIT_ON_INIT_SECONDS 18
// Pi needs to boot up - otherwise

#define BUTTON_1 22
#define BUTTON_2 27
#define BUTTON_3 18
#define BUTTON_4 4
#define BUTTON_5 17

CLEDManager* ledManager = nullptr;
CSequenceManager* sequenceManager = nullptr;

vector<CDigitalButton> mButtons;

int main(int argc, char** argv) {

    cout << "Started" << endl;

//    usleep(1000000.0f * WAIT_ON_INIT_SECONDS);

    srand(time(0)); // Random numbers generated in sequences - need seeding

    wiringPiSetupGpio();

    ledManager = new CLEDManager();
    sequenceManager = new CSequenceManager(ledManager);

    mButtons.push_back(CDigitalButton(BUTTON_1));
    mButtons.push_back(CDigitalButton(BUTTON_2));
    mButtons.push_back(CDigitalButton(BUTTON_3));
    mButtons.push_back(CDigitalButton(BUTTON_4));
    mButtons.push_back(CDigitalButton(BUTTON_5));

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

            cout << "Pressed: " << (i + 1) << endl;
            sequenceManager->sequenceStart(i+1);
        }
    }

    sequenceManager->update();

    // Sleep in case the processor needs to go off and do other things - still 100 updates a second
//    usleep(1000000.0f * UPDATE_INTERVAL_SECONDS);
}