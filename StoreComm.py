import paho.mqtt.client as qt
import os
from datetime import datetime, timezone, timedelta
import g
from Cruncher import Cruncher
from WPackage import Msg
from collections import namedtuple

# -------------------------------------------- Version of 25/08/2024 --------------------------------------------------

# StoreComm class: handles all comms and SD card storage

#global variables(??)
icBuffer = str()
msgBuffer = str()
ogBuffer = str()
msgWaiting = False

# global MQTT callback functions here --------------------------------------------------------------------------------

def on_connect(client, userdata, flags, rc):
    '''on_connect(): sets up 2 MQTT subscriptions
    parameters:
        client: MQTT client object
        [other parameters not used]
    returns: none: it's an ISR!
    '''
    client.subscribe("ws/csv")
    client.subscribe("ws/messages")

def on_icMessage(client, userdata, msg):
    '''on_icMessage(): places incoming MQTT message in main or message buffer, depending on messgae topic attribute
    parameters:
        client, userdata: [not used]
        msg: string, text of incoming message
    returns: none
    '''
    if msg.topic == "ws/csv":
        g.icBuffer = msg.payload.decode("utf-8")
        g.roofCSVReceived = True
        #handle csv
    if msg.topic == "ws/messages":
        g.msgBuffer = msg.payload.decode("utf-8")
        g.roofMsgReceived = True
        #handle messages

        #otherwise ignore
   
# -----------------------------End of MQTT callbacks -----------------------------------
    
# StoreComm class starts here...
class StoreComm:
    def __init__(self):
        '''__init__(): class initiations: sets up MQTT client connection: relies on "Home or Shed" to have been previously determined to use correct Wifi IP address
        parameters:
            self: this instance
        returns: none
        '''
        self.client = qt.Client()
        self.client.on_connect = on_connect
        self.client.on_message = on_icMessage
        if g.atHome:
            self.client.connect("192.168.1.165", 1883, 60)
        else:
            self.client.connect("192.168.1.249", 1883, 60)   # 60 seconds keep alive: ??
        print("mqtt started")

    # Start of SD Card Zone -------------------------------------------------------------

    def recoverData(self):
        '''recoverData(): on bootup, retrieves data already stored on SD card over the previous calendar month: this will usually involve getting data from 4 files:
        current month and previous month for both hours and days
        parameters:
            self: this instance
        returns: tuple of 2 lists of CSV strings (hours, days) recovered from SD card
        '''
        isoHr, isoDay = self.getLatest()
        dtLatestHr = datetime.fromisoformat(isoHr)
        dtLatestDay = datetime.fromisoformat(isoDay[0:19])

        currFolder = g.gardenPath + "csv/"
        dtNow = datetime.now(timezone.utc)

        isoShort = Cruncher.adjustfName(dtNow) # this ensures midnight's data on 1st of month is stored in PREVIOUS month's file

        fNamePrev = currFolder + "H{:d}-{:02d}.csv".format(dtNow.year, dtNow.month - 1)
        fNameThis = currFolder + 'H' + isoShort + ".csv"
        dNameThis = fNameThis.replace('H20', 'D20', 1)  # change initial 'H' to 'D' in filename
        dNamePrev = fNamePrev.replace('H20', 'D20', 1)  # ditto
        ftx = os.path.exists(fNameThis)
        fpx = os.path.exists(fNamePrev)
        dtx = os.path.exists(dNameThis)
        dpx = os.path.exists(dNamePrev) 
        
        hrs = []
        if fpx: # select day/hrs after hdLatest
            Cruncher.fillArraySelected(hrs, fNamePrev, "H", dtLatestHr, True)
        if ftx: # do the opposite
            Cruncher.fillArraySelected(hrs, fNameThis, "H", dtLatestHr, False)
        days = []
        if dpx: # select days after dLatest
            Cruncher.fillArraySelected(days, dNamePrev, "D", dtLatestDay, True)
        if dtx: # do the opposite
            Cruncher.fillArraySelected(days, dNameThis, "D", dtLatestDay, False)
        
        # we now have 2 arrays of CSV entries to place into their respective WPackage arrays
        RecoveryDuo = namedtuple("recovery", "hrList dayList")
        recover = RecoveryDuo(hrs, days)
        return recover
    
    def storePackage(self, wp): ## NB: this method takes on trust that this really is the next item to store on SD card file (hour or day)
        '''storePackage(): stores the contents of wp package into the relevant ('H' or 'D') CSV file on the SD card. Also updates "Latest.txt file" on success
        parameters:
            self: this instance
            wp: WPackage to store on SD card as CSV string
        returns: none
        '''
        csv = wp.makeCSV()
        dtPk = wp.dtPackage
        isoShort = dtPk.isoformat()[0:7]

        # First get "latest.txt" file info: ok if new package's date is after the relevant latest (guards against preemature request by Shed on Roof)
        #isoHr, isoDy = self.getLatest()
        #if (wp.hdr == 'H'):
         #   ok = (wp.isoDate > isoHr)
        #else:
         #   ok = (wp.isoDate > isoDy) 
        ok = True       
        
        # now store one line of csv data to the relevant (H or D) month's file
        if ok:
            isoShort = Cruncher.adjustfName(dtPk) # this ensures midnight's data on 1st of month is stored in PREVIOUS month's file
            currFolder = g.gardenPath + "csv/"
            fName = currFolder + wp.hdr + isoShort + ".csv"  # NB: fName is derived from package data
            print("File to write to: " + fName)
            if os.path.exists(fName):
                f = open(fName, 'a')
            else:
                f = open(fName, 'w')
                if (wp.hdr == 'H'): # add line of headers
                    f.write(g.sdhHeaders + "\n")
                else:
                    f.write(g.sddHeaders + "\n")
            f.write(datetime.now(timezone.utc).isoformat()[0:19] + csv + "\n")
            f.close()
            print("Written to file: " + datetime.now(timezone.utc).isoformat()[0:19] + csv + "\n")

            # ensure only the relevant one (of two) items is updated!
            #newHr = isoHr
            #newDy = isoDy
            #if wp.hdr == 'H':
                #newHr = wp.isoDate[0:19]    ## truncates at seconds
            #else:
                #newDy = wp.isoDate
          
            # now, write latest to SD card
            #fLatest = g.gardenPath + "Latest.txt"
            #f = open(fLatest, 'wt')
            #print(newHr + ';' + newDy, file=f)
            #f.close()
            #self.getLatest()    # TEMP!
        else:
            self.createAndLogMessage("Data from roof was not new!")

    def getLatest(self):
        '''getLatest(): gets the most recently saved hourly and daily data from "Latest.txt" file
        parameters:
            self: this instance
        returns: tuple of 2 strings showing most recent hourly and daily data, in ISO format
        '''
        fName = g.gardenPath + "Latest.txt"
        f = open(fName, 'rt')
        latestInfo = f.readline()
        f.close()      
        isoHr = latestInfo[0:19]
        isoDy = latestInfo[20:]
        return isoHr, isoDy          
    
    def logMessage(self, m : Msg):
        '''logMessage(): stores message in log file for the relevant month (uses Cruncher adjustment for midnight on 1st of month)
        parameters:
            self: this instance
            m: Msg object to be stored
        returns: none
        '''
        iso = m.getTimestamp()  # this is now a datetime object

        # now store message to the relevant month's log file
        iso = Cruncher.adjustfName(iso) # this ensures midnight's data on 1st of month is stored in PREVIOUS month's file
        currFolder = g.gardenPath + "log/"
        fName = currFolder + "M" + iso + ".log"  # NB: fName is derived from package data
        if os.path.exists(fName):
            mode = 'a'
        else:
            mode = 'w'
        f = open(fName, mode)
        f.write(m.getLogEntry() + "\n")
        f.close()

    def createAndLogMessage(self, txt):
        '''createAndLogMessage(): inserts message text into the start position of global message list and deletes bottom entry if list length > MAX_MSGQ,
        then calls logMessage()
        parameters:
            self: this instance
            text: text string to insert
        returns: none
        '''
        m = Msg(txt, False)
        g.msgs.insert(0, m)
        if len(g.msgs) > g.MAX_MSGQ:
            g.msgs.pop(-1)

        self.logMessage(m)
