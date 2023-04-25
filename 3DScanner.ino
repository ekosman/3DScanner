#include <EasyButton.h>

// Define stepper motor connections and steps per revolution
#define dirPin 3
#define stepPin 2
#define switchPin 8
#define stepsPerRevolution 800
#define stepDelay 50000

int direction = 1;

EasyButton limitSwitch(switchPin);

void onPressedCallback()
{
    int state = digitalRead(dirPin);
    switch (state)
    {
    case LOW:
    {
        digitalWrite(dirPin, HIGH);
        break;
    }
    case HIGH:
    {
        digitalWrite(dirPin, LOW);
        break;
    }
    }
}

void setup()
{
    // Set the motor pins as outputs
    Serial.begin(9600);
    pinMode(dirPin, OUTPUT);
    pinMode(stepPin, OUTPUT);
    limitSwitch.begin();
    limitSwitch.onPressed(onPressedCallback);
}

void loop()
{
    limitSwitch.read();
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(stepDelay);
    delay(2);
}
