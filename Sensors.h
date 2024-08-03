#ifndef SENSORS_H
#define SENSORS_H

#include "Arduino.h"

#include <Wire.h>
#include <Adafruit_BMP085_U.h>
#include <Adafruit_AHTX0.h>
#include <BH1750.h>

struct sens {
  int temperature;
  int humidity;
  int pressure;
  int lightA;
  int lightB;
};

#define MIN_BAR 0.05

// ----------------------------------------------------------------------------------------------------------

class Sensors {
  public:
  Sensors();
  int begin();
  bool updateAHT();
  bool updateBMP();
  byte updateBH1750();
  void getCSVRT(char* buf);
  void getCSVHour(int hr, char* buf);
  void storeHrResults(int hr);

  private:
  // Nested classes
  Adafruit_AHTX0 _aht;
  Adafruit_BMP085_Unified _bmp;
  BH1750 _bh1750a;
  BH1750 _bh1750b;  
  
  bool makeCSV(sens vals, char *buf);

  unsigned long int _prevTime;
  int _sensorStatus;  
  sens _results;
  sens _hesults[HPD];

};
#endif