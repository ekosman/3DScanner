#include <ezButton.h>

// Define stepper motor connections and steps per revolution
#define dirPin 3
#define stepPin 2
#define stepsPerRevolution 800
#define stepDelay 50000

int direction = 1;

ezButton limitSwitch(8);

void setup()
{
    // Set the motor pins as outputs
    Serial.begin(9600);
    pinMode(dirPin, OUTPUT);
    pinMode(stepPin, OUTPUT);
    limitSwitch.setDebounceTime(50);
}

void loop()
{
    // Move the stepper motor forward one revolution
    limitSwitch.loop();

    if (limitSwitch.isPressed())
    {
        if (direction == 1)
        {
            digitalWrite(dirPin, LOW);
            direction = -1;
        }
        else
        {
            digitalWrite(dirPin, HIGH);
            direction = 1;
        }
    }
    if (limitSwitch.isReleased())
    {
        Serial.println(direction);
    }

    digitalWrite(stepPin, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(stepDelay);
    delay(2);
}
