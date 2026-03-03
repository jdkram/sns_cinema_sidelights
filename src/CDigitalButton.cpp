#include <iostream>
#include "CDigitalButton.h"

#include <wiringPi.h>

#define CONSECUTIVE_READINGS_TO_TRIGGER 10

CDigitalButton::CDigitalButton(int pPin) : mPin(pPin), mPressed(false), mPressedLast(false), mConsecutiveReadings(0) {

    pinMode(pPin, INPUT);
    pullUpDnControl(pPin, PUD_DOWN);
    // setting this doesn't seem to make a difference but leaving it in just in case
}

void CDigitalButton::update() {

    int reading = digitalRead(mPin);

    if (reading) {
        mConsecutiveReadings++;
    } else {
        mConsecutiveReadings = 0;
    }

    mPressed = false;

    if(mConsecutiveReadings >= CONSECUTIVE_READINGS_TO_TRIGGER) {

//      mPressedLast used to prevent multiple presses being triggered
        if (!mPressedLast) {

            mPressed = true;
        }

        mPressedLast = true;

    } else {

        mPressedLast = false;
    }
}

bool CDigitalButton::wasPressed() {

    return mPressed;
}