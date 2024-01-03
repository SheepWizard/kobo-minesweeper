from _fbink import ffi, lib as FBInk
from PIL import Image
from common import Cell, Game
import math
import os

fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = True

path = os.path.dirname(__file__)

dotDisplayImages = [
    "number_0.png",
    "number_1.png",
    "number_2.png",
    "number_3.png",
    "number_4.png",
    "number_5.png",
    "number_6.png",
    "number_7.png",
    "number_8.png",
    "number_9.png",
]


def getImageNameFromNumber(number: int):
    if number >= 1 and number <= 8:
        return f"cell_{number}.png"

    return "cell_open.png"


def getCellImage(cell: Cell):
    if not cell.isOpen:
        if cell.isFlagged:
            return "cell_flag.png"
        return "cell_hidden.png"

    if cell.isMine:
        return "cell_mine.png"

    return getImageNameFromNumber(cell.number)


def displayImage(path: str, width: int, height: int, xPos: int, yPos: int):
    image = Image.open(path)
    image = image.resize((width, height))

    rawData = image.tobytes("raw")
    rawLen = len(rawData)

    try:
        FBInk.fbink_print_raw_data(
            fbfd, rawData, width, height, rawLen, xPos, yPos, fbink_cfg)
    except Exception as e:
        print("Fails to draw: ", e)


def drawDotDisplay(number: int, position: str):
    yPadding = 120
    xPadding = 50
    screenWidth, _ = getScreenSize()

    digitHeight = math.floor(screenWidth / 10)
    digitWidth = math.floor(digitHeight / 2)

    number = max(-99, min(number, 999))

    string = str(number)
    offset = 3 - len(string)

    xStart = xPadding
    if position == "right":
        xStart = screenWidth - xPadding - (digitWidth*3)

    for i in range(3):
        if i >= offset:
            subStr = string[i-offset]
            if subStr == "-":
                imagePath = f"{path}/assets/number_blank.png"
                displayImage(imagePath, digitWidth,
                             digitHeight, xStart, yPadding)
            else:
                imagePath = f"{path}/assets/{dotDisplayImages[int(subStr)]}"
                displayImage(imagePath, digitWidth,
                             digitHeight, xStart, yPadding)
        else:
            imagePath = f"{path}/assets/{dotDisplayImages[0]}"
            displayImage(imagePath, digitWidth, digitHeight, xStart, yPadding)
        xStart += digitWidth


def drawSmile(game: Game):
    yPadding = 120
    screenWidth, _ = getScreenSize()

    smileSize = math.floor(screenWidth / 10)
    xPos = math.floor(screenWidth / 2 - (smileSize/2))

    smilePath = f"{path}/assets/smiley_play.png"

    if game.gameOver:
        if game.hitMine:
            smilePath = f"{path}/assets/smiley_dead.png"
        else:
            smilePath = f"{path}/assets/smiley_win.png"

    game.smileRect = (xPos, xPos + smileSize, yPadding, yPadding + smileSize)

    displayImage(smilePath, smileSize, smileSize, xPos, yPadding)


def drawCell(game: Game, cell: Cell):
    imageName = getCellImage(cell)

    screenWidth, screenHeight = getScreenSize()

    xPadding = 50
    yPadding = 60
    cellSize = (math.floor(screenWidth / game.maxX) -
                (math.floor(xPadding*2 / game.maxX)))

    boardYSize = cellSize * game.maxY
    yDiff = screenHeight - boardYSize

    cellImagePath = f"{path}/assets/{imageName}"

    x = cell.x * cellSize + xPadding
    y = cell.y * cellSize + math.floor(yDiff / 2) + yPadding

    cell.screenX = x
    cell.screenY = y
    cell.size = cellSize

    displayImage(cellImagePath, cellSize, cellSize, x, y)


def drawCellsBatch(game: Game, cells: list[Cell]):
    disableRefresh()
    for i, cell in enumerate(cells):
        if i % 20 == 0:
            refreshScreen()
        drawCell(game, cell)

    enableRefresh()
    refreshScreen()


def drawTimer(number: int):
    drawDotDisplay(number, "right")


def drawFlagCount(number: int):
    drawDotDisplay(number, "left")


def drawCloseIcon():
    closePath = f"{path}/assets/close.jpg"
    displayImage(closePath, 60, 60, 0, 0)


def getScreenSize() -> tuple[int, int]:
    return (state.screen_width, state.screen_height)


def refreshScreen():
    FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, fbink_cfg)


def disableRefresh():
    fbink_cfg.no_refresh = True


def enableRefresh():
    fbink_cfg.no_refresh = False


def closeDraw():
    refreshScreen()
    FBInk.fbink_close(fbfd)


def initDraw():
    screenWidth, screenHeight = getScreenSize()
    background = Image.new(mode="RGB", size=(
        screenWidth, screenHeight), color=(255, 255, 255))
    backgroundRaw = background.tobytes("raw")

    try:
        FBInk.fbink_print_raw_data(fbfd, backgroundRaw, background.width, background.height, len(
            backgroundRaw), 0, 0, fbink_cfg)
    except Exception as e:
        print("initDraw: ", e)
        FBInk.fbink_close(fbfd)


fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
