#include "Config.h"
#include "RainWind.h"
#include "Sensors.h"
#include "Comms.h"
#include <WiFi.h>
#include <PubSubClient.h>
//=============================================== Version of 21/08/2024 ========================================================
// Status: NEW "Bare Bones" version requiring major simplification: corresponding changes need to Shed 
// RoofBB.ino: sketch to interface with all sensors and counters and send results in CSV form at
// frequent intervals (currently 3 secs) to Shed.
// Also sends hourly on prompting from shed processor (catchup only) via MQTT Wifi link
// Designed for ESP32

// struct hdc acts as a kind of "primary key" unique identifier for each "package" of weather data (realtime, hourly or daily)

struct hdc {
  int day;
  int hour;
  char hdr;
};
// ------------------------------------------ MQTT COMMS ------------------------------------------------------------------
// NB MQTT libraries require instances in global space

// ASSUME (FOR NOW) ALL MQTT REMAINS THE SAME
// MQTT variables come first
WiFiClient espClient;
PubSubClient qtClient(espClient);
int nwkIx;
bool bNewMessage;
unsigned int icLength;
byte bqticBuf[QT_LEN];
char qticBuf[QT_LEN];
char qtogBuf[QT_LEN];
char mqttServer[IP_LEN];

/********************************************************************************************************************
qtCallback(): Callback function for MQTT Client: receives i/c MQTT message from Shed
parameters:
  topic: string containing "ws/shedRequests", otherwise ignored
  message: byte array (ASCII) with message
  length: i/c message length
returns: void
**********************************************************************************************************************/
void qtCallback(char* topic, byte* message, unsigned int length) {
  if (strcmp(topic, "ws/shedRequests") == 0) {
    icLength = length;
    for (int i = 0; i < length; i++) {
      bqticBuf[i] = message[i];
    }
  bNewMessage = true;
  }
}

/*********************************************************************************************************************
qtSetup(): sets up MQTT connection
parameters:none
returns: boolean True for success, False for failure
**********************************************************************************************************************/
bool qtSetup() {
  switch (nwkIx) {
    case 0:
      strcpy(mqttServer, SHED_IP);
      break;
    case 1:
      strcpy(mqttServer, HOME_IP);
      break;
    case 2:
      strcpy(mqttServer, RICH_IP);
      break;
  }

  qtClient.setServer(mqttServer, 1883);
  qtClient.setCallback(qtCallback);
  return qtReconnect();
}

/*********************************************************************************************************************
qtReconnect(): does the actual connection to MQTT broker (3 attempts)
parameters: none
returns: boolean: True for success, False for failure
**********************************************************************************************************************/
bool qtReconnect() {
  // Loop until we're reconnected
  int numTries = 0;

  while (!qtClient.connected() && (numTries++ < 3)) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (qtClient.connect("misRoof")) {
      Serial.println("connected");
      // Subscribe
      qtClient.loop();
      qtClient.subscribe("ws/shedRequests");
    }
    else {
      Serial.print("failed, rc=");
      Serial.print(qtClient.state());
      Serial.println(" try again in 3 seconds");
      // Wait 3 seconds before retrying
      delay(3000);
    }
  }
  
  return qtClient.connected();
}
// LEAVE THE ABOVE ALONE! (24/06/2024)
// ------------------------------------------------------------------------------------------------
// Instances of classes in local libraries
RainWind rainWind;
Sensors sensors;
Comms comms;

// global variables: REVIEWED 01/08
int loopCount;
unsigned long loopStart;
unsigned long loopEnd;
bool _bUnplugged;
int volts;
char dummy[BUF_LEN] = ",0,0,0,0,0,0,0,0,0,0";
char rtBuf[BUF_LEN];
char hrBuf[BUF_LEN];
char isoBoot[ISO_LEN];  // boot time in ISO format
char latestHr[ISO_LEN];
char latestDay[ISO_LEN];

/**********************************************************************************************************
setup(): runs once at startup: sets up comms, clock (Chrono), rainwind and sensions instantiation, MQTT, [seeds random() if "unplugged"]
***********************************************************************************************************/
void setup() {
  Serial.begin(115200);
  pinMode(LEDPin, OUTPUT);
  comms.begin();
  nwkIx = comms.nwkIndex();
  unsigned long u = comms.timeStamp();
  sensors.begin();
  rainWind.begin();
  pinMode(VoltsPin, INPUT);

  int my_count = 0;
  while ( !qtSetup ) {
    Serial.println("MQTT setup failed. No MQTT comms. Check RPi is powered and running.");
    digitalWrite(LEDPin, !digitalRead(LEDPin));
    delay(800);
    if ( my_count++ == 11 } ESP_restart();
  }

  loopCount = 0;
  
  if (_bUnplugged) {
    randomSeed(millis() & 0xffff);
    Serial.print("ESP is unplugged: random mode. ");
  }
  strcpy(latestHr, "2024-01-01T00:00:00");  //arbitrary date before now
  strcpy(latestDay, "2024-01-01T00:00:00");
  
  // Start with a nice empty i/c Buffer
  flushICBuffer();


  postMessage("RoofBB ver 21/08/2024: Roof setup finished."); 
}

/************************************************************************************************************
loop(): runs continuously, looping every 0.25 seconds with slower "zones": see details in comments below
*************************************************************************************************************/
void loop() {
  bool bHDCSent = false; //reset at start of each loop
  byte actFlag = 0;
  loopStart = millis();
  qtClient.loop();

  // Loop timing zones start here
  
  // ZONE 1: EVERY LOOP (1/4 sec) ----------------------------------------------------------------- 
  rainWind.updateRevs(); // 4 times/sec to catch gusts
  // END ZONE 1 -----------------------------------------------------------------------------------
  
  //ZONE 4: EVERY 4 LOOPS (1 sec) ---------------------------------------------------------
  if ((loopCount % ZONE4) == 0) {
    rainWind.updateBucketTips();
    actFlag += 1;
    // SAVE HOURLY DATA DELETED HERE
    // CHECK IF SHED WANTS DATA: 
    hdc hd1 = shedRequested();
    if (hd1.day != 0) {  // by Shed
      Serial.print("Shed req");Serial.print(hd1.hdr);Serial.print(hd1.day);Serial.print(":");Serial.println(hd1.hour);  // TEMP
      actFlag += 4;
    }
  }
  // END ZONE 4 -----------------------------------------------------------------------------------
  
  // ZONE 12: EVERY 12 LOOPS (3 secs) -------------------------------------------------------------
  if ((loopCount % ZONE12) == 0) {
    rainWind.onWDUpdate();
    actFlag += 8;
    if (!qtReconnect()) {
      actFlag += 32;
    } // checks connection and attempts retry if none
    if (!bHDCSent) { // don't send RT if hourly, daily or catchup CSV string has been sent this loop
      getAndPostRT();
      actFlag += 64;
    }
    digitalWrite(LEDPin, !digitalRead(LEDPin)); // blink
  }

  // ZONE 40: EVERY 40 LOOPS (10 secs) ------------------------------------------------------------
  if ((loopCount % ZONE40) == 0) {
    // update sensor results
    bool b = sensors.updateAHT();
    bool bz = sensors.updateBMP();
    byte by = sensors.updateBH1750();
    actFlag += 128;
  }
  // END ZONE 40 ----------------------------------------------------------------------------------

  // ZONE SLOWEST: EVERY MAX_LOOP_COUNT LOOPS (30 secs)
  if (loopCount == 0) {
    // REVIEW BELOW
    volts = checkBattery();
  }
  
  //Loop timing zones end here
  
  // End-of-loop timing code
  loopEnd = millis();
  if ((loopEnd - loopStart) > LOOP_TIME) { // Code took over LOOP_TIME
    char mBuf[BUF_LEN];
    sprintf(mBuf, "Long loop time: %ul; Flag: %x", loopEnd - loopStart, actFlag);
    postMessage(mBuf);
  }
  else {  // wait until LOOP_TIME has elapsed
    while(millis() - loopStart < LOOP_TIME) {
      delay(1);
    }
  }
  loopCount = (loopCount + 1) % MAX_LOOP_COUNT;
  // END OF LOOP
}
// --------------------------------- OTHER HELPER FUNCTIONS ---------------------------------------------------------

/********************************************************************************************************************
postCSV(): post CSV using contituent parts already calculated
parameters:
  ch: header char
  isoDateSaved: ISO formatted date string
  csv : string containing CSV "raw" values
returns: void
*********************************************************************************************************************/
void postCSV(char ch, const char* csv) {
  char buf[BUF_LEN];
  sprintf(buf, "%c%s%02d", ch, csv, volts);  // analog read of volts pin added 21/06/2024
  qtClient.loop();
  qtClient.publish("ws/csv", buf, false);
  if (buf[0] != 'R'){ Serial.print("Published: "); Serial.println(buf); }
}

/********************************************************************************************************************
postMessage(): post message verbatim, just adding 'M' and current date (ISO) to the front
parameters:
  message: string containing message
returns: void
*********************************************************************************************************************/
void postMessage(const char* mess) {
  char buf[BUF_LEN];
  buf[0] = 'M';
  strcpy(buf + 1, mess);
  qtClient.publish("ws/messages", buf, false); 
}

/*******************************************************************************************************************
getAndPostRT(): gathers in and posts 2x CSV half-strings from the RainWind and Sensors objects ready to send to Shed
parameters: none
returns: boolean: always true
********************************************************************************************************************/
bool getAndPostRT() {
  rainWind.getCSVRT(rtBuf);
  //Serial.println(rtBuf + 15); // TEMP!!!
  int len = strlen(rtBuf);
  sensors.getCSVRT(rtBuf + len);
  postCSV('R', rtBuf);
  return true;
}


/************************************************************************************************************
shedRequested(): confirms Shed wants hourly data and returns a struct hdc object. No request iff hd.day == 0
parameters: none
returns: hdc structure (hour, day, header character): day ==0 signifies no request
*************************************************************************************************************/
hdc shedRequested() { 
  hdc hd1;
  if(!bNewMessage) {
    hd1.day = 0;
    return hd1;
  }
  // Message received by here  
  if (icLength != HRREQ_LEN) {
    hd1.day = 0;
    postMessage("Shed request rejected: wrong length");
    bNewMessage = false;
    return hd1;
  }
  for (int i = 0; i < icLength; i++) qticBuf[i] = (char)bqticBuf[i];
  qticBuf[icLength] = '/0'; // zero terminated!

  hd1.hdr = qticBuf[0]; // at least one character: Header
  if (hd1.hdr == 'H') { // valid header
    // Shed must send message in format "DddHdd": 
    hd1.day = 10 * (qticBuf[1] - '0') + qticBuf[2] - '0';
    hd1.hour = 10 * (qticBuf[4] - '0') + qticBuf[5] - '0';
  }
  else { // no valid character
    hd1.hour = 0;
    postMessage("Shed request header not 'H': ");
  }
  
  flushICBuffer(); // empty buffer, because relevant info is now stored in struct hd
  bNewMessage = false;
  return hd1;
}

// UNDER REVIEW BELOW
void flushICBuffer() {
}

// checkBattery():
int checkBattery() {
  return analogRead(VoltsPin);
}
