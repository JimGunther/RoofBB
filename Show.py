from tkinter import *
from tkinter import ttk, font
from datetime import datetime, timezone, timedelta
import time
import g
from WPackage import WPackage
from Cruncher import Cruncher
from Repo import Repo

# ------------------------------------------- Version of 13/08/2024 ---------------------------------------------
            
class Display:
    #initial values
    g.init()
    displayMode = g.DM_RT
    dt = datetime.now(timezone.utc)
    hhix = dt.hour
    hdix = dt.day - 1
    dix = dt.day - 1
    
    def updateLabelNames(self):
        '''updateLabelNames(): produces string showing names of weather items (different for display mode g.DM_DY)
        parameters:
            self: current Display instance
        returns: string of weather item names sparated by newline characters (for use in main window text box)
        '''
        dmode = self.displayMode
        if dmode == g.DM_DY:
            names = g.dNames
        else:
            names = g.rhNames
        s = str()
        chunks = names.split('\n')
        for chk in chunks:
            s += chk + '\n'
        return s

    def updateMessages(self, mess):
        '''updateMessages(): updates the string for showing the list of messages
        parameters:
            self: current instance
            mess: current list of message strings
        returns: concatenated string with newline characters, suitable for text box display
        '''
        s = str()
        for m in mess:
            s += m.getLogEntry() + '\n'
        if len(g.msgs) == 0:
            s = 'No messages\n'
        return s
    
    def updateFooter(self):
        '''updateFooter(): updates the footer text with current date/time information
        parameters:
            self: current instance
        returns: string for display in footer
        '''
        t = time.localtime()
        fmt = "%A %d %B %Y %H:%M:%S"
        return time.strftime(fmt, t)

    def updateLabelValues(self, wp):
        '''updateLabelValues(): produces string to display given display mode, day (0-based) and hour indexes (from current WPackage and units string)
        parameters:
            self: current instance
            wp: WPackage to display
        returns: string to display in weather values text box
        '''
        dmode, dy, hr = self.getMix()
        uts = g.rhUnits
        if dmode == g.DM_DY:
            uts = g.dUnits
        return wp.makeLabelText(uts)

    def updateVarLabels(self, wp):
        '''updateVarLabels(): updates those labels which vary frequently
        parameters:
            self: current instance
            wp: current WPackage to show
        returns: none
        '''
        self.strValues.set(self.updateLabelValues(wp))
        self.strMessages.set(self.updateMessages(g.msgs))
        self.strFooter.set(self.updateFooter())

    def updateAllLabels(self, wp):
        '''updateAllLabels(): combination function to update all the text labels on the screen
        parameters:
            self: current instance
            wp: current WPackage to display
            returns: none
        '''
        self.updateVarLabels(wp)
        self.strNames.set(self.updateLabelNames())
        self.strRise.set(Cruncher.sunRiseSet().riseTime)
        self.strSet.set(Cruncher.sunRiseSet().setTime)

    # Button command handlers ------------------------------------------------------------------------------------

    def nowMode(self, *args):
        '''nowMode(): puts main window into realtime mode
        parameters:
            self: current instance
            *args: needed to conform to widget event handler profile (not used)
        returns: none
        '''
        self.displayMode = g.DM_RT
        self.strHeader.set('Weather Now')
        self.strNames.set(self.updateLabelNames())
        chd = Cruncher.mixtoCHD(self.getMix())
        wp = Repo.retrieve(chd)
        self.updateVarLabels(wp)

    def hoursMode(self, *args):
        '''hoursMode(): puts main window into 'hourly' mode
        parameters:
            self: current instance
            *args: needed to conform to widget event handler profile (not used)
        returns: none
        '''
        self.displayMode = g.DM_HR
        self.dt = datetime.now(timezone.utc)
        self.hhix = self.dt.hour
        self.dhix = self.dt.day - 1
        dst = time.localtime(time.time()).tm_isdst
        self.strHeader.set('Hourly: ' + str((self.dt.hour + dst) % g.HPD) + ':00 (Today)')
        self.strNames.set(self.updateLabelNames())
        chd = Cruncher.mixtoCHD(self.getMix())
        wp = Repo.retrieve(chd)
        self.updateVarLabels(wp)

    def daysMode(self, *args):
        '''daysMode(): puts main window into 'daily' mode
        parameters:
            self: current instance
            *args: needed to conform to widget event handler profile (not used)
        returns: none
        '''
        self.displayMode = g.DM_DY
        self.dt = datetime.now(timezone.utc)
        self.dix = self.dt.day - 1
        self.strHeader.set('Daily: ' + self.dt.strftime('%A'))
        self.strNames.set(self.updateLabelNames())
        chd = Cruncher.mixtoCHD(self.getMix())
        print('Days mode: ' + str(self.getMix()))
        wp = Repo.retrieve(chd)
        self.updateVarLabels(wp)

    def back(self, *args):
        '''back(): shows previous hour or day (hourly and daily modes); does nothing (realtime mode) (scrolls)
        parameters:
            self: current instance
            *args: needed to conform to widget event handler profile (not used)
        returns: none
        '''
        td = None
        if self.displayMode == g.DM_RT:
            return
        if self.displayMode == g.DM_HR:
            td = timedelta(hours=1)
            earliest = datetime.now(timezone.utc) - timedelta(hours=g.HPD)
        if self.displayMode == g.DM_DY:
            td = timedelta(days=1)
            earliest = datetime.now(timezone.utc) - timedelta(days=g.DPW)
        self.dt = self.dt - td
        if self.dt < earliest:
            if self.displayMode == g.DM_HR:
                self.dt += timedelta(hours=g.HPD)
            else:
                self.dt += timedelta(days=g.DPW)
        self.hhix = self.dt.hour
        self.hdix = self.dt.day - 1
        if self.displayMode == g.DM_HR:
            dst = time.localtime(time.time()).tm_isdst
            sYest = '(Today)'
            if self.dt.day < datetime.today().day:
                sYest = '(Yesterday)'
            self.strHeader.set('Hourly: ' + str((self.dt.hour + dst) % g.HPD) + ':00 ' + sYest)
        else:
            self.strHeader.set('Daily: ' + self.dt.strftime('%A'))
        chd = Cruncher.mixtoCHD(self.getMix())
        wp = Repo.retrieve(chd)
        self.updateVarLabels(wp)
    
    def fwd(self, *args):
        '''fwd(): shows next hour or day (hourly and daily modes); does nothing (realtime mode) (scrolls)
        parameters:
            self: current instance
            *args: needed to conform to widget event handler profile (not used)
        returns: none
        '''
        td = None
        if self.displayMode == g.DM_RT:
            return
        if self.displayMode == g.DM_HR:
            td = timedelta(hours=1)
            latest = datetime.now(timezone.utc)
        if self.displayMode == g.DM_DY:
            td = timedelta(days=1)
            latest = datetime.now(timezone.utc)
        self.dt = self.dt + td
        self.hhix = self.dt.hour
        self.hdix = self.dt.day - 1
        if self.dt > latest:
            if self.displayMode == g.DM_HR:
                self.dt -= timedelta(hours=g.HPD)
            else:
                self.dt -= timedelta(days=g.DPW)
        self.hhix = self.dt.hour
        self.hdix = self.dt.day - 1
        dst = time.localtime(time.time()).tm_isdst
        if self.displayMode == g.DM_HR:
            sYest = '(Today)'
            if self.dt.day < datetime.today().day:
                sYest = '(Yesterday)'
            self.strHeader.set('Hourly: ' + str((self.hhix + dst) % g.HPD) + ':00 ' + sYest)
        else:
            self.dix = self.dt.day - 1
            self.strHeader.set('Daily: ' + self.dt.strftime('%A'))
        chd = Cruncher.mixtoCHD(self.getMix())
        wp = Repo.retrieve(chd)
        self.updateVarLabels(wp)

    # Methods to layout and display GUI widgets ----------------------------------------------------------------------
    
    def middlePanels(self, parent): #parent is frmMiddle
        '''middlePanels(): GUI for child widgets of frmMiddle
        parameters:
            self: current instance
            parent: parent form: frmMiddle in this case
        returns: none
        '''
        # Tree view
        treeTree = ttk.Treeview(parent, style='Shed.Treeview', height=7)
        treeTree.insert('', 'end','now', text='Now')
        treeTree.insert('', 'end', '24hours', text='Last 24 hrs')
        treeTree.insert('', 'end', 'week', text='Last week')
        treeTree.insert('', 'end', 'archive', text='Archive')
        treeTree.grid(column=0, row=0, sticky=(N, W, S))

        # names panel (different for day listing)
        lblNames = ttk.Label(parent, name='names', textvariable=self.strNames, font=self.fntText, wraplength=260, background='#d0d0ff', justify='right', anchor='ne')
        lblNames.grid(column=1, row=0, sticky=(N, W, E, S))

        #values panel (variable)
        lblValues = ttk.Label(parent, name='values', textvariable=self.strValues, font=self.fntText, wraplength=240, background='#d0d0ff', justify='left', anchor='nw')
        lblValues.grid(column=2, row=0, sticky=(N, E, S))
       
    def bottomPanels(self, parent): # parent is frmLower
        '''bottomPanels(): GUI for child widgets of frmLower
        parameters:
            self: current instance
            parent: parent form: frmLower in this case
        returns: none
        '''
        frmSunRiseSet = ttk.Frame(parent, padding='3 3 3 3')
        frmSunRiseSet.grid(column=0, row=0, sticky=(W, E, S))
        lblSR = ttk.Label(frmSunRiseSet, name='sr', text='Sun rise: ', font=self.fntText, wraplength=150, anchor='nw')
        lblSS = ttk.Label(frmSunRiseSet, name='ss', text=' set: ', font=self.fntText, wraplength=100, anchor='nw')
        lblSunrise = ttk.Label(frmSunRiseSet, name='srise', textvariable=self.strRise, font=self.fntText, wraplength=300, anchor='nw')
        lblSunset = ttk.Label(frmSunRiseSet, name='sset', textvariable=self.strSet, font=self.fntText, wraplength=300, anchor='ne')
        lblSR.grid(column=0, row=0, sticky=(W, E, S))
        lblSunrise.grid(column=1, row=0, sticky=(W, E, S))
        lblSS.grid(column=2, row=0, sticky=(W, E, S))
        lblSunset.grid(column=3, row=0, sticky=(W, E, S))
        # row of buttons
        frmButtons = ttk.Frame(parent, padding="3 3 3 3")
        frmButtons.grid(column=0, row=1, sticky=(W, E, S))
        btnNow = ttk.Button(frmButtons, text='Now', style='Shed.TButton', command=self.nowMode).grid(column=0, row=0, sticky=(W, E, S))
        btnHours = ttk.Button(frmButtons, text='24 Hours', style='Shed.TButton', command=self.hoursMode).grid(column=1, row=0, sticky=(W, E, S))
        btnDays = ttk.Button(frmButtons, text='Week', style='Shed.TButton', command=self.daysMode).grid(column=2, row=0, sticky=(W, E, S))
        btnBack = ttk.Button(frmButtons, text='<<', style='Shed.TButton', command=self.back).grid(column=3, row=0, sticky=(W, E, S))
        btnFwd =ttk.Button(frmButtons, text='>>', style='Shed.TButton', command=self.fwd).grid(column=4, row=0, sticky=(W, E, S))
        btnOther = ttk.Button(frmButtons, text='Extras', style='Shed.TButton', command=self.nowMode).grid(column=5, row=0, sticky=(W, E, S))   ## NB temporary assignment of callback
        for child in frmButtons.winfo_children():
            child.grid_configure(padx=5, pady=5)
         
        # messages
        lblMessages = ttk.Label(parent, name='messages', textvariable=self.strMessages, font=self.fntMessages, wraplength=750, anchor='nw')
        lblMessages.grid(column=0, row=2, sticky=(W, E, S))
        
        #footer
        lblFooter = ttk.Label(parent, name='footer', textvariable=self.strFooter, font=self.fntHeader, foreground='white', background='#0000d0', anchor='center')
        lblFooter.grid(column=0, row=3, sticky=(W, E, S))

    def __init__(self, root):
        '''__init__() displays the title bar and 3 outer frames (frmTop, frmMiddle, frmLower). Also sets up styles, fonts and StringVar variables
        parameters:
            self: current instance
            root: TTk root frame
        returns: none
        '''
        # Window title bar and 3 outer frames
        root.title("Weather Station")
        frmTop = ttk.Frame(root, padding="3 3 3 3")
        frmTop.grid(column=0, row=0, sticky=(N, W, E))
        frmTop.columnconfigure(0, weight=1)
        frmTop.rowconfigure(0, weight=1)
        frmTop.rowconfigure(1, weight=1)
        frmMiddle = ttk.Frame(root, style='Shed.TFrame', padding="3 3 3 3")
        frmMiddle.grid(column=0, row=1, sticky=(N, W, E, S))
        frmMiddle.columnconfigure(0, minsize=120, weight=1)
        frmMiddle.columnconfigure(1, minsize=180, weight=1)
        frmMiddle.columnconfigure(2, minsize=80, weight=1)
        frmMiddle.rowconfigure(0, weight=1)
        frmBottom = ttk.Frame(root, style='Shed.TFrame', padding="3 3 3 3")
        frmBottom.grid(column=0, row=2, sticky=(W, E, S))
        frmBottom.columnconfigure(0, weight=1)
        frmBottom.rowconfigure(0, weight=1)
        frmBottom.rowconfigure(1, weight=1)
        frmBottom.rowconfigure(2, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        #define fonts to use
        self.fntTitle = font.Font(family='FreeSans', name='appFntTitle', size=40, weight='bold')
        self.fntHeader = font.Font(family='FreeSans', name='appFntHeader', size=32, weight='bold')
        self.fntText = font.Font(family='FreeSans', name='appFntText', size=22, weight='normal')
        self.fntMessages = font.Font(family='FreeSans', name='appFntMessages', size=16, slant='italic', weight='normal')
        
        # customised styles
        sFrame = ttk.Style()
        sFrame.configure('Shed.TFrame', background='#d0d0ff')
        sButton = ttk.Style()
        sButton.configure('Shed.TButton', font=self.fntText)
        sTree = ttk.Style()
        sTree.configure('Shed.Treeview', font=self.fntText, rowheight=40)
    
        # Title at top of window (fixed)
        lblTitle = ttk.Label(frmTop, name='title', text='MiS Bedford Weather', font=self.fntTitle, foreground='white', background='#0000d0', anchor='center')
        lblTitle.grid(column=0, row=0, sticky=(N, W, E))

        # Header (variable: by display mode)
        self.strHeader = StringVar()
        lblHeader = ttk.Label(frmTop, name='header', textvariable=self.strHeader, font=self.fntHeader, foreground = 'yellow', background='#4040ff', anchor='center')
        lblHeader.grid(column=0, row=1, sticky=(N, W, E))
        
        self.strNames = StringVar()
        self.strValues = StringVar()
        self.middlePanels(frmMiddle)

        self.strMessages = StringVar()
        self.strFooter = StringVar()

        self.strRise = StringVar()
        self.strSet = StringVar()
        self.bottomPanels(frmBottom)

        self.displayMode = g.DM_RT
        
    # Utility method(s) used mainly by other classes -----------------------------------------------------------
     
    def getMix(self):
        '''getMix(): returns a tuple: displayMode, day index, hour index (==0 for day Mode)
        parameters:
        self: current instance
        returns: mix tuple
        '''
        if self.displayMode == g.DM_RT:
            return (self.displayMode, 0, 0)
        if self.displayMode == g.DM_HR:
            return (self.displayMode, self.hdix, self.hhix)
        if self.displayMode == g.DM_DY:
            return (self.displayMode, self.dix, 0)
        return (0, 0, 0)
    
    
        
