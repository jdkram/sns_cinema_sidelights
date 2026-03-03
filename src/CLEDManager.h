#ifndef ARDUINO_CLEDMANAGER_H
#define ARDUINO_CLEDMANAGER_H

#include <vector>

const int BOARD_1_ADDRESS = 0x60;
const int BOARD_2_ADDRESS = 0x40;

struct SLED{

  SLED(int pBoard, int pPin) : board(pBoard), pin(pPin), brightness(0.0f){}

    int board;
    int pin;
    float brightness;
};

class CLEDManager{

  public:

    CLEDManager();

    void ledBrightnessSet(int pLED, float pBrightness);
    float ledBrightnessGet(int pLED);

//    void ledOn(int pLED);
//    void ledOff(int pLED);

  private:

    int mBoard1;
    int mBoard2;

    std::vector<SLED> mLEDs;

    void ledAdd(int pBoard, int pPin);
    void pwmDutyCycleSet(int pLED, int pOffTime, int pOnTime);
    SLED* ledGet(int pLED);
};

#endif
