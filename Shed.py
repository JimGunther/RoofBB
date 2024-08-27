#Global variables
import g
# Set up global variables first
g.init()
from Repo import Repo
from Cruncher import Cruncher
from Show import Display
from StoreComm import StoreComm 
from WPackage import WPackage, Msg, HrBuilder as HB, DyBuilder as DB
from datetime import datetime, timezone, timedelta
#import time
import os
from tkinter import *

# --------------------------------------- Version of 26/08/2024 --------------------------------------------------

if os.environ.get('DISPLAY','') == '':
    os.environ.__setitem__('DISPLAY', ':1.0')

root = Tk()
dtBoot = datetime.now(timezone.utc)
hrNext = 0
prevHr = dtBoot.hour
prevWD = 0
bAlarm = True
dtLastRoof = datetime.now(timezone.utc)
en = [] #eastNorth array for hourly wind direction

# Local class instances
sc = StoreComm()
dsp = Display(root)

def checkPulse():
    '''checkPulse(): method to raise alarm message if Roof sends no messages for 30secs
    parameters: none
    returns: none
    '''
    global dtLastRoof, bAlarm
    td = timedelta(seconds=30)
    if bAlarm and (datetime.now(timezone.utc) - dtLastRoof > td):
        bAlarm = False
        sc.createAndLogMessage("No recent Roof message")  

def roofIncoming(validHdrs):
    '''roofIncoming(): method to return a WPackage or None if no i/c, not validated or a message. Also saves into RAM array and stores on SD card if valid hourly or daily weather data
    and, if message, adds to message list and stores entry in log file
    parameters:
        validHdrs: string containing the valid headers for this call to function
    returns: WPackage or None
    '''
    global hrNext, dtLastRoof, bAlarm
    if g.roofCSVReceived:
        g.roofCSVReceived = False  ## switch off flag
        dtLastRoof = datetime.now(timezone.utc)
        bAlarm = True
        #print(g.icBuffer)
        if Cruncher.validate(g.icBuffer, sc, validHdrs, False):
            wp = saveIncoming(g.icBuffer)   #into memory as a WPackage object
            if wp is not None:
                if isinstance(wp, WPackage):
                    if wp.hdr == 'R':
                        # do RT to hourly: 
                        HB.rtToHrUpdate(wp)
                    else:
                        sc.storePackage(wp) # into filing system on SD card
                        if wp.hdr == 'H':   #safeguard check
                            latestHr, xx = sc.getLatest()   # use the first value only in tuple returned
                            dtHrLatest = datetime.fromisoformat(latestHr[0:13])
                            dtNext = dtHrLatest + timedelta(hours=1)
                            hrNext = dtNext.hour
            return wp
    if g.roofMsgReceived:
        g.roofMsgReceived = False #switch off flag
        if Cruncher.validate(g.msgBuffer, sc, 'M',  True):
            wp = saveIncoming(g.msgBuffer)
            if wp is not None:
                if isinstance(wp, Msg):
                    g.msgs.insert(0, wp)
                    if len(g.msgs) > g.MAX_MSGQ:
                        g.msgs.pop(-1)
                    sc.logMessage(wp)
            # variable wp is a reference to the newly arrived WPackage object or Msg
            return wp
        else:
            return None
    else:
        return None
        
def saveIncoming(txt):
    '''saveIncoming(): method to deal with validated incoming message and CSV data: NB this method is NOT for selecting the package to Display! Saves in Repo if WPackage
    parameters:
        txt: incoming string
    returns: WPackage or Msg object
    '''
    global prevWD

    if (txt[0] == 'M'):
        g.msgBuffer = str()
        for c in txt[1:]:
            g.msgBuffer += c
        return Msg(g.msgBuffer, True)
    
    #from here on, all are validated CSV strings....
    ch = txt[0]
 
    wp = WPackage()
    wp.fromRoof(txt, prevWD)
    prevWD = wp.getVal(3)
    
    if ch == 'R':
        Repo.deposit(wp)
    if ch == 'H':
        Repo.deposit(wp)
    return wp

def doHourly():
    '''doHourly(): if a new hour, does shed-based hourly calculations
    parameters: none
    returns: bool: True if hour "ticked by"
    '''
    global prevHr
    currHr = datetime.now(timezone.utc).hour
    if currHr != prevHr:
        print("Start doHourly()")
        # Make hourly WPackage
        wp = WPackage()
        messg = wp.makeHourly(Repo.rtPackage, en)
        if len(messg) > 0:
            sc.createAndLogMessage(messg)
        Repo.deposit(wp)
        sc.storePackage(wp)
        DB.hrToDyUpdate(wp)
        if currHr == 0: # midnight
            wpD = WPackage()
            wpD.makeDaily(wp)
            Repo.deposit(wpD)
            sc.storePackage(wpD)
            DB.resetDay()
        HB.resetHour()
        prevHr = currHr
        return True
    return False        

# ---------------------------- Now, main functions: setup and loop -------------------------------

def setup():
    # Initial (dummy) values for key variables here
    #g.init()
    
    Repo.setup()
    
    # restore data from SD card to volatile memory
    #r = sc.recoverData()
#    hrs = r.hrList
 #   days = r.dayList
  #  hList = "Hours: "
   # dList = "Days: "
    
    #for hr in hrs:
     #   if len(hr) > g.MIN_CSV: # only recover if it's probable valid data
      #      h = int(hr[11:13])
       #     d = int(hr[8:10]) - 1
        #    wp = WPackage()
         #   if wp.fromSD('H', hr):
          #      Repo.deposit(wp)
           #     hList += str(d) + ':' + str(h) + ';'

#    for dy in days:
 #       if len(dy) > g.MIN_CSV: # as above
  #          d = int(dy[8:10]) - 1
   #         wp = WPackage()
    #        if wp.fromSD('D', dy):
     #           Repo.deposit(wp)
      #          dList += str(d) + ';'
        
    Cruncher.setupVane(HB.cpRevs, en)
    HB.setup()
    DB.setup()

    sc.client.loop_start()
    root.after(1500, loop1)
    if g.atHome:
        ss = "at home"
    else:
        ss = "at Shed"
    sc.createAndLogMessage("Shed startup [ver 26/08] completed " + ss)
    dsp.updateAllLabels(Repo.rtPackage)  # using dummy WPackage for initial display only 
    print("Setup done.")

def loop1():
    # first check for mqtt messages 
    roofIncoming('RH')
    checkPulse()              
    doHourly()
    # update all the relevant screen information
    chd = Cruncher.mixtoCHD(dsp.getMix())
    dsp.updateVarLabels(Repo.retrieve(chd))    
    #END OF MAIN LOOP
    root.after(1500, loop1)


# --------------------------------------- actual program! ----------------------------------        

setup()
global hdrText                     

hdrText = 'Weather Now'
dsp.strHeader.set(hdrText)

root.mainloop()
