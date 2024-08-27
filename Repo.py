import g
from WPackage import WPackage

# ------------------------------------------------------- Version of 27/07/2024 --------------------------------------------

# the main repository of the WPackage items
class Repo():
    # class attributes
    rtPackage = WPackage()
    rtPackage.blank('R')
    hrPackages = []
    dyPackages = []

    @classmethod
    def setup(cls):
        #first, fill WPackage hour and day arrays with dummy values
        _hrTemplate = WPackage()
        _hrTemplate.blank('H')
        _dyTemplate = WPackage()
        _dyTemplate.blank('D')
        _oneDay = []
        for x in range(0, g.HPD):
            _oneDay.append(_hrTemplate)
        for y in range(0, g.DPM):
            cls.hrPackages.append(_oneDay)
            cls.dyPackages.append(_dyTemplate)
    
    @classmethod
    #NB: chd == header char, hour, day (array index = day - 1)
    def deposit(cls, wp: WPackage):
        ch = wp.hdr
        hix = wp.hour
        dix = wp.dom
        if ch == 'R':
            cls.rtPackage = wp
        if ch == 'H':
            cls.hrPackages[dix - 1][hix] = wp
        if ch == 'D':
            cls.dyPackages[dix - 1] = wp
    
    @classmethod
    def retrieve(cls, chd):
        ch, hix, dix = chd
        if ch == 'R':
            return cls.rtPackage 
        if ch == 'H':
            return cls.hrPackages[dix - 1][hix]
        if ch == 'D':
            return cls.dyPackages[dix - 1]
        return None
