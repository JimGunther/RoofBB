#ifndef CHRONO_H
#define CHRONO_H

#include "Arduino.h"
#include "Config.h"

/* Chrono: class to add Clock functionality to Roof processor
*/
#define TRUNC_NONE 0
#define TRUNC_HOUR 14
#define TRUNC_DAY 11
#define SECS_PER_DAY 86400
#define SECS_PER_HOUR 3600
#define SECS_PER_MINUTE 60
#define MINS_PER_HOUR 60
#define DAYS_PER_QUAD 1461

class Chrono {

  public:
  Chrono();
  void begin(unsigned long unix = 0L);
  unsigned long now();
  int Year(unsigned long u);
  int Month(unsigned long u);
  int Date(unsigned long u);
  int DoY(unsigned long u);
  int Hour(unsigned long u);
  int date(){ return Date(now()); };
  int hour(){ return Hour(now()); };
  char* nowISO(int truncate);

  bool hourChanged();
  char* getIsoDate(char* buf, int dy, int hr);
  
  private:
  unsigned long _unix2k;
  unsigned long _ms;
  int _dd[MPY] = { 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334 };
  int Minutes(unsigned long u);
  int Seconds(unsigned long u);

  char _isoNowBuf[ISO_LEN];
  
  int _prevHour, _prevMin, _thisHour;

};

#endif