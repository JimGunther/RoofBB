#include "Config.h"
#include "Arduino.h"
#include "RainWind.h"

// ------------------------------ Version of 21/08/2024 ---------------------------------

// Interrupt Service Routines start here______________

// Rain

volatile unsigned long _lastRTime  = 0;
volatile int _cumTipsCount;
volatile int _hrTipsCount; // number of rain bucket tips (cumulative per hour)
const int _margin = 5;  // minimum milliseconds between checks: insurance against contact bounce: ?? STILL NEEDED FOR HALL EFFECT SENSORS???  

void ICACHE_RAM_ATTR buckets_tipped();
void buckets_tipped() {
unsigned long thisRTime = millis();
  if (thisRTime - _lastRTime > _margin) {
    _cumTipsCount++;
    _hrTipsCount++;
    _lastRTime = thisRTime;
  }
}

// Wind 
volatile int _gustCounter = 0;
volatile int _currRevs = 0;
volatile int _prevRevs = 0;
volatile unsigned long _lastSTime = 0;
volatile unsigned long _thisSTime;

void ICACHE_RAM_ATTR one_Rotation();
void one_Rotation() {
  _thisSTime = millis();
  if (_thisSTime - _lastSTime > _margin) {
    if (digitalRead(RevsPin) == LOW)
    {
       _currRevs++;
       _gustCounter++;
    }
    _lastSTime = _thisSTime;
  }
}

// -------------------------------------------------------------------------------------------------------

// RainWind class acts as the interface between rain and wind measurement devices and the main ino code
RainWind::RainWind() {};

/*********************************************************************************************************
begin(): initiates RainWind object: attaches 2 interrupts, sets pin modes and calls 3 "reset" methods
parameters: none
returns: void
**********************************************************************************************************/
void RainWind::begin() {
  attachInterrupt(digitalPinToInterrupt(RainPin), buckets_tipped, CHANGE); // rain buckets
  attachInterrupt(digitalPinToInterrupt(RevsPin), one_Rotation, CHANGE);  // anemometer
  
  //set pin modes
  pinMode(RainPin, INPUT_PULLUP); 
  pinMode(RevsPin, INPUT_PULLUP);
  pinMode(WDPin, INPUT_PULLUP);
  
  for ( int hr = 0; hr < 24; hr++ ) )
    resetHour( hr );
  }
  _results.maxRevs = 0;
}

/***********************************************************************************************************
resetHour(hr): resets "hourly" variables to zero
paramters:
  hr: int: hour (0-23) to be reset
returns: void
************************************************************************************************************/
void RainWind::resetHour(int hr) { // STILL NEEDED I THINK! MAYBE NOT AFTER ResetHour reinstated
  _prevTips = _hrTipsCount;
  _hrTipsCount = 0;
  _hrRevs = 0;
  _gustHr = 0;
  _hesults[hr].bucketsHr = 0;
  _hesults[hr].gustHr = 0;
  _hesults[hr].revsHr = 0;
}

// Various methods to update values in "real time" zones -----------------------------------------

/*************************************************************************************************
onWDUpdate(): adds revs count since last call to the total for the wind direction (called every 3 secs)
parameters: none
returns: int: the analog reading / 128 (0-31)
**************************************************************************************************/
int RainWind::onWDUpdate() {
  int revs;
  _currAnalog = getAnalog();
  _results.ana128 = _currAnalog; 
  return _results.ana128;
}

/**************************************************************************************************
getAnalog(): returns current vane analogur value (0 - 4095)
parameters: none
returns: int: wind direction analogue value (0 - 4095) 
***************************************************************************************************/
int RainWind::getAnalog() {
  return analogRead(WDPin);  // this produces analog values between 0 and 4095
}
/*
// 8-pin version
int WDPosition(int inVal) {
  int val = inVal;
  int d, m, x = 0;
  for (m = 1; m < 255; m = m << 1) {
    if (m & val) {
      break;
    }
    x++;
  }
  x = x << 1; //double it
  if (val & 1) val += 256;
  d = val << 1;
  if (val & d) x += 1;
  return x;
}
*/
/**************************************************************************************************
updateRevs(): results stored in one of 12 array posistions (12 == 3 secs speed measurement interval / 0.25 secs poll interval)
(polled 4 times a second to catch gusts)
parameters: none
returns: void
***************************************************************************************************/
void RainWind::updateRevs() { 
  int revsNow = _currRevs; // from last interrupt
  int revsInc = revsNow - _pollRevs[_ixPoll];
  revsInc = max(0, revsInc);
  _results.revs3 = revsInc;
  _hrRevs += revsInc;
  _pollRevs[_ixPoll] = revsNow;

  if (revsInc > _results.maxRevs) {
    _results.maxRevs = _results.revs3;
  }

  if (revsInc > _gustHr) {
    _gustHr = revsInc;
  }

  _ixPoll = (_ixPoll + 1) % POLL_COUNT;
}

/*************************************************************************************************
updateBucketTips(): stores the current value of volatile _cumTipsCount
parameters: none
returns: void
**************************************************************************************************/
void RainWind::updateBucketTips() {
  _results.buckets = _cumTipsCount; // cumulates for whole day
}

/*************************************************************************************************
storeHrResults(): puts rain and wind results into relevant element of _hesults array
parameters:
  hr: int: hour (0-23)
returns: void
**************************************************************************************************/
void RainWind::storeHrResults(int hr) {
  _hesults[hr].bucketsHr = _hrTipsCount - _prevTips;
  _hesults[hr].revsHr = _hrRevs;
  //_hrTipsCount = 0;
  _hesults[hr].gustHr = _gustHr;
}

/***************************************************************************************************
getCSVRT(): puts realtime values into CSV buffer rtBuf
parameters: char* realtime buffer address
returns: void
****************************************************************************************************/
void RainWind::getCSVRT(char *rtBuf) {
  makeCSV(_results, rtBuf);
}

/**************************************************************************************************
makeCSV(): converts integer values in wr struct to CSV string (character field width 4 per item)
parameters:
  vals: a wr structure to hold the RT and hourly values
  buf: char*: character buffer to hold string: buffer length BUF_LEN (currently 84)
returns: boolean: always true
***************************************************************************************************/
bool RainWind::makeCSV(wr vals, char *buf) {
  sprintf(buf, ",%04d,%04d,%04d,%04d", vals.buckets, vals.revs3, vals.maxRevs, vals.ana128);
  return true;
}

/**************************************************************************************************
makeCSVHr(): converts integer values in wr struct to CSV string (character field width 4 per item)
parameters:
  vals: a wrHr structure to hold the hourly values
  buf: char*: character buffer to hold string: buffer length BUF_LEN (currently 84)
returns: boolean: always true
***************************************************************************************************/
bool RainWind::makeCSVHr(wrHr vals, char *buf) {
  sprintf(buf, ",%04d,%04d,%04d,%04d", vals.bucketsHr, vals.revsHr, vals.gustHr, NUL_WD);
  return true;
}

/**************************************************************************************************
getCSVHour(): takes values from requested hr wr array item and converts to CSV and stores into buf
parameters:
  hr: int: hour (0-23)
  buf: char*: pointer to character buffer to hold CSV string: length BUF_LEN (currently 84)
returns: void
***************************************************************************************************/
void RainWind::getCSVHour(int hr, char *buf) {
  makeCSVHr(_hesults[hr], buf);
}
