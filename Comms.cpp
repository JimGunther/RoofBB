#include "Comms.h"
#include "Arduino.h"

// class Comms: responsible for wifi (but not MQTT) communications
// Also reads stored Wifi login credentials

// -------------------------------- Version of 02/08/2024 --------------------------------------------
Comms::Comms() {};  // empty constructor

/*****************************************************************************************************
begin(): initiation code for Comms object: connects to Wifi and sets Clock from the internet
parameters: none
returns: void
******************************************************************************************************/
void Comms::begin() {
  // Set WiFi to station mode and disconnect from an AP if it was previously connected.
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  readCredentials();  // gets all networks' router credentials
  //Serial.println("Preferences read.");
  if (!connectToWiFi()) {
    _status = 1;
    Serial.println("WiFi connection failed.");
    return;
  }
  _tt = calculateTime();
  if (_tt == 0UL) {
    Serial.println("Unable to get time from internet.");
    _status = 2;
  }
  else _status = 0;
}

/********************************************************************************************************
connectToWiFi(): scans wifi networks and choose a match with Shed or Home
parameters: none
Returns: boolean: true if successful
*********************************************************************************************************/
bool Comms::connectToWiFi() {
  WiFi.mode(WIFI_STA);
  Serial.print("WiFi Connecting...");
  // Scan and choose network to connect
  WiFi.disconnect();
  int nn = WiFi.scanNetworks();
  if (nn > 0) {
    int i, j;
    for (i = 0; i < nn; i++) {
      for (j = 0; j < NUM_NETWORKS; j++) {
        if (strcmp(WiFi.SSID(i).c_str(), _ssid[j]) == 0) {
          strcpy(_ssidChosen, _ssid[j]);
          strcpy(_pwdChosen, _pwd[j]);
          _nwkIx = j;
        }
      }
    }
  }
  else return false;
  
  // Now attempt connection to chosen network
  int numTries = 0;
  WiFi.disconnect();
  WiFi.begin(_ssidChosen, _pwdChosen);
  WiFi.waitForConnectResult();
  while ((WiFi.status() != WL_CONNECTED) && numTries++ < 5) {
    delay(100);
  }
  //Serial.print("Status: "); Serial.println(WiFi.status());
  Serial.print("WiFi connected. IP Address: ");
  strcpy(_ipAddress, WiFi.localIP().toString().c_str());
  Serial.println(_ipAddress); // this is IP address for HUB, NOT MQTT server!
  return true;
}

/***************************************************************************************************
nwkIndex(): reports which Wifi was found
parameters: none
returns: int: index of found network
*****************************************************************************************************/
int Comms::nwkIndex() {
  return _nwkIx;
}

/*****************************************************************************************************
readCredentials(): reads the login credentials of allowed Wifi networks
parameters: none
returns: boolen: always true
******************************************************************************************************/
// readPreferences():          
bool Comms::readCredentials() {
  strcpy(_ssid[0], SHED_SSID);
  strcpy(_pwd[0], SHED_PWD);
  strcpy(_ssid[1], HOME_SSID);
  strcpy(_pwd[1], HOME_PWD);
  strcpy(_ssid[2], RICH_SSID);
  strcpy(_pwd[2], RICH_PWD);
  return true;
}

/*****************************************************************************************************
calculateTime(): returns unsigned long int (Unix time) from website
parameters: none
returns: unsigned long integer representing time (seconds since 1/1/2000) if successful, 0 otherwise
******************************************************************************************************/
 unsigned long Comms::calculateTime() {
  const int DPQ = 1461; // days per quadyear
  const int SPD = 86400;
  const int SPH = 3600;
  const int SPM = 60;
  // setup this after wifi connected
  delay(100);
  configTime(0, 0, "europe.pool.ntp.org");
  struct tm timeinfo;
  Serial.println("Please be patient. This sometimes takes several seconds:");
  while (!getLocalTime(&timeinfo)) {
    Serial.print(">");
  }

  // Now convert struct tm to "seconds since midnight 1st Jan 2000"
  int q2k = (timeinfo.tm_year - 100) / 4;
  unsigned int d = q2k * DPQ;
  int yOffset = timeinfo.tm_year % 4;
  int dsq = (yOffset == 0) ? 0 : 1 + yOffset * DPY;  // DPY == 365
  d += dsq;
  unsigned long t = d * SPD + (timeinfo.tm_yday * SPD) + (timeinfo.tm_hour * SPH) + (timeinfo.tm_min * SPM) +
    timeinfo.tm_sec;
  return t;
  }
