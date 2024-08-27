from Cruncher import Cruncher
from datetime import datetime, timezone
import g
# WPackage class

# ---------------------------------------- Version of 25/08/2024 --------------------------------------------------

class WPackage:
    def __init__(self):
        self.hdr = '#'
        self.dtPackage = datetime.now(timezone.utc)
        self.vals = []

    def blank(self, hdr):
        self.hdr = hdr

    def fromRoof(self, csv, prevWD):
        '''fromRoof(): initiates WPackage object entirely from CSV and now() iso-formatted
        parameters:
            self: this instance
            csv: actual CSV string (with header character as 1st CSV character)
        returns: none
        '''
        csv = str(csv)
        self.hdr = csv[0:1]
        self.dtPackage = datetime.now(timezone.utc)
        self.dom = self.dtPackage.day
        self.hour = self.dtPackage.hour
        if self.hdr == 'H': #used only during catchup
            self.vals = Cruncher.hcsvToVals(csv[2:])
        else:
            self.vals = Cruncher.rcsvToVals(csv[2:], prevWD)

    def fromSD(self, hdr, csv):   #CSV comes from SD card; hdr value comes from initial character of .csv file; csv itself starts with isoDate: no header character
        '''fromSD(): initiates WPackage object from 1st character of filename (hdr) and CSV on SD card
        parameters:
            self: this instance
            hdr: actual header read from SD file name (no header in CSV string)
            csv: actual CSV string (without header character)
        returns: bool : True if no. of vals == expected number
        '''
        self.hdr = hdr
        self.dtPackage = datetime.fromisoformat(csv[0:19])
        isoDate = csv[0:19]    # NB isoDate starts at char [0]
        self.dom = int(isoDate[8:10])
        self.hour = int(isoDate[11:13])
        self.vals = Cruncher.sdCSVToVals(csv[20:])
        if hdr == 'H':
            num = g.NUM_HITEMS
        else:
            num = g.NUM_DITEMS
        return len(self.vals) == num
    
    def makeHourly(self, wpRT, en):   # used for making hourly package from rt and HrBuilder
        '''makeHourly(): makes hourly WPackage from wind/rain values stored in HrBuilder class and sensor values from realtime package
        parameters:
            self: this instance
            wpRT: the realtime WPackage
            en: the eastNorth tuples stored in Shed.py
        returns: str: message to identify WD analog coverage: 
        '''
        self.hdr = 'H'
        self.dtPackage = datetime.now(timezone.utc)
        self.dom = self.dtPackage.day
        self.hour = self.dtPackage.hour
        
        # now make vals
        self.vals.append(HrBuilder.hrBuckets * g.CR_RAIN)
        if HrBuilder.count == 0:
            self.vals.append(0.0)
        else:
            self.vals.append(HrBuilder.hrRevs * g.CR_SPEED / HrBuilder.count)
        self.vals.append(HrBuilder.hrGust * g.CR_SPEED)
        hrDir, hrWTF = Cruncher.hrDirection(HrBuilder.cpRevs, en)
        self.vals.append(hrDir)

        # START TEMP (LEAVE UNTIL VANE PERFORMANCE ASSURED!)
        mess = ""
        if HrBuilder.hrRevs != 0:
            cum = 0
            for i in range(0, g.NUM_POINTS):
                cum += HrBuilder.cpRevs[i]
            cover = float(cum) / float(HrBuilder.hrRevs) * 100.0
            if (cover < 85.0) or (hrWTF < 0.8):
                mess = "WD coverage (hr " + str(self.hour) + "): " + "{:.1f}".format(cover) + "; WTF value: " + "{:.3f}".format(hrWTF)            
        else:
            mess = "No anem revs in hour " + str(self.hour)
        # END TEMP

        # 5 rt sensors + voltage
        for i in range(g.NUM_WRITEMS, g.NUM_RITEMS):
            self.vals.append(wpRT.getVal(i))
        # Reset anaRevs array, ready for next hour
        for i in range (0, g.NUM_POINTS):
            HrBuilder.cpRevs[i] = 0
        return mess
  
    def makeDaily(self, wpH):
        '''makeDaily(): makes daily WPackage from wind/rain values stored in HrBuilder class and sensor values from realtime package
        parameters:
            self: this instance
            wpH: the current hourly WPackage
        '''
        self.hdr = 'D'
        self.dtPackage = datetime.now(timezone.utc)
        self.dom = self.dtPackage.day
        self.hour = 0
        
        #now make vals
        self.vals.append(DyBuilder.dayBuckets * g.CR_RAIN)
        self.vals.append(DyBuilder.dayRevs * g.CR_SPEED / DyBuilder.pollCount)
        self.vals.append(DyBuilder.dayGust * g.CR_SPEED)
        self.vals.append(DyBuilder.maxDayTemp)
        self.vals.append(DyBuilder.minDayTemp)
        self.vals.append(DyBuilder.maxDayHum)
        self.vals.append(DyBuilder.minDayHum)
        self.vals.append(Cruncher.riseFall(DyBuilder.hrPressure))
        self.vals.append(DyBuilder.maxDayLight)
        self.vals.append(DyBuilder.minDayLight)
        self.vals.append(wpH.getVal(9))
        print("Day: Revs: " + str(DyBuilder.dayRevs) + "; Count: " + str(DyBuilder.hrCount))  ## TEMP

    def makeCSV(self):
        '''makeCSV(): creates a CSV string from itself in the format for SD storage
        parameters:
            self: this instance
        returns: CSV string (SD card-style)
        '''
        csv = self.hdr
        x = 0
        if not self.vals is None:
            for val in self.vals:
                if isinstance(val, int):
                    csv += ',' + str(val)
                else:   # must be float
                    if x == 0:
                        dp = "{:.2f}"
                    else:
                        dp = "{:.1f}"
                    csv += ',' + dp.format(val)
                x += 1
        return csv[1:]  ## lose the first comma
    
    def makeLabelText(self, units):
        '''makeLabelText(): creates a string suitable for displaying in text box on GUI display screen
        parameters:
            self: this instance
            units: string list of units for each weather item: compass point is converted from 0-15 to N, NNE, etc
        returns: string for display
        '''
        csv = self.makeCSV()
        chunks = csv[2:].split(',')
        uChunks = units.split('\n')
        s = str()
        if len(chunks) < g.NUM_RITEMS:
            return '(empty)'
        if len(uChunks) < len(chunks):
            return 'not enough headers'
        x = 0
        for chk in chunks:
            if uChunks[x] == 'com':
                s += g.compass[int(chk)] + '\n'
            else:
                s += chk + uChunks[x] + '\n'
            x += 1
        return s
    
    def getVal(self, i):
        '''getVal(): returns the ith weather value as int or float
        parameters:
            self: this instance
            i: index of value to return
        returns: value as int or float
        '''
        return self.vals[i]
    
    def getValCount(self):
        '''getValCount(): returns the number of values in the values list
        parameters:
            self: this instance
        returns: int = list length
        '''
        return len(self.vals)
    
# ---------------------------------------------------------------------------------------------------------------

# Helper classes HrBuilder, DyBuilder

class HrBuilder:
    hrBuckets = 0
    hrRevs = 0
    hrGust = 0
    prevIx = 0
    count = 0
    cpRevs = []

    @classmethod
    def setup(cls):
        '''setup(): initializes HrBuilder arrays, etc
        parameters:
            cls: this class object
        returns: none
        '''
        cls.prevIx = 0

    @classmethod
    def resetHour(cls):
        '''resetHour(): resets key valiables / countaers to zero
        parameters:
            cls: this class object
        returns: none
        '''
        cls.hrBuckets = 0
        cls.hrRevs = 0
        cls.hrGust = 0
        cls.count = 0
        for i in range(0, g.NUM_POINTS):
            cls.cpRevs[i] = 0
    
    @classmethod
    def rtToHrUpdate(cls, wp: WPackage):
        '''rtToHrUpdate(): method to update values in HrBuilder from 3-second realtime data
        parameters:
            cls: this class object
            wp: the realtime WPackage object
        returns: none
        '''
        # buckets are cumulated over 24 hours and saved every hour in 'H' WPackage
        revs = wp.getVal(1)
        cls.hrRevs += revs
        if revs > cls.hrGust:
            cls.hrGust = revs
        wd = wp.getVal(3)
        if wd < g.NUM_POINTS:
            cls.cpRevs[wd] += revs
        # all sensors copy realtime data hourly
        cls.count += 1

class DyBuilder:
    dayBuckets = 0
    dayRevs = 0
    dayGust = 0
    maxDayTemp = -10
    minDayTemp = 40
    maxDayHum = 0
    minDayHum = 100
    maxDayLight = 0
    minDayLight = 100
    hrCount = 0
    pollCount = 0
    hrPressure = []

    @classmethod
    def setup(cls):
        '''setup(): initaliizes arrays, etc
        parameters:
            cls: this class object
        returns: none
        '''
        for i in range(0, g.HPD):
            cls.hrPressure.append(0)

    @classmethod
    def resetDay(cls):
        cls.dayBuckets = 0
        cls.dayRevs = 0
        cls.dayGust = 0
        cls.maxDayTemp = -10
        cls.minDayTemp = 40
        cls.maxDayHum = 0
        cls.minDayHum = 100
        cls.maxDayLight = 0
        cls.minDayLight = 100
        cls.hrCount = 0
        cls.pollCount = 0
        for i in range(0, g.HPD):
            cls.hrPressure[i] = 0

    @classmethod
    def hrToDyUpdate(cls, wp: WPackage):
        '''hrToDyUpdate(): updates values in DyBuilder from information form HrBuilder and hourly wp
        parameters:
            cls: this class object
            wp: the current hourly WPackage object
        returns: none
        '''
        cls.dayBuckets += wp.getVal(0)  # add hourly buckets
        cls.dayRevs += HrBuilder.hrRevs
        gu = wp.getVal(2)
        if gu > cls.dayGust:
            cls.dayGust = gu
        t = wp.getVal(4)
        if t > cls.maxDayTemp:
            cls.maxDayTemp = t
        if t < cls.minDayTemp:
            cls.minDayTemp = t
        hm = wp.getVal(5)
        if hm > cls.maxDayHum:
            cls.maxDayHum = hm
        if hm < cls.minDayHum:
            cls.minDayHum = hm
        prss = wp.getVal(6)
        cls.hrPressure[wp.hour] = prss
        li = wp.getVal(7)
        if li > cls.maxDayLight:
            cls.maxDayLight = li
        if li < cls.minDayLight:
            cls.minDayLight = li
        li = wp.getVal(8)
        if li > cls.maxDayLight:
            cls.maxDayLight = li
        if li < cls.minDayLight:
            cls.minDayLight = li
        cls.hrCount += 1
        cls.pollCount += HrBuilder.count


# -----------------------------------------------------------------------------------------------------------------
class Msg:
    def __init__(self, txt, fromRoof):
        '''
        __init__(): initiation of Msg object
        parameters:
            self: this instance
            txt: string: messgae text
            fromRoof: boolean: True if message originated from Roof, False if from Shed
        returns: none
        '''
        self.bRoof = fromRoof
        if fromRoof:    # use full "csv" string from roof: note that txt starts with ISO date, not 'M'
            self.timeStamp = datetime.now(timezone.utc)
            self.text = txt[2:]
        else:   # just use the whole text and timestamp it "now"
            self.timeStamp = datetime.now(timezone.utc)   ## curtail fractions of seconds
            self.text = txt

    def getText(self):
        '''getText(): returns actual text of message
        parameters:
            self: this instance
        returns: the message text only
        '''
        return self.text
    
    def getTimestamp(self):
        '''getTimestamp(): returns time as datetime message was created
        parameters:
            self: this instance
        returns: ISO time string
        '''
        return self.timeStamp
    
    def getLogEntry(self):
        '''getLogEntry(): rteurns full stringg of message with timestamp and source (Roof or Shed)
        parameters:
            self: this instance
        returns: full message stringwith timestamp and source
        '''
        if (self.bRoof):
            src = "Roof"
        else:
           src = "Shed"        
        return self.getTimestamp().isoformat()[0:19] + " [" + src + "]: " + self.text
