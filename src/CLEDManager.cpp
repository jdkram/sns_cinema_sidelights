#include "CLEDManager.h"

#include <iostream>
#include <wiringPi.h>

#include "../pca9685/src/pca9685.h"

#define PIN_BASE_1 100
#define PIN_BASE_2 200
#define HERTZ 1000

using namespace std;

CLEDManager::CLEDManager() {

    mBoard1 = pca9685Setup(PIN_BASE_1, BOARD_1_ADDRESS, HERTZ);
    mBoard2 = pca9685Setup(PIN_BASE_2, BOARD_2_ADDRESS, HERTZ);

    if (mBoard1 < 0 || mBoard2 < 0) {
        printf("Error in setup\n");
        return;
    }

    // Reset all output
//    pca9685PWMReset(mBoard1);
//    pca9685PWMReset(mBoard2);

    for (int pin = 0; pin < 6; pin++) {

//        cout << "Pin: " << pin << ", " << PIN_BASE_1 + pin + 2 << endl;
        ledAdd(mBoard1, PIN_BASE_1 + pin + 2);
    }

    // Second half of pins are wired up in reverse order - quicker to change here than rewire
    for (int pin = 0; pin < 6; pin++) {

//        cout << "Pin: " << pin << ", " << PIN_BASE_1 + 13 - pin << endl;
        ledAdd(mBoard1, PIN_BASE_1 + 13 - pin);
    }

    for (int pin = 0; pin < 6; pin++) {

        ledAdd(mBoard1, PIN_BASE_2 + pin + 2);
    }

    // Second half of pins are wired up in reverse order - quicker to change here than rewire
    for (int pin = 0; pin < 6; pin++) {

        ledAdd(mBoard2, PIN_BASE_2 + 13 - pin);
    }

    for (size_t i = 1; i <= mLEDs.size(); i++) {

        ledBrightnessSet(i, 0);
    }
}

void CLEDManager::ledAdd(int pBoard, int pPin) {

    SLED led = SLED(pBoard, pPin);

    mLEDs.push_back(led);
}

// pLED is number shown on the box
// Power is out of 100
void CLEDManager::ledBrightnessSet(int pLED, float pBrightness) {

    if (pBrightness < 0 || pBrightness > 100) {
        cout << "LED Power must be between 0 and 100" << endl;
        return;
    }

    if (SLED *led = ledGet(pLED)) {

        led->brightness = pBrightness;

        // Convert power percentage to tick in the duty cycle
        int powerScaledUp = pBrightness * 4095.0 / 100.0;

        int onTime = 4095 - powerScaledUp;

        pwmWrite(led->pin, onTime);
    }
}

float CLEDManager::ledBrightnessGet(int pLED) {

    if (SLED *led = ledGet(pLED)) {

        return led->brightness;
    }

    return 0;
}


SLED *CLEDManager::ledGet(int pLED) {

    int ledIndex = pLED - 1;
    // Taking away one to get the position in the vector which is what pwmDutyCycleSet takes

    if ((size_t) ledIndex < 0 || (size_t) ledIndex >= mLEDs.size()) {

        cout << "LED not found - should be between 1 and 24" << endl;
        return nullptr;
    }

    return &mLEDs[ledIndex];
}

// Duty Cycle is 0-4095 ticks - set when to go off and when to go on
//void CLEDManager::pwmDutyCycleSet(int pLED, int pOffTime, int pOnTime){
//
//  if(SLED* led = ledGet(pLED)){
//
//    led->board->setPWM(led->pin, pOffTime, pOnTime);
//
//    // Serial.print("Setting PWM Cycle: ");
//    // Serial.print(led->pin);
//    // Serial.print(",");
//    // Serial.print("pOffTime,");
//    // Serial.print(pOffTime);
//    // Serial.print(",");
//    // Serial.print(pOnTime);
//    // Serial.print(",");
//  }
//  else{
//
//    Serial.print("LED not found: ");
//  }
//
//  // nl();
//}

// Docs for the board suggest using this to turn to full or 0 power
// but don't think we'll see the difference between this and using the brightnessSet function
//void CLEDManager::ledOn(int pPin){
//
//  pwmDutyCycleSet(pPin-1, 0, 4096);
//}
//
//void CLEDManager::ledOff(int pPin){
//
//  pwmDutyCycleSet(pPin-1, 4096, 0);
//}
