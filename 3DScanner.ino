// Define the pins used to connect the stepper motor
const int STEP_PIN = 2;
const int DIR_PIN = 3;

// Define the number of steps per revolution
const int STEPS_PER_REV = 200;

void setup()
{
    // Set the pins as outputs
    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN, OUTPUT);
}

void loop()
{
    // Rotate the stepper motor 1 revolution clockwise
    digitalWrite(DIR_PIN, HIGH); // Set the direction to clockwise
    for (int i = 0; i < STEPS_PER_REV; i++)
    {
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(1000); // Set the speed of the motor
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(1000); // Set the speed of the motor
    }

    // Pause for 1 second
    delay(1000);

    // Rotate the stepper motor 1 revolution counterclockwise
    digitalWrite(DIR_PIN, LOW); // Set the direction to counterclockwise
    for (int i = 0; i < STEPS_PER_REV; i++)
    {
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(1000); // Set the speed of the motor
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(1000); // Set the speed of the motor
    }

    // Pause for 1 second
    delay(1000);
}
