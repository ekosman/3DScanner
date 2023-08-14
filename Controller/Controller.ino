#include <Servo.h>

// Define stepper motor connections and steps per revolution
#define Y_DIR_PIN 3
#define Y_STEP_PIN 2

#define Z_DIR_PIN 4
#define Z_STEP_PIN 5

#define X_ROLL_PIN 10
#define ZERO_X_ROLL 123
#define DELTA_X_ROLL 20

#define Y_ROLL_PIN 11
#define ZERO_Y_ROLL 123
#define DELTA_Y_ROLL 90



#define Y_DOWN_SWITCH_PIN 26
#define Y_DOWN_SWITCH_LOW_PIN 27
#define Y_DOWN_SWITCH_SIGNAL_PIN 19

#define Y_UP_SWITCH_PIN 24
#define Y_UP_SWITCH_LOW_PIN 25
#define Y_UP_SWITCH_SIGNAL_PIN 20

#define Z_BACK_SWITCH_PIN 22
#define Z_BACK_SWITCH_LOW_PIN 23
#define Z_BACK_SWITCH_SIGNAL_PIN 21

#define Z_FRONT_SWITCH_PIN 28
#define Z_FRONT_SWITCH_LOW_PIN 29
#define Z_FRONT_SWITCH_SIGNAL_PIN 18

#define MAX_SPEED 100
#define SPEED_FACTOR 100

#define DELIMITER "_"

#define DebounceTimer 50

typedef void (*intFunction)();

volatile bool YDownSwitchPressed = false, YUpSwitchPressed = false;
volatile bool ZBackSwitchPressed = false, ZFrontSwitchPressed = false;

volatile unsigned int previousMillisForDebounce = 0;
volatile unsigned int currentMillis = 0;

Servo xRollServo, yRollServo;

enum Direction { forward, backward, up, down, xRoll, yRoll };

int getMotorDirPin(enum Direction direction) {
  int res;
  if (direction == up || direction == down)
    res = Y_DIR_PIN;
  else if (direction == forward || direction == backward)
    res = Z_DIR_PIN;

  return res;
}

int getMotorStepPin(int direction) {
  int res;
  if (direction == up || direction == down)
    res = Y_STEP_PIN;
  else if (direction == forward || direction == backward)
    res = Z_STEP_PIN;

  return res;
}

int getMotorStepValue(int direction) {
  int res;
  if (direction == down || direction == forward)
    res = HIGH;
  else if (direction == up || direction == backward)
    res = LOW;

  return res;
}

void moveAxis(int direction, int revolutions, float speed) {
  int motorDirPin = getMotorDirPin(direction);
  int stepPin = getMotorStepPin(direction);
  int stepPinValue = getMotorStepValue(direction);
  float delay = ((MAX_SPEED - speed) / MAX_SPEED) * SPEED_FACTOR;

  digitalWrite(motorDirPin, stepPinValue);

  for (int i = 0; i < revolutions; i++) {
    if (doesConflit(direction)) {
      Serial.println("stop!");
      break;
    }
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(delay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(delay);
  }
}

bool doesConflit(int direction) {
  return ((YUpSwitchPressed && (direction == up)) || (YDownSwitchPressed && (direction == down)) ||
          (ZFrontSwitchPressed && (direction == forward)) ||
          (ZBackSwitchPressed && (direction == backward)));
}

void buttonStateChanged(int signalPin, bool *out) {
  currentMillis = millis();

  if (currentMillis - previousMillisForDebounce >= DebounceTimer) {
    previousMillisForDebounce = currentMillis;
    *out = 1 - *out;
    // if (digitalRead(signalPin)) {
    //   *out = false;
    //   Serial.print("Up,");
    // } else {
    //   *out = true;
    //   Serial.print("Down,");
    // }
  }
}

void ZBackbuttonStateChanged() {
  buttonStateChanged(Z_BACK_SWITCH_SIGNAL_PIN, &ZBackSwitchPressed);
}

void ZFrontbuttonStateChanged(){
  buttonStateChanged(Z_FRONT_SWITCH_SIGNAL_PIN, &ZFrontSwitchPressed);
}

void YDownbuttonStateChanged(){
  buttonStateChanged(Y_DOWN_SWITCH_SIGNAL_PIN, &YDownSwitchPressed);
}

void YUpbuttonStateChanged(){
  buttonStateChanged(Y_UP_SWITCH_SIGNAL_PIN, &YUpSwitchPressed);
}

void configureLimitSwitch(int switchPin, int switchSignalPin, int lowPin, intFunction func) {
  pinMode(switchPin, OUTPUT);
  digitalWrite(switchPin, HIGH);

  attachInterrupt(digitalPinToInterrupt(switchSignalPin), func, CHANGE);

  pinMode(lowPin, OUTPUT);
  digitalWrite(lowPin, LOW);

  Serial.println("Pin " + String(switchPin) + " is pressed: " + String(curState));
  if (switchPin == Y_DOWN_SWITCH_PIN)
    YDownSwitchPressed = curState;
  else if (switchPin == Y_UP_SWITCH_PIN)
    YUpSwitchPressed = curState;
  else if (switchPin == Z_FRONT_SWITCH_PIN)
    ZFrontSwitchPressed = curState;
  else if (switchPin == Z_BACK_SWITCH_PIN)
    ZBackSwitchPressed = curState;
}

void setup() {
  // Set the motor pins as outputs
  Serial.begin(9600);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);
  pinMode(Z_STEP_PIN, OUTPUT);

  xRollServo.attach(X_ROLL_PIN, 800, 2200);
  yRollServo.attach(Y_ROLL_PIN, 800, 2200);

  configureLimitSwitch(Y_UP_SWITCH_PIN, Y_UP_SWITCH_SIGNAL_PIN, Y_UP_SWITCH_LOW_PIN, YUpbuttonStateChanged);
  configureLimitSwitch(Y_DOWN_SWITCH_PIN, Y_DOWN_SWITCH_SIGNAL_PIN, Y_DOWN_SWITCH_LOW_PIN, YDownbuttonStateChanged);
  configureLimitSwitch(Z_BACK_SWITCH_PIN, Z_BACK_SWITCH_SIGNAL_PIN, Z_BACK_SWITCH_LOW_PIN, ZBackbuttonStateChanged);
  configureLimitSwitch(Z_FRONT_SWITCH_PIN, Z_FRONT_SWITCH_SIGNAL_PIN, Z_FRONT_SWITCH_LOW_PIN, ZFrontbuttonStateChanged);
  

  Serial.println("Init complete!");
}

void loop() {
  if (Serial.available()) {                       // Check if there is data available to read
    String receivedString = Serial.readString();  // Read the incoming string

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

    if (direction == "up") {
      // Serial.println("move 10 up"); // Print the received string
      moveAxis(up, steps, speed);
    } else if (direction == "down") {
      // Serial.println("move 10 up"); // Print the received string
      moveAxis(down, steps, speed);
    } else if (direction == "forward") {
      // Serial.println("move 10 up"); // Print the received string
      moveAxis(forward, steps, speed);
    } else if (direction == "backward") {
      // Serial.println("move 10 up"); // Print the received string
      moveAxis(backward, steps, speed);
    } else if (direction == "xRoll") {
      steps = constrain(steps, ZERO_X_ROLL - DELTA_X_ROLL, ZERO_X_ROLL + DELTA_X_ROLL);
      xRollServo.write(steps);
    } else if (direction == "yRoll") {
      steps = constrain(steps, ZERO_Y_ROLL - DELTA_Y_ROLL, ZERO_Y_ROLL + DELTA_Y_ROLL);
      yRollServo.write(steps);
    }
  }
}
