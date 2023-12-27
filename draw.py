import sys
from _fbink import ffi, lib as FBInk
from PIL import Image
from common import Cell, Game
import math

fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg.is_centered = True
fbink_cfg.is_halfway = True
fbfd = FBInk.fbink_open()

# add way to close fbfd
 

def getImageNameFromNumber(number: int):
    if number >= 1 and number <= 8:
        return f"cell_{number}.png"

    return "cell_open.png"

def getCellImage(cell: Cell):
    if not cell.isOpen:
        return "cell_hidden.png"

    if cell.isMine:
        return "cell_mine.png"

    if cell.isFlagged:
        return "cell_flag.png"

    return getImageNameFromNumber(cell.number)

def drawSmile(game: Game):
    yPadding = 50
    screenWidth, _ = getScreenSize()

    smileSize = math.floor(screenWidth / 10)
    xPos = math.floor(screenWidth / 2 - smileSize)

    smileImage = Image.open(f"./assets/smiley_play.png")
    smileImage = smileImage.resize((smileSize,smileSize))

    raw_data = smileImage.tobytes("raw")
    raw_len = len(raw_data)

    game.smileRect = (xPos, xPos + smileSize, yPadding, yPadding + smileSize)
    
    try:
        FBInk.fbink_print_raw_data(fbfd,raw_data, smileSize, smileSize, raw_len, xPos, yPadding, fbink_cfg)
    finally:
        pass

def drawCell(game: Game, cell: Cell):
    imageName = getCellImage(cell)

    screenWidth, screenHeight = getScreenSize()
    
    padding = 50
    cellSize = (math.floor(screenWidth / game.maxX) - (math.floor(padding*2 / game.maxX)))

    boardYSize = cellSize * game.maxY
    yDiff = screenHeight - boardYSize
    
    cellImage = Image.open(f"./assets/{imageName}")
    cellImage = cellImage.resize((cellSize, cellSize))

    raw_data = cellImage.tobytes("raw")
    raw_len = len(raw_data)

    x = cell.x * cellSize + padding
    y = cell.y * cellSize + math.floor(yDiff / 2)

    cell.screenX = x
    cell.screenY = y
    cell.size = cellSize

    try:
        FBInk.fbink_print_raw_data(fbfd, raw_data, cellImage.width, cellImage.height, raw_len, x,y, fbink_cfg)
    finally:
        pass
    

def getScreenSize() -> (int, int):
    return (state.screen_width, state.screen_height)

FBInk.fbink_init(fbfd, fbink_cfg)
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
FBInk.fbink_refresh(fbfd,0,0,0,0,fbink_cfg)
background = Image.new(mode="RGB", size=(state.screen_width,state.screen_height), color=(255,255,255))
background_raw = background.tobytes("raw")
FBInk.fbink_print_raw_data(fbfd, background_raw, background.width, background.height, len(background_raw), 0, 0, fbink_cfg)







