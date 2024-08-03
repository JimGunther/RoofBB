#include "Arduino.h"
#include "Chrono.h"

// *********************** Version of 02/08/2024 *******************************************
// Chrono class is a utility serving 2 different but related purposes:
// 1) it acts as a realtime clock, once fed with starter value from internet - from Comms class
// 2) it provides a variety of static methods for formatting and "date part" values of datetime,
// given an unsigned long value as input parameter
// Chrono internally stores the unix time MINUS seconds 1970-2000

Chrono::Chrono() {};
/**********************************************************************************************
begin(): sets up Chrono clock, using value from internet where available
parameters: unix2k: Unix time from internet, adjusted to year 2000 baseline - instead of 1970
returns: void
***********************************************************************************************/
void Chrono::begin(unsigned long unix2k) {
  _unix2k = unix2k;
  if (unix2k == 0) _unix2k = now();
  _ms = millis();
  _prevHour = hour();
}

/**********************************************************************************************
now(): returns calculated time now as an unsigned long
parameters: none
returns: seconds since 1/1/2000 as unsigned long
***********************************************************************************************/
unsigned long Chrono::now() {
  unsigned long secs = (millis() - _ms) / 1000UL;
  unsigned long rv = _unix2k + secs;
  return rv; 
}  // Unix value (>1/1/2000)

/************************************************************************************************
hourChanged(): checks if hour has changed since the last call (i.e. previous loop)
parameters: none
returns: boolean: true if hour changed, otherwise false
*************************************************************************************************/
bool Chrono::hourChanged() {
  bool b = (hour() != _prevHour);
  _prevHour = hour();
  return b;
}

/*************************************************************************************************
Year(): gets year from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: claculated year
**************************************************************************************************/
int Chrono::Year(unsigned long u) {
  int d2000 = u / SECS_PER_DAY;  // days since 01.01.2000
  int quads = d2000 / DAYS_PER_QUAD; // (rounded down)
  int dslq = d2000 - DAYS_PER_QUAD * quads; // days since last quad start
  int yslq = (dslq < DPY + 1) ? 0 : 1 + (dslq - DPY - 1) / DPY;  // (rounded down)
  return 2000 + quads * 4 + yslq; 
}

/*************************************************************************************************
DoY(): gets day of year from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated day of year
***************************************************************************************************/
int Chrono::DoY(unsigned long u) {
  int ys2k = Chrono::Year(u) - 2000;
  int qs2k = ys2k / 4;
  int yslq = ys2k - qs2k * 4; // must be 0-3
  int ds2k = (int)(u / SECS_PER_DAY);
  return ds2k - (yslq * DPY) - (qs2k * DAYS_PER_QUAD);  // day of year: zero-based
}

/*************************************************************************************************
Month(): gets month (1-12) from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated month
***************************************************************************************************/
int Chrono::Month(unsigned long u) { 
  int y = Chrono::Year(u);
  int doyr = DoY(u);
  bool leap = (y % 4) == 0;
  int adjust = leap && (doyr > 58) ? 1 : 0;
  int i;
  for (i = 1; i < MPY; i++) {
    if (doyr < _dd[i] + adjust) return i;
  }
  return 12;
}

/*************************************************************************************************
Date(): gets day of month from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated day of month
***************************************************************************************************/
int Chrono::Date(unsigned long u) {
  int mth = Chrono::Month(u);
  int doyr = Chrono::DoY(u);
  int m1 = _dd[mth];
  int i;
  for (i = 1; i < DPM; i++) {
    if ((doyr > _dd[i - 1]) && (doyr <= _dd[i])) return doyr - _dd[i - 1];
  }
  return doyr - _dd[11];
}

/*************************************************************************************************
Hour(): gets hour (0-23) from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated hour 
***************************************************************************************************/
int Chrono::Hour(unsigned long u) {
  int secs = u % SECS_PER_DAY;
  return (int)(secs / SECS_PER_HOUR);
}

/*************************************************************************************************
nowISO(): gets date/time now in ISO format from unsigned long input
NB this method uses an internal buffer in the Chrono class.
Use strcpy() to make a copy of this string immediately after calling this method
parameters: int: truncate: length of string to truncate to
returns: char*: calculated date/time (ISO)
***************************************************************************************************/
char* Chrono::nowISO(int truncate) {
  unsigned long unix2k = now();
  sprintf(_isoNowBuf, "%d-%02d-%02dT%02d:%02d:%02d", Year(unix2k), Month(unix2k), Date(unix2k), Hour(unix2k), Minutes(unix2k),
    Seconds(unix2k));
  if (truncate != TRUNC_NONE) {
    if (truncate == TRUNC_HOUR) strcpy(_isoNowBuf + truncate, "00:00");
    else strcpy(_isoNowBuf + truncate, "00:00:00");
  }
  return _isoNowBuf;
}

/*************************************************************************************************
Minutes(): gets minutes (0-59) from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated minutes 
***************************************************************************************************/
int Chrono::Minutes(unsigned long u) {
  int secs = u % SECS_PER_HOUR;
  return (int)(secs / SECS_PER_MINUTE);
}

/*************************************************************************************************
Seconds(): gets seconds (0-59) from unsigned long input
parameters: u: unsigned long representing seconds since 1/1/2000
returns: int: calculated seconds 
***************************************************************************************************/
int Chrono::Seconds(unsigned long u) {
  return u % SECS_PER_MINUTE;
}

/**************************************************************************************************
getIsoDate(): places ISO formatted date for now in buffer buf from day and hour data only
NB: Returns ISO date for yesterday if date/hour combination is later than time now.
parameters:
  buf: character buffer to receive data (20 bytes minimum)
  dy: int date (1-31)
  hr: int hour (0-23)
returns: ISO formatted date/time string
****************************************************************************************************/
char* Chrono::getIsoDate(char* buf, int dy, int hr) {
  unsigned long u = now();
  int y = Year(u);
  int m = Month(u);
  int d = Date(u);
  int h = Hour(u);
  int hd = d * 24 + h;
  if ((dy * 24 + hr) > hd) {  // assumes shed is asking for yesterday's data
    m--;
    if (m == 0) {
      m = 12;
      y--;
    }
    
  }
  // if now < yyyy-mm-ddThh:00:00 stored values must be for last month!

  sprintf(buf, "%d-%02d-%02dT%02d:00:00", y, m, dy, hr);
  return buf;
}

