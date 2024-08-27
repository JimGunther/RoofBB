import re
import math
import g
from datetime import date, datetime
import time
#from StoreComm import createAndLogMessage
from collections import namedtuple
# class Cruncher here

# ------------------------------------------------- Version of 25/08/2024 ---------------------------------------------------------

class Cruncher:
    #def __init__(self):
     #   pass
    
    # filter(): method to decide which data file lines to be included in data recovery at startup
    @staticmethod
    def filter(line, hdr, limit, lowHigh):  #NB: 'line' has NO header character, starts with isoDate
        ''' filter(): this method filters in only the relevant lines from the monthly csv file
        parameters:
            line: the CSV text minus initial header character
            hdr: the header character
            limit: the calculated cut-off date/hour, evaluated as 24*(day -1 ) + hour
            lowHigh: boolean value set to True for previous month's file and False for current month's file
        returns: bool
        '''
        if not line:
            return False
        if len(line) < 19:  # 19 == length of iISO date string
            return False
        dt = datetime.fromisoformat(line[0:19])
        return (dt > limit) == lowHigh
    
    @staticmethod
    def fillArraySelected(lst, fN, hdr, limit, lowHigh):
        '''fillArraySelected(): this method appends CSV lines from an SD card file on bootup to restore weather values from an earlier session.
        parameters:
            lst: the List object to receive the appended lines
            fN: name of file on SD card
            hdr: the header character ('H' or 'D') of the source file and wetaher packages
            limit: the calculated cutoff date/hour, evaluated as 24*(day - 1) + hour
            lowHigh: boolean value: True for previous month's file and False for current
        returns: void (values are appended to lst)
        '''
        f = open(fN, "rt")
        while True:
            line = f.readline()
            if not line:
                break
            if len(line) == 0:
                break
            if line[0:2] != "20":   # must be header, not data
                line = f.readline()
            if Cruncher.filter(line, hdr, limit, lowHigh):
                lst.append(line)
        f.close()

    @staticmethod
    def rcsvToVals(icCSV, prevWD):
        '''rcsvToVals(): takes an i/c realtime CSV string from roof, splits it at commas, converts each part to integer or float and adds to list 
        parameters:
            icCSV: string variable containing the incoming roof CSV line after the header character and ISO date have been stripped off the front
        returns: list of calculated native values (ints and floats) for storing in a WPackage object
        '''
        chunks = icCSV.split(",")
        lng = len(chunks)
        vals = []
        x = 0
        while x < lng:  
            chk = chunks[x]
            if x == 0: # bucket tips to rain mm
                val = g.CR_RAIN * float(chk)                    
            elif x == 1: # revs wind speed
                val = g.CR_SPEED * float(chk)
            elif x == 2: # gust
                val = g.CR_SPEED * float(chk)
            elif x == 3: # direction
                val = Cruncher.a2c(int(chk), prevWD)
            elif x == lng - 1:
                val = float(chk) * 3.3 / 4096.0
            elif x > 3:
                val = int(chk)
            else:   
                val = None
            if not val is None:
                vals.append(val)
            x += 1
        
        return vals
    
    @staticmethod
    def hcsvToVals(icCSV):
        '''hcsvToVals(): takes an i/c hourly CSV string from roof, splits it at commas, converts each part to integer or float and adds to list 
        parameters:
        icCSV: string variable containing the incoming roof CSV line after the header character and ISO date have been stripped off the front
        returns: list of calculated native values (ints and floats) for storing in a WPackage object
        '''
        chunks = icCSV.split(",")
        lng = len(chunks)
        vals = []
        x = 0
        while x < lng:  
            chk = chunks[x]
            if x == 0: # bucket tips to rain mm
                val = g.CR_RAIN * float(chk)                    
            elif x == 1: # revs wind speed
                val = g.CR_SPEED * float(chk) / 1200.0  # I think! (depends on Roof calc'n)
            elif x == 2: # gust
                val = g.CR_SPEED * float(chk)
            elif x == 3: # direction
                val = g.NUL_WD
            elif x == lng - 1:
                val = float(chk) * 3.3 / 4096.0
            elif x > 3:
                val = int(chk)
            else:   
                val = None
            if not val is None:
                vals.append(val)
            x += 1
        return vals

    @staticmethod
    def sdCSVToVals(sdCSV):
        '''sdCSVToVals(): used to recover data from SD card, NOT i/c from Roof (hourly results only): converts raw counts and intervals to wind measurements (RainWind)
        parameters:
            sdCSV: string of CSV as stored on the SD card (that part following the ISO date)
        returns: list of calculated native values (ints and floats) for storing in a WPackage object
        '''
        chunks = sdCSV.split(',')
        lng = len(chunks)
        vals = []
        x = 0
        while (x < lng):
            chk = chunks[x]
            if chk.find(".") > 0:
                val = float(chk)
            else:
                val = int(chk)
            vals.append(val)
            x += 1
        return vals
    
    @staticmethod
    def dayCSVToVals(dyCSV):
        '''dayCSVToVals(): used to recover data from SD card, NOT i/c from Roof (daily results only): converts raw counts and intervals to wind measurements (RainWind)
        parameters:
            sdCSV: string of CSV as stored on the SD card (that part following the ISO date)
        returns: list of calculated native values (ints and floats) for storing in a WPackage object
        '''
        chunks = dyCSV.split(',')
        lng = len(chunks)
        vals = []
        x = 0
        while x < lng:
            chk = chunks[x]
            if x == 0: # total buckets
                val = g.CR_RAIN * float(chk)
            elif x == 1: # total Revs
                val = g.CR_SPEED * float(chk)   # divided by ??
            elif x == 2: #max gusts
                val = g.CR_SPEED * float(chk)   # divided by ??
            elif x == lng - 1:
                val = float(chk) * 3.3 / 4096.0
            elif x > 2:
                val = int(chk)
            if not val is None:
                vals.append(val)
            x += 1
        return vals

    
    @staticmethod
    def valsToCSV(vals): 
        '''valsToCSV(): takes a list of values (ints and floats) and creates a CSV string in a format suitable for storing on SD card
        parameters:
            vals: list of integers and floats stored in WPackage
        returns: CSV string suitable for storing on SD card
        '''
        csvOut = ''
        lng = len(vals)
        for x in range(0, lng):
            match x:
                case 0: # bucket tips
                    s = '{0:.2f}'.format(vals[x])
                    break
                case 1: # wind speed
                    s = '{0:.1f}'.format(vals[x])
                    break
                case 2: # gust
                    s = '{0:.1f}'.format(vals[x])
                    break
                case _:
                    s = str(vals[x])
                    break
        csvOut = csvOut + ',' + s
        
        return csvOut    
    
    @staticmethod
    def validate(txt, sc, validHdrs, msgOnly):
        '''validate(): checks i/c string for validity (header, ISO date, correct no. of CSV entries, all entries numeric)
        parameters:
            txt: the CSV string to validate
            sc: the current StoreComm class object (to enable message logging)
            validHdrs: string containing which header characters are valid in this context
            msgOnly: boolean: if True, only Header and ISO date checked
        returns: boolean: True if fully validated, False otherwise
        '''
        if txt == "(empty)":
            return False
        # first validate header character
        hdr = txt[0]
        validHeader = False
        for c in validHdrs:
            if hdr == c:
                validHeader = True
        if not validHeader:
            sc.createAndLogMessage("Invalid header: " + hdr + "; valid: " + validHdrs )
            return False
        
        if msgOnly: # no further validation for messages
            return True
        
        # now count commas
        csvPart = txt[2:]   # now no iso date string: '2' because of comma between R and CSV
        numCommas = csvPart.count(",")
        if hdr == 'D':
            matchNum = g.NUM_DITEMS - 1 #first comma is omitted from check: no. commas == no. items - 1
        else:
            if hdr == 'H':
                matchNum = g.NUM_HITEMS - 1
            else:
                matchNum = g.NUM_RITEMS - 1
        if numCommas != matchNum:
            sc.createAndLogMessage("Wrong number of commas\t" + str(matchNum) + " expected, " + str(numCommas) + " found.")
            return False
        
        strippedCSV = csvPart.replace(",", "").replace("-", "").replace(".", "")
        return strippedCSV.isnumeric()
    
    @staticmethod
    def mixtoCHD(mix):
        '''mixtoCHD(): converts a 'Mix' tuple(header, day, hour) to a CHD tuple (character, hour day)
        parameters:
            mix: tuple(char, int, int) in 'Mix' order
            returns: tuple (char, int, int) in CHD order
        '''
        dmode, dy, hr = mix
        s = 'RHD'
        #depends on dmode being in the range 0 to 2
        ch = s[dmode]
        return (ch, hr, dy + 1)
                
    @staticmethod
    def adjustedTime(t, lati, lngHr, bRise):
        '''adjustedTime(): helper for sunrise/set calculation
        parameters:
            t: double: internal representation of unadjusted rise or set time
            lati: float: latitude in degrees (+ve = north)
            lngHr: float: longitude converted from degrees (+ve = east) to time difference from Greenwich (in hours)
            bRise: boolean: True when calculating sunrise, False for sunset
        returns: time (24 hour): double expressed as hours and decimal fractions of hour
        '''
        DegRad = math.pi / 180.0
        RadDeg = 180.0 / math.pi
        Zenith = 90.833
    
        sma = 0.9856 * t - 3.289    # sun's mean anomaly
        truLong = sma + 1.916 * math.sin(DegRad * sma) + 0.02 * math.sin(DegRad * 2.0 * sma) + 282.634  # sun's true longitude
        while (truLong < 0.0):
            truLong += 360.0
        while (truLong > 360.0):
            truLong -= 360.0;   # adjust to range 0 - 360 degrees

        ra = RadDeg * math.atan(0.91764 * math.tan(DegRad * truLong))   # sun's right ascension
        while (ra < 0.0):
            ra += 360.0
        while (ra > 360.0):
            ra -= 360.0;   # adjust to range 0 - 360 degrees

        # Put ra into same quadrant as truLong
        longQuad = math.floor(truLong / 90.0) * 90.0
        raQuad = math.floor(ra / 90.0) * 90.0
        ra = ra + longQuad - raQuad

        # Convert ra to hours
        ra = ra / 15.0; # i.e. 24 / 360

        #  Sun's declination
        sinDec = 0.39782 * math.sin(DegRad * truLong)
        cosDec = math.cos(math.asin(sinDec))

        # Sun's local hour angle
        cosH = (math.cos(DegRad * Zenith) - (sinDec * math.sin(DegRad * lati))) / (cosDec * math.cos(DegRad * lati))

        if ((cosH > 1.0) or (cosH < -1.0)): return 0.0

        hr = 360.0 - RadDeg * math.acos(cosH) if bRise else RadDeg * math.acos(cosH)
        hr = hr / 15.0     # degrees to hours

        # Calculate local time for rise / set
        tRS = hr + ra - (0.06571 * t) - 6.622
        ut = tRS - lngHr;    # UTC
        while (ut < 0.0): ut += 24.0
        while (ut >= 24.0): ut -= 24.0

        return ut
        
    @staticmethod
    def sunRiseSet():
        '''sunRiseSet(): calculates sunrise and sunset time at Shed (NB: Latitude and longitude of Bedford Shed ishard-coded)
        parameters: none
        returns: named tuple (SRS) :(double, double) sun rise and set timesas hour and decimal fractions of hour
        '''
        LATI = 52.12766
        LONGI = -0.46959
        dayOfYear = date.today().timetuple().tm_yday
        
        # Convert longitude to hour value to get approx noon, rise, set times
        lngHr = LONGI / 15.0
        tRise = dayOfYear + ((6.0 - lngHr) / 24.0)
        tSet = dayOfYear + ((18.0 - lngHr) / 24.0)
        hrRise = Cruncher.adjustedTime(tRise, LATI, lngHr, True)
        hrSet = Cruncher.adjustedTime(tSet, LATI, lngHr, False)
        timeNow = time.localtime()
        isDST = timeNow.tm_isdst
        hrRise += isDST
        hrSet += isDST
        csvAppend = "{:.{}f}".format(hrRise, 3) + "," + "{:.{}f}".format(hrSet, 3) + ","
        sRise = Cruncher.dblToHrMin(hrRise)
        sSet = Cruncher.dblToHrMin(hrSet)
        SRS = namedtuple("SRS", "csvAppend riseTime setTime")
        srs = SRS(csvAppend, sRise, sSet)

        return srs   # tuple of CSV needed and formatted strings for (LCD) display
    
    @staticmethod
    def dblToHrMin(h):
        '''dblToHrMin(): helper to sunrise/set. Converts time as double (hours and fractions of hour) to string formatted hh:mm
        parameters:
            h: double (hours and fractions of hour)
        returns: string formatted hh:mm
        '''
        hr = int(h)
        mn = int((h - hr) * 60 + 0.5)
        if mn == 60:    #prevents format "hh:60" which can happen owing to rounding errors
            mn = 0
            hr += 1
        return str(hr) + ":" + "{:02d}".format(mn)
 
    @staticmethod
    def adjustfName(dt: datetime):    
        '''adjustfName(): method to ensure midnight's data on 1st of month is stored in previous month's file
        parameters:
            dt: datetime for WPacke or Msg
        returns: string in ISO format: only adjusted for the entry at midnight on 1st day of month
        '''
        dtReturn = dt
        if (dt.day == 1) and (dt.hour == 0):
            yr = dt.year
            mn = dt.month - 1
            if mn == 0: # Jan=>Dec
                mn = 12
                yr -= 1
            dtReturn = datetime(yr, mn, 1)
        return dtReturn.isoformat()[0:7]
    
    @staticmethod
    def setupVane(cumRevs, eastNorth):
        '''setupVane(): assigns trig values to each compass direction for "hourly average direction" calculation; also initializes cumRevs array
        parameters:
            cumRevs: array of cumulative revs at each (of 8) compass points
            eastNorth: empty list (to be populated with 8 tuples)
        returns:
            eastNorth: array of tuples withh east and north trig values
        '''
        # Trigonometrical values of eastings and northings for compass points
        s1 = math.sin(math.pi / 8.0)
        s2 = 1.0 / math.sqrt(2.0) # = sin(PI/4) == cos (PI/4)
        s3 = math.cos(math.pi / 8.0)
  
        # Initiate east, north coordinates for 8 compass points (i.e alternate array elements)
        eastNorth.append((0.0, 1.0))    # northeastNorth.app
        eastNorth.append((-s1, s3))     # NNW
        eastNorth.append((-s2, s2))     # northwest
        eastNorth.append((-s3, s1))     # WNW
        eastNorth.append((-1.0, 0.0))   # west
        eastNorth.append((-s3, -s1))    # WSW
        eastNorth.append((-s2, -s2))    # southwest
        eastNorth.append((-s1, -s3))    # SSW
        eastNorth.append((0.0, -1.0))   # south
        eastNorth.append((s1, -s3))     # SSE
        eastNorth.append((s2, -s2))     # southeast
        eastNorth.append((s3, -s1))     # ESE
        eastNorth.append((1.0, 0.0))    # east
        eastNorth.append((s3, s1))      # ENE
        eastNorth.append((s2, s2))      # northeast
        eastNorth.append((s1, s3))      # NNE
  
        # set revolution counts to zero for all 16 compass points
        for i in range(0, g.NUM_POINTS):
            cumRevs.append(0)

    @staticmethod
    def a2c(anaVal, prevCP):
        '''a2c(): converts analog pin reading to compass direction (0-15)
        parameters:
            anaVal: int: analog pin reading
            prevCP: int: previous value of compass point
        returns: int: compass point (0-15)
        '''    
        v128 = (anaVal + 64) >> 7 # +64 does rounding in 128-sized ranges
        mtch = -1
        for x in range(0, g.NUM_POINTS):
            if g.C2A[x] == v128:
                mtch = x
                break
        if mtch > -1:
            return mtch
        else:
            return prevCP

    @staticmethod
    def hrDirection(cpRevs, eastNorth):
        '''hrDirection(): trignometric algorithm to produce "average" wind direction in an hour: check results for soundness of logic
        parameters:
            cpRevs: array of 16 integers representing anemometer revs at each compass point
            eastNorth: list of 8 tuples created in setupVane()
        returns: tuple of 2 integers: (aveDirn, wtf value)
        '''
        #  int iCompass
        totalRevs = 0
        countedRevs = 0
        eastings = 0.0
        northings = 0.0
        minDistance = 4.0 # circle diameter squared

        # method below allocates wind "amount" to relevant direction

        # allocate revs to each compass point
        for iCmp in range(0, g.NUM_POINTS):
            totalRevs += cpRevs[iCmp]
            if iCmp > -1:
                countedRevs += cpRevs[iCmp]    # total of revs "seen" by the 16 selected points
                eastings += cpRevs[iCmp] * eastNorth[iCmp][0]  # first element of tuple: easting
                northings += cpRevs[iCmp] * eastNorth[iCmp][1] # second element of tuple: northing
  
        if totalRevs == 0:
            return (g.NO_WD, 0)
  
        # scale eastings and northings into range {-1, 1}
        eastings = eastings / totalRevs  # average eastings: this is guaranteed to be in the range {-1, 1}
        northings = northings / totalRevs # average northings: ditto
        radiusMean = math.sqrt(eastings * eastings + northings * northings) # distance from compass centre to mean point, always in the range {0, 1}
        if radiusMean < 0.1:
            return g.VAR_WD  # too variable to be meaningful
  
        eastings = eastings / radiusMean
        northings = northings / radiusMean # project the mean point to the compass circle
  
        # Now find out which compass point is nearest to this calculated point
        for i in range(0, g.NUM_POINTS):
            eastDistance = eastNorth[i][0] - eastings
            northDistance = eastNorth[i][1] - northings
            sqDistance = eastDistance * eastDistance + northDistance * northDistance
            if sqDistance < minDistance:
                meanPosition = i
                minDistance = sqDistance
  
        return (meanPosition, radiusMean)

    @staticmethod
    def riseFall(hourlyPress):
        '''riseFall(hourlyPress): rising / falling: calculates line of best fit through 24 hourly barometric pressure results
        parameters: 
            hourlyPress: array of 24 integers with hourly barometric pressure values
        returns: int: -1 (falling), 0 (steady) or 1 (rising)
        '''
        avePress = 0.0
        sumPress = 0.0
        sumXY = 0.0
        count = 0
    
        print(hourlyPress)  # TEMP
        for i in range (0, g.HPD):
            if hourlyPress[i] > 0:
                count += 1
                sumPress += hourlyPress[i]
        avePress = sumPress / count
        print("RF: count: " + str(count) + "; avePress = " + str(avePress)) #TEMP

        # Use simple linear regression to determine line of best fit and hence rising or falling pressure: MOVE THIS!
        h = -11.5
        for i in range(0, g.HPD):
            if hourlyPress[i] > 0:
                sumXY = sumXY + h * (hourlyPress[i] - avePress)
            h = h + 1.0
  
        sumXY = sumXY / 1150.0 # => slope of best fit line: 1150 assumes 24 hourly results, but doesn't matter as
        print("sumXY: " + str(sumXY)) #TEMP
        if sumXY < 0.0:
            rv = -1
        else:
            rv = 1
        if abs(sumXY) < (g.MIN_BAR * count / g.HPD):
            rv = 0
        return rv
