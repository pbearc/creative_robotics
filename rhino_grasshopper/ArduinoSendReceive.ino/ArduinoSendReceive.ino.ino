/*
  Braccio send and receive Arduino, by Fabio D'Agnano, including the Braccio Library  by Andrea Martino.



 This example is in the public domain.
 */

#include <Braccio.h>
#include <Servo.h>

Servo base;
Servo shoulder;
Servo elbow;
Servo wrist_rot;
Servo wrist_ver;
Servo gripper;
int speed=20;


#define GRIPPER_CLOSED 85
#define GRIPPER_OPENED 20

// Variables to store positions
int currentPosition[6] = {90, 90, 90, 90, 90, 50}; // Current position of the arm

void setup() {
  Serial.begin(9600);                             // Match your Grasshopper baud rate
  Serial.println("Initializing... Please Wait");  // Start of initialization


  //Initialization functions and set up the initial position for Braccio
  //All the servo motors will be positioned in the "safety" position:
  //Base (M1):90 degrees
  //Shoulder (M2): 45 degrees
  //Elbow (M3): 180 degrees
  //Wrist vertical (M4): 180 degrees
  //Wrist rotation (M5): 90 degrees
  //gripper (M6): 10 degrees
  Braccio.begin();

  Serial.println("Initialization Complete");
}

void loop() {
  if (Serial.available() > 0) {
    String receivedData = Serial.readStringUntil('\n'); // Read until newline character
    receivedData.trim();                                // Remove leading/trailing whitespace

    int newPosition[6];
    // Parse six integers from the string
    if (sscanf(receivedData.c_str(), "%d,%d,%d,%d,%d,%d,%d", &newPosition[0], &newPosition[1], &newPosition[2], &newPosition[3], &newPosition[4], &newPosition[5], &newPosition[6]) == 7) {
      // Move the arm to the new position immediately
      speed=newPosition[6];
      Braccio.ServoMovement(speed,newPosition[0], newPosition[1], newPosition[2], newPosition[3], newPosition[4], newPosition[5]);
      
      // Update current position
      for (int i = 0; i < 7; i++) {
        currentPosition[i] = newPosition[i];
      }
      
      Serial.print("Moved to new position: ");
      Serial.println(receivedData);
      
      // Clear the serial buffer
      while (Serial.available() > 0) {
        Serial.read();
      }
    } else {
      Serial.println("Error: Invalid data format. Expected six integers separated by commas.");
    }
  }
}




