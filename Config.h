#ifndef CONFIG_H
#define CONFIG_H

// ****************************** Version of 07.08.2024 ******************************************
// General Constants
// Wifi-related
#define NUM_NETWORKS 3
#define SSID_LEN 16
#define PWD_LEN 16
#define ISO_LEN 20
#define IP_LEN 20
#define SHED_SSID "BTB-NTCHT6"
#define HOME_SSID "BT-S7AT5Q"
#define RICH_SSID "GOULD_TP"
#define SHED_PWD "UJDafGKptCvXb4"
#define HOME_PWD "yJrbR6x6TkDP7g"
#define RICH_PWD "starwest"

// MQTT
#define SHED_IP "192.168.1.249"
#define HOME_IP "192.168.1.165" // was .248"
#define RICH_IP "192.168.1.177"
#define QT_LEN 80 // probably overgenerous

// Various charcater buffers' lengths
#define BUF_LEN 84
#define CATCHUP_LEN 164
#define ICBUF_LEN 10
#define HRREQ_LEN 6 // length of hourly i/c request message: HxxDxx (hour and date requested)

#define NUL_WD 18  // code for wind direction NULL value

// Timings, etc
#define LOOP_TIME 250  // milliseconds
#define MAX_LOOP_COUNT 120
#define ZONE4 4
#define ZONE12 12
#define ZONE40 40
#define ZONE0 120

#define POLL_COUNT 12  // number of loops between successive revs calculations 

// Time constants
#define SECS_1970_TO_2000 946684800UL
#define HPD 24 // hours per day
#define DPM 31  // days per month
#define MPY 12  // months per year
#define DPY 365 // days per (non-leap) year
#define CLOCK_UPD_HR 15
#define CLOCK_UPD_MIN 30

// Pin numbers == GPIO numbers
const int RevsPin = 25;  // pin connected to wind speed rotation counter (interrupt 0) 
const int RainPin = 15; // pin connected to rain gauge - buckets tipped (interrupt 1);
const int WDPin = 32; // vane (wind direction)
const int VoltsPin = 34;  // raw analog value, not volts!
const int LEDPin = 16;

#endif
