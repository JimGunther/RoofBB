#include "Config.h"
#include "Arduino.h"
#include "Sensors.h"

// --------------------------------------- Version of 30/07/2024 ------------------------------------------
// Sensors class acts as the interface between 4 I2C sensors and the main ino code
Sensors::Sensors() : _aht(), _bmp()  {};

/**********************************************************************************************************
begin(): initializes the Sensors object: sets all _results (realtime), _hesults (hourly),  _desults (daily) values to zero,
initializes I2C sensors and stores status of each sensor: _sensorStatus of 15 means NO sensors and sets "unplugged" flag
"Unplugged" invokes random number generation in place of real values and will need to be disabled at some time soon.
parameters: none
returns: int: the value of _sensorStatus
***********************************************************************************************************/
int Sensors::begin() {
  bool bBMP, bAHT, bBHa, bBHb;
  _results.temperature = 0;
  _results.humidity = 0;
  _results.pressure = 0;
  _results.lightA = 0;
  _results.lightB = 0;
  Serial.println();
  
  // Initialise the four I2C sensors
  Serial.print("Sensor status: ");
  _sensorStatus = 0;
  bBMP = _bmp.begin();
  if (!bBMP) _sensorStatus = 1;
  bAHT = _aht.begin();
  if (!bAHT) _sensorStatus += 2;
  bBHa = _bh1750a.begin();
  if (!bBHa) _sensorStatus += 4;
  bBHb = _bh1750b.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5c);
  if (!bBHb) _sensorStatus += 8;
  return _sensorStatus;
}

/********************************************************************************************************
update AHT(): The AHT sensor is read every 10 seconds (Zone40) and values stored in 2 _result fields (temperature and humidity)
parameters: none
returns: boolean: true if actual results, false if random numbers
*********************************************************************************************************/
bool Sensors::updateAHT() {
  sensors_event_t humidity, temp;
  bool rv = false;
  if((_sensorStatus & 1) == 0) {
    if (_aht.getEvent(&humidity, &temp)) {
      _results.humidity = (int)(humidity.relative_humidity + 0.5f);  // round to int
      _results.temperature = (int)(temp.temperature + 0.5f); // round to int
      rv = true;
    }
  } else {    //do random stuff
    unsigned long r = random(100);
    _results.humidity = (int)r % 100;
    _results.temperature = 5 + (int)r % 20;
    rv = false;
  }
  return rv;
}

/***************************************************************************************************
update BMP(): The BMP sensor is read every 10 seconds (Zone40) and values stored in _result field pressure
parameters: none
returns: boolean: true if actual results, false if random
****************************************************************************************************/
bool Sensors::updateBMP() {
  float p;
  if ((_sensorStatus & 2) == 0) {
    _bmp.getPressure(&p);
    _results.pressure = (int)(0.01f * p);
    return true;
  } else {
    //Serial.print("Random pressure ");
    unsigned long r = random(40);
    _results.pressure = 980 + (int)r;
    return false;
  }
}

/********************************************************************************************************
updateBH1750(): places the current readings of the light sensors in the _result struct: adapted for 2 light sensors
parameters: none
returns: byte: _sensorStatus & 12: values 0 (both real), 4 (A random, B real), 8 (A real, B random) or 12 (both random)
*********************************************************************************************************/
byte Sensors::updateBH1750() {
  float output;
  
  if ((_sensorStatus & 4) == 0) {
    output = _bh1750a.readLightLevel();
    if (output < 0) _results.lightA = 0;
    else _results.lightA = (int)(20.0 * log(1.0f + output)); // may need rescaling
  }
  else {  // "random" mode
    unsigned long r = random(100); // arbitrary shift
    int ir = (int)r;
    _results.lightA = ir;
  }
if ((_sensorStatus & 8) == 0) {
    output = _bh1750b.readLightLevel();
    if (output < 0) _results.lightB = 0;
    else _results.lightB = (int)(20.0 * log(1.0f + output)); // may need rescaling
  }
  else {  // "random" mode
    unsigned long r = random(100); // arbitrary shift
    int ir = (int)r;
    _results.lightB = ir;
  }

  return (byte)_sensorStatus & 12;
}

/****************************************************************************************************
makeCSV(): realtime and hourly CSV results to buf
parameters:
  vals: sens structure containing realtime or hourly results
  buf: char* character buffer address to receive CSV
returns: boolean: always true
*****************************************************************************************************/
bool Sensors::makeCSV(sens vals, char *buf) {
  sprintf(buf, ",%04d,%04d,%04d,%04d,%04d,", vals.temperature, vals.humidity, vals.pressure, vals.lightA, vals.lightB);
  return true;
}

/****************************************************************************************************
getCSVRT(): put RT values into designated buffer buf
parameters: buf: char* character buffer address to receive CSV
returns: void
*****************************************************************************************************/
void Sensors::getCSVRT(char* buf) {
  makeCSV(_results, buf);
}

/***************************************************************************************************
storeHrResults(): method to copy realtime values into relevant day and hour array element
parameters:
  hr: int hour (0-23)
returns: void
****************************************************************************************************/
void Sensors::storeHrResults(int hr) {
  // Simply re-use realtime figures for all sensors
  _hesults[hr].temperature = _results.temperature;
  _hesults[hr].humidity = _results.humidity;
  _hesults[hr].pressure = _results.pressure;
  _hesults[hr].lightA = _results.lightA;
  _hesults[hr].lightB = _results.lightB;
}

/************************************************************************************************
getCSVHour(): formats hourly values as CSV and places into character buffer
parameters:
  dy: int day (1-31)
  hr: int (0-23)
  buf: char* character buffer address
returns: void
*************************************************************************************************/
void Sensors::getCSVHour(int hr, char* buf) {
  makeCSV(_results, buf); // NB: hourly sensors data are just the realtime values
}

