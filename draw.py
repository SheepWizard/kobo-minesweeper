import sys
from _fbink import ffi, lib as FBInk
from PIL import Image
from common import Cell, Game
import math
import os

fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = True

path = os.path.dirname(__file__)

# add way to close fbfd


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


def drawSmile(game: Game):
    yPadding = 50
    screenWidth, _ = getScreenSize()

    smileSize = math.floor(screenWidth / 10)
    xPos = math.floor(screenWidth / 2 - (smileSize/2))

    smilePath = f"{path}/assets/smiley_play.png"

    if game.gameOver:
        if game.hitMine:
            smilePath = f"{path}/assets/smiley_dead.png"
        else:
            smilePath = f"{path}/assets/smiley_win.png"

    smileImage = Image.open(smilePath)
    smileImage = smileImage.resize((smileSize, smileSize))

    raw_data = smileImage.tobytes("raw")
    raw_len = len(raw_data)

    game.smileRect = (xPos, xPos + smileSize, yPadding, yPadding + smileSize)

    try:
        FBInk.fbink_print_raw_data(
            fbfd, raw_data, smileSize, smileSize, raw_len, xPos, yPadding, fbink_cfg)
    except Exception as e:
        print("drawSmile: ", e)
        FBInk.fbink_close(fbfd)


def drawCell(game: Game, cell: Cell):
    imageName = getCellImage(cell)

    screenWidth, screenHeight = getScreenSize()

    padding = 50
    cellSize = (math.floor(screenWidth / game.maxX) -
                (math.floor(padding*2 / game.maxX)))

    boardYSize = cellSize * game.maxY
    yDiff = screenHeight - boardYSize

    cellImage = Image.open(f"{path}/assets/{imageName}")
    cellImage = cellImage.resize((cellSize, cellSize))

    raw_data = cellImage.tobytes("raw")
    raw_len = len(raw_data)

    x = cell.x * cellSize + padding
    y = cell.y * cellSize + math.floor(yDiff / 2)

    cell.screenX = x
    cell.screenY = y
    cell.size = cellSize

    try:
        FBInk.fbink_print_raw_data(
            fbfd, raw_data, cellImage.width, cellImage.height, raw_len, x, y, fbink_cfg)
    except Exception as e:
        print("drawCell: ", e)
        FBInk.fbink_close(fbfd)


def getScreenSize() -> tuple[int, int]:
    return (state.screen_width, state.screen_height)


def refreshScreen():
    d = ffi.new("FBInkRect *")
    FBInk.fbink_cls(fbfd, fbink_cfg, d, True)


def closeDraw():
    refreshScreen()
    FBInk.fbink_close(fbfd)


def initDraw():
    screenWidth, screenHeight = getScreenSize()
    background = Image.new(mode="RGB", size=(
        screenWidth, screenHeight), color=(255, 255, 255))
    backgroundRaw = background.tobytes("raw")

    closeSize = 100

    close = Image.new(mode="RGBA", size=(
        closeSize, closeSize), color=(100, 100, 100))
    closeRaw = close.tobytes("raw")

    try:
        FBInk.fbink_print_raw_data(fbfd, backgroundRaw, background.width, background.height, len(
            backgroundRaw), 0, 0, fbink_cfg)
        FBInk.fbink_print_raw_data(
            fbfd, closeRaw, close.width, close.height, len(closeRaw), 0, 0, fbink_cfg)
    except Exception as e:
        print("initDraw: ", e)
        FBInk.fbink_close(fbfd)


fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
