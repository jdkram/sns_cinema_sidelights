#include <vector>

using namespace std;

class CDigitalButton {

public:
    CDigitalButton(int pPin);

    bool wasPressed();

    void update();

private:
    int mPin;
    bool mPressed;
    bool mPressedLast;
    int mConsecutiveReadings;
};