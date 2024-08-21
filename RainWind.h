#ifndef RAINWIND_H
#define RAINWIND_H

#include "Arduino.h"

// Structure used to hold windrain data
struct wr {
  int buckets;  // tips since midnight
  int revs3;  // revs in last 3 seconds
  int maxRevs;  // gust measure (3 secs)
  int ana128; // WD analogue sensor reading 
};

// struct to hold hourly BACKUP data
struct wrHr {
  int bucketsHr;
  int revsHr;
  int gustHr;
};
// ----------------------------------------------------------------------------------------------------------
//-------------------------------------- Version of 21.08.2024 ----------------------------------------------

// Class RainWind(): interface with the wind and rain detectors

class RainWind {

  public:
  RainWind();
  void begin();
  int onWDUpdate();
  void updateRevs();
  void updateBucketTips();
  void getCSVRT(char* buf);
  void getCSVHour(int hr, char* buf);
  void storeHrResults(int hr);

  private:
  //void resetDay();
  void resetHour(int h);
  //void initResults();
  int getAnalog();
  bool makeCSV(wr vals, char* buf);
  bool makeCSVHr(wrHr vals, char *buf);
  
  // local (private) variables
  int _prevTips;
  int _hrRevs;
  int _gustHr;
  int _currAnalog;
  int _ixPoll;
  wr _results;
  wrHr _hesults[HPD];
  int _pollRevs[POLL_COUNT];
};

#endif