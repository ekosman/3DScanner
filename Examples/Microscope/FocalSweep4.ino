/*
  Benthic Underwater Microscope Control
  Written by Andrew Mullen
  03/02/2015 - BUM_Board V2.0

  The Arduino controls 3 system components - the camera, LED's and optotune
  electronically tunable lens (ETL). System component: Physical parameter which
  is controlled --> System parameters which can be adjusted
    1. Camera: Trigger Camera Exposure --> Frames Per Second (Computer controls:
  turn saving on/off, exposure length) cl = live view (cl1 = on, cl0 = off) cs =
  single focal scan cp = single photometric circle ct = start time series ct# =
  change time series interval length (min) cf# = change frames per ??

    2. Optotune: Current Supplied to Optotune --> Number of Focal Steps, Current
  Focal Step of = step one focal step forward ob = step one focal step backward
      oc# = choose specific focal step number
      os# = change total number of focal steps

  SPI Interface - Control
    The circuit: CS - to digital pin 0  (SS pin), SDI - to digital pin 2 (MOSI
  pin), CLK - to digital pin 1 (SCK pin)
*/

////////
// Set Up
////////

// Include Libraries:
#include <SPI.h>
#include <Servo.h>
// Set Variables
// Camera
const int cameraTrigger = 4;  // set the camera trigger pin
int fps = 10;                 // set fps
// Projector
const int externalTrigger = 6;  // external trigger pin
// LEDS
const int ledTrigger = 21;  // led 1
const int all = 0;
const int w = 1;
const int b = 2;
const int r = 3;
const int e = 4;
const int off = 5;  // duration of led pulses (microseconds)
int ledMode = all;
long ledTime[] = {400, 200, 200, 200, 10};
// Optotune
// Optotune - Determine BFL/Amps/Driver Level
int stepTotal = 6;       // set total number of focal steps (default 200)
int previous_stepTotal;  // used to reset stepNum when changing stepTotal
int stepNum = 0;         // set current focal step nunmber
int extraSteps;          // extra exposure after stack is finished (to ensure program
                         // does not get stuck)
boolean scanRange = 0;   // choose to only scan over a specific range

int scanMin = 0;          // used with scan range option  int scanMin = 0
int scanMax = stepTotal;  // used with scan range option int scanMax = stepTotal
int stepDelay = 10;
int scanStep = 50;

float wd;
float wdMax = 86;
float wdMin = 60;           // bfl = back focal length (mm)
float optotuneAmp;          // optotuneAmp = -0.0001242*bfl^3 + 0.06884*bfl^2
                            // - 13.83*bfl + 1015.2 (in milli-amps)
float driverAmp_max = 300;  // in milli-amps
float driverAmp_max_use = 250;
int optotuneAmp_list[200];
int driverLevel;      // driverLevel is 12 bit = 0 - 4095, driverLevel =
                      // (optotuneAmp / driverAmp_max) * 4095
int driverVals[200];  // values found from optotune manual, set driverVals array
                      // with 100 slots
int wdVals[200];
long currentReport;  // report current via gui
int i;
int a;
int j;
// Optotune - SPI
const int slaveSelectPin = 0;  // set pin 0 as the slave select to initialize driverSPI Interface
const int addressSPI = 0;      // set SPI address for driver to 0
int driverByte1;
int driverByte2;  // data sent to driver: 4 bit address, 12 bit current level ->
                  // split into 2 bytes (8 bits each)
// Reading Input
int incomingByte;
String command;
int setting = 0;
int mode = 0;
long value = 0;
boolean state = 0;
// Controlling Loops
boolean firstLoop = 1;

// Capture Parameters
long exposureTime = 20000;  // us //long exposureTime = 40000; //us
int projExposurePer = 50;   // percentage
bool use_LED = 0;

// Setup Loop
void setup() {
  // Computer Communcation (Serial Interface)
  Serial.begin(9600);  // initialize serial communication
  while (!Serial) {
    ;  // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Arduino connected! Version 0");

  // Driver Communication (SPI Interface)
  pinMode(slaveSelectPin, OUTPUT);  // set the slaveSelectPin as an output
  SPI.begin();                      // initialize SPI
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE0);
  SPI.setClockDivider(SPI_CLOCK_DIV4);
  // Camera + Projector
  pinMode(cameraTrigger, OUTPUT);
  pinMode(externalTrigger, OUTPUT);  // projector
  pinMode(ledTrigger, OUTPUT);       // LED
  Serial.flush();                    // make sure nothing's in the buffer at the beginning of the
                                     // run
}

//////////////
// Program Loop
//////////////
void loop() {
  // Program Startup
  if (firstLoop == 1) {
    Serial.println("Hello Teensy Started, Waiting for order...");  //***Making Read Input
                                                                   // Not Work, Very Odd***
    setting = 'q';
    mode = 'S';
    value = stepTotal;
    optotuneControl();
    firstLoop = 0;
  }
  if (Serial.available()) {
    readInput();
  }  // get input

  // System Settings - Optotune Camera
  if (setting == 'O' || setting == 'o') {
    optotuneControl();
    setting = 'q';  // Control Optotune
  }
  if (setting == 'P' || setting == 'p') {
    setParameters();
    setting = 'q';
  }
  // Imaging
  if (setting == 'C' || setting == 'c')  // Capture
  {
    if (mode == 'S' || mode == 's') {
      captureFocalSweep();
      setting = 'q';  // Single focal sweep
    }
    if (mode == 'R' || mode == 'r') {
      advanceCamera();
      setting = 'q';  // Advance projector
    }
    if (mode == 'm') {
      captureSingleStep();
      setting = 'q';  // Single focal sweep in slow motion
    }
    if (mode == 'l') {
      captureLiveView();  // Captures continues live view
    }

    if (mode == 'b') {
      stopView();
      setting = 'q';
    }

    if (mode == 'F' || mode == 'f') {
      FocalStack();
      setting = 'q';
    }
  }
  // DEBUG
  if (setting == 'd')  // Debug
  {
    if (mode == 'p') {
      advanceProjector();  // Advance projector
    }
  }
}

////////////////////////
// Basic System Functions
////////////////////////
void readInput() {
  //  incomingByte = Serial.read(); command = incomingByte; //read first byte
  while (Serial.available() /*!= 0*/) {
    incomingByte = Serial.read();  // continue reading if additional bytes
    command.concat((char)incomingByte);
  }
  // Serial.println(""); Serial.print("Input: "); Serial.print(command);
  // Serial.println(); //display complete input
  setting = command[0];         // select setting from input
  mode = command[1];            // select mode from input
  value = atol(&(command[2]));  // select value from input
  if (value == 0) {
    state = 0;
  } else if (value == 1) {
    state = 1;
  } else
    state = 2;
  command = "";
  Serial.flush();
}
///////////////////
void setCurrentDriver(int driverLevel) {
  digitalWrite(slaveSelectPin,
               LOW);  // take the SS pin low to initialize SPI communication
  driverByte1 = (addressSPI << 4) + ((unsigned int)driverLevel >>
                                     8);  // SPI address shifted 4 bits, first 4 bits of level
  driverByte2 = 255 & driverLevel;        // last 8 bis of level (calculated using
                                          // bitwise logic, 255 = 11111111)
  SPI.transfer(driverByte1);
  SPI.transfer(driverByte2);  //  send in the address and value via SPI
  digitalWrite(slaveSelectPin,
               HIGH);  // take the SS pin high to de-select the chip
}

////////////////////////////////
// System Control Functions
///////////////////////
void optotuneControl() {
  if (mode == 'S' || mode == 's')  // Change the number of Focal Steps
  {
    stepTotal = value;
    Serial.print("New Number of Steps: ");
    Serial.println(stepTotal);
    for (i = 0; i < stepTotal; i++) {
      optotuneAmp = ((float)i + 0.5) / (float)stepTotal * driverAmp_max_use;
      // wd = (float)wdMax - i * ( (wdMax-wdMin) / ((float)stepTotal-1) ); //
      // (BFL = 210mm to 80mm range) optotuneAmp =  -0.00025058632*pow(wd,4) +
      // 0.07517730392*pow(wd,3) - 8.49438801629*pow(wd,2) + 419.36852014456*wd
      // - 7344.10899548123;

      optotuneAmp_list[i] = optotuneAmp * 1;
      driverVals[i] = (optotuneAmp / driverAmp_max) * 4095;
      wdVals[i] = 0;
      Serial.print("Step:");
      Serial.print(i);
      Serial.print("  WD:");
      Serial.print(wd);
      Serial.print("mm  Current:");
      Serial.print(optotuneAmp);
      Serial.print("mA  DriverVal: ");
      Serial.println(driverVals[i]);
      // Serial.println(optotuneAmp);
    }
    Serial.print("Current Step: ");
    Serial.print(stepNum);
    Serial.print(" ( ");
    Serial.print(stepTotal);
    Serial.print(" total steps)");
    Serial.print("  Current:");
    Serial.print(optotuneAmp_list[stepNum]);
    Serial.println("mA");

    int stepExposure = exposureTime / stepTotal;
    int prePatternDelay = int(((10000.0 - float(projExposurePer)) * float(stepExposure)) /
                              10000.0);  // ursprunglich at 100.0
    int delayFirstHalf = (stepExposure - prePatternDelay) / 2;
    int delaySecondHalf = stepExposure - prePatternDelay - delayFirstHalf;

    Serial.println("");
    Serial.print("Exposure time = ");
    Serial.print(exposureTime / 1000);
    Serial.println("ms");
    Serial.print("Step duration is ");
    Serial.print(stepExposure);
    Serial.println("us");
    Serial.print("Delay: ");
    Serial.print(prePatternDelay);
    Serial.println("us");
    Serial.print("First duty cycle: ");
    Serial.print(delayFirstHalf);
    Serial.println("us");
    Serial.print("Second duty cycle: ");
    Serial.print(delaySecondHalf);
    Serial.println("us");
    Serial.print("Max current: ");
    Serial.print(driverAmp_max_use);
    Serial.println("mA");

    stepNum = 0;
  }
  if (mode == 'F' || mode == 'f') {
    if (stepNum < stepTotal - 1) {
      stepNum++;  // Step optotune backwards
    } else {
      stepNum = 0;
    };
  }
  if (mode == 'B' || mode == 'b') {
    if (stepNum > 0) {
      stepNum--;  // Step optotune forwards
    } else {
      stepNum = stepTotal - 1;
    };
  }
  if (mode == 'C' || mode == 'c') {
    if (value > -1 && value < stepTotal) {
      stepNum = value;  // Specific optotune step
    };
  }
  if (mode == 'A' || mode == 'a') {
    stepNum = stepTotal - 1;  // Step optotune to max value
  }
  if (mode == 'Z' || mode == 'z') {
    stepNum = 0;  // Step optotune to min value
  }
  setCurrentDriver(driverVals[stepNum]);
}

////////////////////////////
// Camera Exposure Old Code
////////////////////////////

void cameraExposure() {
  // int delayTimeForInternal = ledTime[ledMode]-ledTime[e];
  // for (int i=0; i <= 6; i++) { digitalWrite(ledTrigger_high[i],
  // ledState[i]);}
  digitalWrite(externalTrigger, HIGH);
  // digitalWrite(ledTrigger_low[6], HIGH); //TODO remove after UV test
  digitalWrite(cameraTrigger, HIGH);   // trigger the camera high
  delayMicroseconds(ledTime[e]);       // wait for external exposure
  digitalWrite(externalTrigger, LOW);  // turn external LED off
  // delayMicroseconds(delayTimeForInternal); //wait for internal exposure
  // for (int i=0; i <= 6; i++) { digitalWrite(ledTrigger_high[i], LOW);} //
  // turn internal lights off digitalWrite(ledTrigger_low[6], LOW); //TODO
  // remove after UV test

  digitalWrite(cameraTrigger, LOW);  // set camera low
}
///////////////////
void cameraDelay() {
  { delay(1000 / fps - (long)ledTime[ledMode] / 1000); }
}
/////////////////////////////////

//////////////////
// Set system parameters
//////////////////

void setParameters() {
  if (mode == 'e')  // Change exposure
  {
    exposureTime = value;
    Serial.print("Exposure: ");
    Serial.println(exposureTime);
  }

  if (mode == 'p')  // Change projector exposure
  {
    projExposurePer = value;
    Serial.print("Projector exposure: ");
    Serial.println(projExposurePer);
  }

  if (mode == 'l')  // Change use_LED status
  {
    use_LED = value;
    Serial.print("Use LED: ");
    Serial.println(use_LED);
  }

  if (mode == 'c')  // Change max_current
  {
    driverAmp_max_use = float(value);
    Serial.print("Max current use: ");
    Serial.println(driverAmp_max_use);
  }
}

//////////////////
// Capture Continuous
//////////////////
void captureLiveView() {
  setCurrentDriver(driverVals[stepNum]);
  cameraDelay();
  cameraExposure();
}

void stopView() {
  digitalWrite(cameraTrigger, LOW);
  digitalWrite(externalTrigger, LOW);
}

//////////////////
// Capture Focal Stack
/////////////////

void FocalStack() {
  Serial.println("Single Focal Stack");
  Serial.print("Step Number(1-");
  Serial.print(stepTotal);
  Serial.print("):");
  if (scanRange == 0) {
    for (int stepNum = 0; stepNum < stepTotal; stepNum++)
    // for (int stepNum = 0; stepNum < endStep; stepNum++)
    {
      Serial.print(stepNum + 1);
      setCurrentDriver(driverVals[stepNum]);  // set new Optotune value
      currentReport = ((float)driverVals[stepNum] / 4095) * driverAmp_max;
      Serial.print(" (");
      Serial.print(currentReport);
      Serial.print("mA)");
      Serial.print(", ");
      cameraDelay();
      cameraExposure();
    }
  }
  if (scanRange == 1) {
    for (int stepNum = scanMin; stepNum < scanMax; stepNum++) {
      Serial.print(stepNum + 1);
      setCurrentDriver(driverVals[stepNum]);  // set new Optotune value
      currentReport = ((float)driverVals[stepNum] / 4095) * driverAmp_max;
      Serial.print(" (");
      Serial.print(currentReport);
      Serial.print("mA)");
      Serial.print(", ");
      cameraDelay();
      cameraExposure();
    }
  }
  for (int extraSteps = 0; extraSteps < 1; extraSteps++)  // extra exposure after stack is finished
                                                          // (to ensure program does not get stuck)
  {
    cameraDelay();
    cameraExposure();  // extra exposure after stack is finished
  }
}

void captureFocalSweep() {
  int stepExposure = exposureTime / stepTotal;
  int prePatternDelay = int(((100.0 - float(projExposurePer)) * float(stepExposure)) / 100.0);
  int delayFirstHalf = (stepExposure - prePatternDelay) / 2;
  int delaySecondHalf = stepExposure - prePatternDelay - delayFirstHalf;

  Serial.println("proj Exposure");
  Serial.print(projExposurePer);
  Serial.println("pre Pattern Delay");
  Serial.print(prePatternDelay);
  Serial.println("delay first half");
  Serial.print(delayFirstHalf);
  Serial.println("dealy Second Half");
  Serial.println(delaySecondHalf);

  digitalWrite(cameraTrigger, HIGH);  // trigger the camera high
  Serial.println("Camera Trigger High");

  for (int i = 0; i < stepTotal; i++) {
    setCurrentDriver(driverVals[i]);      // set new Optotune value
    delayMicroseconds(prePatternDelay);   // delay before switching to pattern
    digitalWrite(externalTrigger, HIGH);  // switch projector pattern
    // Serial.println("external Trigger high");
    if (use_LED == 1) {
      digitalWrite(ledTrigger, HIGH);  // turn LED on
    }
    // Serial.println("turn LED on");
    // currentReport = ((float)driverVals[i] / 4095) * driverAmp_max;
    // Serial.print(" ("); Serial.print(currentReport); Serial.print("mA)");
    // Serial.print(", ");
    delayMicroseconds(delayFirstHalf);   // wait for half a duty cycle
    digitalWrite(externalTrigger, LOW);  // prepare for next rising edge
    // Serial.println("external Trigger low");
    delayMicroseconds(delaySecondHalf);  // wait for half a duty cycle
    digitalWrite(ledTrigger, LOW);       // turn LED off
    // Serial.println("turn LED off");
    // delay(20); // eingefuegt um an aus des proektors zu ueberpruefen
  }

  digitalWrite(cameraTrigger, LOW);  // trigger the camera low
  // Serial.println("camera Trigger LOW");
  setCurrentDriver(driverVals[0]);  // return camera to zero step
  // Serial.println("Capture done");
}

void captureSingleStep() {
  int stepExposure = exposureTime / stepTotal;
  int prePatternDelay = int(((100.0 - float(projExposurePer)) * float(stepExposure)) / 100.0);
  int delayFirstHalf = (stepExposure - prePatternDelay) / 2;
  int delaySecondHalf = stepExposure - prePatternDelay - delayFirstHalf;

  // Serial.println(projExposurePer);
  // Serial.println(prePatternDelay);
  // Serial.println(delayFirstHalf);
  // Serial.println(delaySecondHalf);

  digitalWrite(cameraTrigger, HIGH);  // trigger the camera high
  // Serial.print("camera Trigger high");
  delayMicroseconds(prePatternDelay);  // delay before switching to pattern
  ////Serial.print(prePatternDelay);
  digitalWrite(externalTrigger, HIGH);  // switch projector pattern
  // Serial.print("Proj switch pattern");
  // currentReport = ((float)driverVals[i] / 4095) * driverAmp_max;
  // Serial.print(" ("); Serial.print(currentReport); Serial.print("mA)");
  // Serial.print(", ");
  delayMicroseconds(delayFirstHalf);  // wait for half a duty cycle
  // Serial.print("delayFirstHalf"); Serial.print(delayFirstHalf);
  digitalWrite(externalTrigger, LOW);  // prepare for next rising edge
  // Serial.print("prepare for next rising edge, external trigger low");
  delayMicroseconds(delaySecondHalf);  // wait for half a duty cycle
  // Serial.print("delaySecondHalf"); Serial.print(delaySecondHalf);
  digitalWrite(cameraTrigger, LOW);  // trigger the camera low
  // Serial.print("cameraTrigger low");
}

void advanceProjector() {
  Serial.println("Advance PROJ!");
  digitalWrite(externalTrigger, HIGH);  // switch projector pattern
  Serial.print("switch projector pattern");
  delay(1);
  digitalWrite(externalTrigger, LOW);  // prepare for next rising edge
  Serial.print("prepare for next rising edge");
}

void advanceCamera() {
  Serial.println("Advance cam");
  digitalWrite(cameraTrigger, HIGH);
  Serial.print("cameraTrigger high");
  delay(10);
  digitalWrite(cameraTrigger, LOW);  // prepare for next rising edge
  Serial.print("cameraTrigger low");
}
