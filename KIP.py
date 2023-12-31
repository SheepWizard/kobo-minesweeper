# Taken from https://github.com/Mavireck/Kobo-Input-Python and modified slightly

import os
import sys
import struct
from time import time
from fcntl import ioctl
import ctypes

evAbs = 3
evKey = 1
evSyn = 0

synReport = 0
synDropped = 3
synMTreport = 2
btnTouch = 330
absX = 0
absY = 1
absMTposX = 53
absMTposY = 54
absMTPressure = 58
absMTtouchWidthMajor = 48


touch_path = "/dev/input/event1"
# long int, long int, unsigned short, unsigned short, unsigned int
FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(FORMAT)

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

IOC_NONE = 0
IOC_WRITE = 1
IOC_READ = 2


def IOW(type, nr, size):
    return IOC(IOC_WRITE, type, nr, IOC_TYPECHECK(size))


def IOC_TYPECHECK(t):
    result = ctypes.sizeof(t)
    assert result <= _IOC_SIZEMASK, result
    return result


def IOC(dir, type, nr, size):
    assert dir <= _IOC_DIRMASK, dir
    assert type <= _IOC_TYPEMASK, type
    assert nr <= _IOC_NRMASK, nr
    assert size <= _IOC_SIZEMASK, size
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


def EVIOCGRAB(len): return IOW(ord('E'), 0x90, ctypes.c_int)


class inputObject:
    """
    Input object
    """

    def __init__(self, inputPath, vwidth, vheight, grabInput=False, debounceTime=0.2, touchAreaSize=7):
        self.inputPath = inputPath
        self.viewWidth = vwidth
        self.viewHeight = vheight
        self.devFile = open(inputPath, "rb")
        self.lastTouchTime = 0
        self.lastTouchArea = [-3, -3, -2, -2]
        self.touchDebounceTime = debounceTime
        self.lastTouchAreaSize = touchAreaSize
        self.isInputGrabbed = grabInput
        #os.set_blocking(self.devFile.fileno(), False)
        if grabInput:
            ioctl(self.devFile, EVIOCGRAB(1), True)

    def close(self):
        """ Closes the input event file """
        if self.isInputGrabbed:
            ioctl(self.devFile, EVIOCGRAB(1), False)
        self.devFile.close()
        return True

    def getEvtPacket(self):
        err = None
        evPacket = []
        badPacket = False
        while True:
            inp_tmp = self.devFile.read(EVENT_SIZE)
            if inp_tmp is None:
                return
            inp = struct.unpack(FORMAT, inp_tmp)
            if not inp:
                print("binary read failed ", inp)
                return None
            (TimeSec, TimeUsec, EvType, EvCode, EvValue) = inp
            if EvType == evSyn and EvCode == synDropped:
                # we need to ignore all packets up to, and including the next
                # SYN_REPORT
                badPacket = True
                evPacket = None
                continue
            if badPacket and EvType == evSyn and EvCode == synReport:
                # We encountered a SYN_DROPPED previously. Return with an error
                print("Error : bad event packet")
                return None
            if not badPacket:
                evPacket.append(inp)
                if EvType == evSyn and EvCode == synReport:
                    # We have a complete event packet
                    return evPacket

    def getInput(self):
        """
        Returns the rotated x,y coordinates of where the user touches
        """
        err = None
        x, y = -1, -1
        touchPressed = False
        touchReleased = False
        getEvAttempts = 0
        decodeEvAttempts = 0
        evPacket = self.getEvtPacket()
        if not evPacket:
            # We have to try again, increasing the attempts counter
            getEvAttempts += 1
            return None, None, None, None, True
        if getEvAttempts > 4:
            err = 1
            # print("oups error line 101 of KIP")
            return None, None, None, None, err
        # if we have got this far, we can reset the counter
        getEvAttempts = 0
        # Now to decode :
        for e in evPacket:
            if e[2] == evKey:
                if e[3] == 330:
                    if e[4] == 1:
                        touchPressed = True
                    else:
                        touchReleased = True
            elif e[2] == evAbs:
                if e[3] == absX:
                    x = int(e[4])
                elif e[3] == absY:
                    y = int(e[4])
                elif e[3] == absMTposX:
                    x = int(e[4])
                elif e[3] == absMTposY:
                    y = int(e[4])
                # Some kobo's seem to prefer using pressure to detect touch pressed/released
                elif e[3] == absMTPressure:
                    if e[4] > 0:
                        touchPressed = True
                    else:
                        touchReleased = True
                # And others use the ABS_MT_WIDTH_MAJOR (and ABS_MT_TOUCH_MAJOR too, but those
                # are also used and set to zero on other kobo versions) instead :(
                elif e[3] == absMTtouchWidthMajor:
                    if e[4] > 0:
                        touchPressed = True
                    else:
                        touchReleased = True
        ry = x
        rx = self.viewWidth - y + 1
        return (rx, ry, touchPressed, touchReleased, None)
