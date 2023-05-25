#include <EasyButton.h>

// Define stepper motor connections and steps per revolution
#define YdirPin 3
#define YstepPin 2

#define ZdirPin 4
#define ZstepPin 5

#define switchPin 8
#define stepDelay 50

#define MAX_SPEED 100
#define SPEED_FACTOR 100

#define DELIMITER "_"

int direction = 1;


enum Direction {forward, backward, up, down};

EasyButton limitSwitch(switchPin);

void onPressedCallback()
{
    switch (digitalRead(YdirPin))
    {
    case LOW:
    {
        digitalWrite(YdirPin, HIGH);
        break;
    }
    case HIGH:
    {
        digitalWrite(YdirPin, LOW);
        break;
    }
    }
}

int getMotorDirPin(enum Direction direction){
  int res;
  if (direction == up || direction == down)
    res = 3;
  else if (direction == forward || direction == backward)
    res = 4;

  return res;
}

int getMotorStepPin(int direction){
  int res;
  if (direction == up || direction == down)
    res = 2;
  else if (direction == forward || direction == backward)
    res = 5;

  return res;
}

int getMotorStepValue(int direction){
  int res;
  if (direction == down || direction == forward)
    res = HIGH;
  else if (direction == up || direction == backward)
    res = LOW;

  return res;
}

void move(int direction, int revolutions, float speed){
  int motorDirPin = getMotorDirPin(direction);
  int stepPin = getMotorStepPin(direction);
  int stepPinValue = getMotorStepValue(direction);
  float delay = ((MAX_SPEED - speed) / MAX_SPEED) * SPEED_FACTOR;

  digitalWrite(motorDirPin, stepPinValue);

  for (int i = 0; i < revolutions; i++){
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(delay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(delay);
  }


}

void setup()
{
    // Set the motor pins as outputs
    Serial.begin(9600);
    pinMode(YdirPin, OUTPUT);
    pinMode(YstepPin, OUTPUT);
    pinMode(ZdirPin, OUTPUT);
    pinMode(ZstepPin, OUTPUT);
    // limitSwitch.begin();
    // limitSwitch.onPressed(onPressedCallback); // called when released
    // limitSwitch.onPressedFor(2, onPressedCallback);
}

String getEndOfNextToken(String str, int startIndex, String delimiter){
  int index = str.indexOf(delimiter);
  return str.substring(startIndex, index);
}

void loop()
{
  if (Serial.available()) { // Check if there is data available to read
    String receivedString = Serial.readString(); // Read the incoming string
    
    // type
    int startIndex = 0;
    int endIndex = receivedString.indexOf(DELIMITER, startIndex);
    String type = receivedString.substring(startIndex, endIndex);
    
    // direction
    startIndex = endIndex + 1;
    endIndex = receivedString.indexOf(DELIMITER, startIndex);
    String direction = receivedString.substring(startIndex, endIndex);
    
    // steps
    startIndex = endIndex + 1;
    endIndex = receivedString.indexOf(DELIMITER, startIndex);
    int steps = receivedString.substring(startIndex, endIndex).toInt();

    // speed
    startIndex = endIndex + 1;
    endIndex = receivedString.indexOf(DELIMITER, startIndex);
    int speed = receivedString.substring(startIndex, endIndex).toInt();

    Serial.println(type);
    Serial.println(direction);
    Serial.println(steps);
    Serial.println(speed);

    if (direction == "up"){
      // Serial.println("move 10 up"); // Print the received string
      move(up, steps, speed);
    } else if (direction == "down"){
      // Serial.println("move 10 up"); // Print the received string
      move(down, steps, speed);
    } else if (direction == "forward"){
      // Serial.println("move 10 up"); // Print the received string
      move(forward, steps, speed);
    } else if (direction == "backward"){
      // Serial.println("move 10 up"); // Print the received string
      move(backward, steps, speed);
    }
  }
}
