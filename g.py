import os

# ------------------------------------------------------- Version of 01/08/2024 ---------------------------------------

#globals shared between modules

def init():
    global DPW
    DPW = 7
    global DPM
    DPM = 31
    global HPD
    HPD = 24
    global SPH
    SPH = 3600
    global NUM_WRITEMS
    NUM_WRITEMS = 4
    global NUM_RITEMS
    NUM_RITEMS = 10
    global NUM_HITEMS   # used for catchup only
    NUM_HITEMS = 10
    global NUM_DITEMS
    NUM_DITEMS = 11
    global gardenPath
    gardenPath = os.path.realpath(__file__)[0:-4]
    response = os.popen('iwgetid').readline()
    s = response[-11:-2]
    global atHome
    atHome = s == "BT-S7AT5Q"
    
    #display modes
    global DM_RT
    DM_RT = 0
    global DM_HR
    DM_HR = 1
    global DM_DY
    DM_DY = 2
    
    global MIN_CSV
    MIN_CSV = 40
    global icBuffer
    icBuffer = "(empty)"
    global ogBuffer
    ogBuffer = "(empty)"
    global msgBuffer
    msgBuffer = "(empty)"
    global roofCSVReceived
    roofCSVReceived = False
    global roofMsgReceived
    roofMsgReceived = False
    global rhNames
    rhNames = "Rainfall: \nWind Speed: \nGust Speed: \nWind Direction: \nTemperature: \nHumidity: \nBar. Pressure: \nLight Level 1:\nLight Level 2: \nBattery: "
    global dNames
    dNames = "Rainfall: \nAve Wind Speed: \nMax Gust Speed: \nMax Temperature: \nMin Temperature: \nMax Humidity: \nMin Humidity: \nPress Rise/Fall: \nMax Light: \nMin Light: \nVolts: "
    global rhUnits
    rhUnits = "mm\nmph\nmph\ncom\n°\n%\nmB\n%\n%\nV "
    global dUnits
    dUnits = "mm\nmph\nmph\n°\n°\n%\n%\nrf\n%\n%\nV "
    global sdhHeaders
    sdhHeaders = "Date,Rain,WSpeed,MaxGust,AveDir,Temp,Humdty,Press,Light1,Light2,Batt"
    global sddHeaders
    sddHeaders = "Date,Rain,AvWSpd,MaxGust,MaxTemp,MinTemp,MaxHum,MinHum,RiseFall,MaxLgt,MinLgt,Battery"
    global compass
    compass = [ 'N', 'NNW', 'NW', 'WNW', 'W', 'WSW', 'SW', 'SSW', 'S', 'SSE', 'SE', 'ESE', 'E', 'ENE', 'NE', 'NNE', 'CLM', 'VAR', 'NUL' ]
    global msgs
    msgs =  []
    global MAX_MSGQ
    MAX_MSGQ = 5
    global NUM_ANALOG
    NUM_ANALOG = 32
    global NUM_POINTS
    NUM_POINTS = 16
    global C2A
    C2A = [3, 14, 13, 22, 19, 27, 25, 31, 29, 30, 20, 23, 16, 18, 5, 8]
    global NO_WD
    NO_WD = 16
    global VAR_WD
    VAR_WD = 17
    global NUL_WD
    NUL_WD = 18
    global MIN_BAR
    MIN_BAR = 0.05

    #Cruncher ratios
    global CR_RAIN
    CR_RAIN = 0.51  # tips => mm of rain
    global CR_SPEED
    CR_SPEED = .97  # revs / 3s => mph

    