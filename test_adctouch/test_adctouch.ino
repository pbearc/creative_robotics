#include <Braccio.h>
#include <Servo.h>
#include <ADCTouch.h>

Servo base, shoulder, elbow, wrist_rot, wrist_ver, gripper;
int speed = 20;

#define GRIPPER_CLOSED 85
#define GRIPPER_OPENED 20

// Variables to store positions
int currentPosition[6] = {90, 90, 90, 90, 90, 50}; // Current position of the arm

// Touch sensing variables
const int sensorPins[] = {A0, A1, A2, A3, A4, A5};
const int numPins = 6;
int refValues[numPins];
const int thresholdHigh = 200;
const int thresholdLow = 200;
const int sampleCount = 150;

bool pinState[numPins];
bool lastPinState[numPins];

const bool debugMode = true;
unsigned long lastDebugTime = 0;
const unsigned long debugInterval = 1000;

void setup() {
  Serial.begin(9600);
  Serial.println("Initializing... Please Wait");

  // Initialize Braccio
  Braccio.begin();

  // Calibrate touch sensors
  Serial.println("Calibrating touch sensors...");
  for (int i = 0; i < numPins; i++) {
    refValues[i] = ADCTouch.read(sensorPins[i], 1000);
    pinState[i] = false;
    lastPinState[i] = false;
    Serial.print("Pin A");
    Serial.print(i);
    Serial.print(" calibrated: ");
    Serial.println(refValues[i]);
  }

  Serial.println("Initialization Complete");
  Serial.println("TOUCH_SYSTEM_READY");
}

void loop() {
  // Handle Braccio arm control
  if (Serial.available() > 0) {
    String receivedData = Serial.readStringUntil('\n');
    receivedData.trim();

    int newPosition[7];
    if (sscanf(receivedData.c_str(), "%d,%d,%d,%d,%d,%d,%d", &newPosition[0], &newPosition[1], &newPosition[2], 
               &newPosition[3], &newPosition[4], &newPosition[5], &newPosition[6]) == 7) {
      speed = newPosition[6];
      Braccio.ServoMovement(speed, newPosition[0], newPosition[1], newPosition[2], newPosition[3], newPosition[4], newPosition[5]);
      
      for (int i = 0; i < 6; i++) {
        currentPosition[i] = newPosition[i];
      }
      
      Serial.print("Moved to new position: ");
      Serial.println(receivedData);
      
      while (Serial.available() > 0) {
        Serial.read();
      }
    } else {
      Serial.println("Error: Invalid data format. Expected seven integers separated by commas.");
    }
  }

  // Handle touch sensing
  for (int i = 0; i < numPins; i++) {
    int value = ADCTouch.read(sensorPins[i], sampleCount);
    int difference = value - refValues[i];
    
    pinState[i] = (difference > thresholdHigh) || (abs(difference) > thresholdLow && difference < 0);
    
    if (pinState[i] && !lastPinState[i]) {
      Serial.print("PLAY_SOUND:");
      Serial.println(i);
    }
    
    lastPinState[i] = pinState[i];
  }
  
  // Debug output for touch sensing
  if (debugMode && (millis() - lastDebugTime > debugInterval)) {
    lastDebugTime = millis();
    Serial.println("---Touch Values---");
    for (int i = 0; i < numPins; i++) {
      int value = ADCTouch.read(sensorPins[i]);
      int difference = value - refValues[i];
      Serial.print("A");
      Serial.print(i);
      Serial.print(": ");
      Serial.print(difference);
      Serial.print(" (");
      if (difference > thresholdHigh || (abs(difference) > thresholdLow && difference < 0)) {
        Serial.print("TOUCH");
      } else {
        Serial.print("no touch");
      }
      Serial.println(")");
    }
    Serial.println("-----------------");
  }
  
  delay(30);
}
