#ifndef RAINWIND_H
#define RAINWIND_H

#include "Arduino.h"

// structure to hold eastings and northings for each compass point
/*struct eastNorth {
  float east;
  float north;
};*/

// Structure used to hold windrain data
struct wr {
  int buckets;  // tips since midnight
  int revs3;  // revs in last 3 seconds
  int maxRevs;  // gust measure (3 secs)
  int ana128; // WD analogue sensor reading / 128
  //int anaRevs[NUM_ANALOG];
};

// struct to hold hourly BACKUP data
struct wrHr {
  int bucketsHr;
  int revsHr;
  int gustHr;
};
/*
struct wrDay {
  int totalBuckets;
  int totalRevs;
  int maxGustRevs;
};
*/
// ----------------------------------------------------------------------------------------------------------
//-------------------------------------- Version of 18.07.2024 ----------------------------------------------

// Class RainWind(): interface with the wind and rain detectors

class RainWind {

  public:
  RainWind();
  void begin(int bootHr);
  //int pollIndex();
  int onWDUpdate();
  void updateRevs();
  void updateBucketTips();
  void getCSVRT(char* buf);
  void getCSVHour(int hr, char* buf);
  void getCSVDay(char* buf);
  void storeHrResults(int hr);
  //void storeDayResults(/*int dy*/);

  private:
  void resetDay();
  void resetHour(int h);
  void initResults();
  int getAnalog();
  bool makeCSV(wr vals, char* buf);
  bool makeCSVHr(wrHr vals, char *buf);
  //bool makeCSVDay(wrDay vals, char* buf);
  
  // local (private) variables
  int _prevTips;
  int _hrRevs;
  int _maxGustRevs;
  int _gustHr;

  //int _prevAnalog; // previous analog value (0 - 4095)
  int _currAnalog;
  int _ixPoll;
  int _prevBuckets;
  wr _results;
  wrHr _hesults[HPD];
  //wrDay _desults;
  int _pollRevs[POLL_COUNT];
};

#endif