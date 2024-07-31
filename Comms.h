#ifndef COMMS_H
#define COMMS_H
#include <WiFi.h>
#include "Config.h"

class Comms {
  
  public:
  Comms();
  void begin();

  bool readCredentials(); // gets "menu" of wifi networks from code
  bool connectToWiFi();
  unsigned long timeStamp() { return _tt; }
  int getStatus() { return _status; }
  int nwkIndex();
  const char* getIP() { return _ipAddress; }
  private:
  unsigned long calculateTime();
  
  unsigned long _tt;
  int _status;
  int _nwkIx;
  
  char _ssid[NUM_NETWORKS][SSID_LEN];
  char _pwd[NUM_NETWORKS][PWD_LEN];
  char _ssidChosen[SSID_LEN], _pwdChosen[PWD_LEN];
  char _ipAddress[IP_LEN];  
  
};
#endif
