import struct
import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Final, Optional
from grabInput import grab, ungrab

# struct input_event {
#        struct timeval time; = {long seconds, long microseconds}
#        unsigned short type;
#        unsigned short code;
#        unsigned int value;
# };
FORMAT: Final[str] = 'llHHI'
EVENT_SIZE: Final[int] = struct.calcsize(FORMAT)

TOUCH_PATH: Final[str] = "/dev/input/event1"

NOT_INIT_MESSAGE: Final[str] = "Kobo input has not been initialized"


@dataclass
class EventType:
    EV_SYS: Final[int] = 0
    EV_KEY: Final[int] = 1
    EV_ABS: Final[int] = 3


@dataclass
class EventCode:
    BTN_TOUCH: Final[int] = 330
    ABS_MT_POSITION_X: Final[int] = 53
    ABS_MT_POSITION_Y: Final[int] = 54
    ABS_MT_PRESSURE: Final[int] = 58
    SYN_DROPPED: Final[int] = 3


@dataclass
class SwipeDirection:
    LEFT: Final[str] = "LEFT"
    RIGHT: Final[str] = "RIGHT"
    UP: Final[str] = "UP"
    DOWN: Final[str] = "DOWN"


@dataclass
class ListenerName:
    onTouchStart: Final[str] = "onTouchStart"
    onTouchEnd: Final[str] = "onTouchEnd"
    onTap: Final[str] = "onTap"
    onHoldEnd: Final[str] = "onHoldEnd"
    onTouchMove: Final[str] = "onTouchMove"
    onSwipe: Final[str] = "onSwipe"


@dataclass
class KoboInput:
    init: bool = True
    holdDelayMs: int = 200
    swipeDeadZone: int = 40
    isTouching: bool = False
    touchStartTime: int = 0
    currentX: int = 0
    currentY: int = 0
    touchStartX: int = 0
    touchStartY: int = 0
    viewWidth: int = 0
    grabInput: bool = True
    onTouchStart: list[Callable[[int, int], None]
                       ] = field(default_factory=list)
    onTouchEnd: list[Callable[[int, int], None]] = field(default_factory=list)
    onTap: list[Callable[[int, int], None]] = field(default_factory=list)
    onHoldEnd: list[Callable[[int, int, int], None]
                    ] = field(default_factory=list)
    onTouchMove: list[Callable[[int, int], None]] = field(default_factory=list)
    onSwipe: list[Callable[[str, int, int, int, int], None]
                  ] = field(default_factory=list)
    eventFile = open(TOUCH_PATH, "rb")


@dataclass
class Event:
    timeSeconds: int = 0
    timeMicroSeconds: int = 0
    eventType: int = 0
    code: int = 0
    value: int = 0


_koboInputObject: Optional[KoboInput] = None


def _getSwipeDirection(koboInput: KoboInput) -> Optional[str]:
    xDiff = koboInput.touchStartX - koboInput.currentX
    yDiff = koboInput.touchStartY - koboInput.currentY

    if abs(xDiff) > abs(yDiff):
        if abs(xDiff) < koboInput.swipeDeadZone:
            return
        if xDiff < 0:
            return SwipeDirection.RIGHT
        else:
            return SwipeDirection.LEFT
    else:
        if abs(yDiff) < koboInput.swipeDeadZone:
            return
        if yDiff < 0:
            return SwipeDirection.DOWN
        else:
            return SwipeDirection.UP


def _getEvent() -> Optional[Event]:
    if _koboInputObject is None:
        return None
    eventBytes: Optional[bytes] = None
    try:
        eventBytes = _koboInputObject.eventFile.read(EVENT_SIZE)
    except:
        return None
    if not eventBytes:
        return None
    unPackedEvent = struct.unpack(FORMAT, eventBytes)
    if not unPackedEvent:
        return None

    return Event(*unPackedEvent)


def _readPacket(koboInput: KoboInput, packet: list[Event]):
    x: Optional[int] = None
    y: Optional[int] = None
    translatedX: Optional[int] = None
    translatedY: Optional[int] = None
    touchStart = False
    touchEnd = False
    moveUpdated = False
    for event in packet:
        if event.eventType == EventType.EV_KEY and event.code == EventCode.BTN_TOUCH:
            if event.value == 1 and not koboInput.isTouching:
                touchStart = True
                koboInput.isTouching = True
                koboInput.touchStartTime = int(time.time() * 1000)
            elif event.value == 0 and koboInput.isTouching:
                touchEnd = True
                koboInput.isTouching = False
        if event.eventType == EventType.EV_ABS:
            if event.code == EventCode.ABS_MT_POSITION_X:
                moveUpdated = True
                x = event.value
            if event.code == EventCode.ABS_MT_POSITION_Y:
                moveUpdated = True
                y = event.value

    # Rotate coordinates
    if x:
        translatedY = x
    if y:
        translatedX = koboInput.viewWidth - y + 1

    if translatedY:
        koboInput.currentY = translatedY

    if translatedX:
        koboInput.currentX = translatedX

    if touchStart:
        koboInput.touchStartX = koboInput.currentX
        koboInput.touchStartY = koboInput.currentY
        for func in koboInput.onTouchStart:
            func(koboInput.currentX, koboInput.currentY)

    if touchEnd:
        timeDiff = int(time.time() * 1000) - \
            koboInput.touchStartTime
        for func in koboInput.onTouchEnd:
            func(koboInput.currentX, koboInput.currentY)
        if timeDiff < koboInput.holdDelayMs:
            for func in koboInput.onTap:
                func(koboInput.currentX, koboInput.currentY)
        else:
            for func in koboInput.onHoldEnd:
                func(koboInput.currentX, koboInput.currentY, timeDiff)

        swipeDirection = _getSwipeDirection(koboInput)
        if swipeDirection is not None:
            for func in koboInput.onSwipe:
                func(swipeDirection, koboInput.touchStartX,
                     koboInput.touchStartY, koboInput.currentX, koboInput.currentY)

    if moveUpdated:
        for func in koboInput.onTouchMove:
            func(koboInput.currentX, koboInput.currentY)


def closeKoboInput():
    global _koboInputObject
    if _koboInputObject is None:
        print(NOT_INIT_MESSAGE)
        return

    if _koboInputObject.grabInput:
        ungrab(_koboInputObject.eventFile)
    _koboInputObject.eventFile.close()
    _koboInputObject.onHoldEnd.clear()
    _koboInputObject.onSwipe.clear()
    _koboInputObject.onTap.clear()
    _koboInputObject.onTouchEnd.clear()
    _koboInputObject.onTouchMove.clear()
    _koboInputObject.onTouchStart.clear()
    _koboInputObject.init = False


def _task():
    global _koboInputObject
    if _koboInputObject is None:
        return
    eventPacket: list[Event] = []
    while _koboInputObject.init:
        event = _getEvent()
        if event is None:
            continue

        if event.eventType == EventType.EV_SYS and event.code == EventCode.SYN_DROPPED:
            # Bad packet, discard
            eventPacket.clear()
        eventPacket.append(event)
        if event.eventType == EventType.EV_SYS:
            _readPacket(_koboInputObject, eventPacket)
            eventPacket.clear()


def addKoboInputListener(name: str, func: Callable):
    if _koboInputObject is None:
        print(NOT_INIT_MESSAGE)
        return None
    eventList = None
    try:
        eventList = getattr(_koboInputObject, name)
    except:
        print(f"{name} is not a valid listener name")
        return None
    if eventList is None:
        return None
    if not isinstance(eventList, list):
        print(f"{name} is not a valid listener name")
        return None
    eventList.append(func)
    return func


def removeKoboInputListener(name: str, func: Callable):
    if _koboInputObject is None:
        print(NOT_INIT_MESSAGE)
        return False
    eventList = None
    try:
        eventList = getattr(_koboInputObject, name)
    except:
        print(f"{name} is not a valid listener name")
        return False
    if eventList is None:
        return False
    if not isinstance(eventList, list):
        print(f"{name} is not a valid listener name")
        return False
    newList = list(
        filter(lambda x: x != func, _koboInputObject.onTouchStart))
    setattr(_koboInputObject, name, newList)
    return True


def getKoboInputObject():
    return _koboInputObject


def initKoboInput(viewWidth: int, grabInput: bool = True):
    global _koboInputObject
    _koboInputObject = KoboInput(viewWidth=viewWidth, grabInput=grabInput)

    if _koboInputObject.grabInput:
        grab(_koboInputObject.eventFile)

    thread = threading.Thread(target=_task)
    thread.start()
