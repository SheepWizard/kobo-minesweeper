import argparse
from common import Cell, Game
from random import randrange
import math
from draw import drawCellsBatch, drawCloseIcon, drawTimer, drawFlagCount, closeDraw, initDraw, drawCell, drawSmile, getScreenSize, refreshScreen, disableRefresh, enableRefresh
import time
import threading
from stack import Stack
from shell import killNickel, restartNickel
from koboInput import initKoboInput, closeKoboInput, addKoboInputListener, removeKoboInputListener, ListenerName

running = True


def nonRepeatingNumbers(maxNumber: int):
    array: list[int] = [i for i in range(maxNumber)]

    def getNumber():
        nonlocal maxNumber
        if maxNumber < 0:
            return
        random = randrange(0, maxNumber)
        number = array[random]
        array[random] = array[maxNumber-1]
        array[maxNumber-1] = number
        maxNumber -= 1
        return number

    return getNumber


def getCellNeighbours(game: Game, x: int, y: int) -> list[Cell]:
    neighbours: list[Cell] = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            newX = i+x
            newY = j+y
            if (x != newX or y != newY) and newX > -1 and newY > -1 and newX < game.maxX and newY < game.maxY:
                neighbours.append(game.cells[newX][newY])

    return neighbours


def generateGrid(maxX: int, maxY: int) -> list[list[Cell]]:
    cellList = []
    for x in range(maxX):
        cellList.append([])
        for y in range(maxY):
            cellList[x].append(Cell(x, y))

    return cellList


def placeMines(game: Game, mineCount: int) -> list[Cell]:
    randomNumberGenerator = nonRepeatingNumbers(game.maxX * game.maxY)
    cellsWithMines: list[Cell] = []
    for _ in range(mineCount):
        randomNumber = randomNumberGenerator()
        if randomNumber is None:
            continue

        x = math.floor(randomNumber % game.maxX)
        y = math.floor(randomNumber / game.maxX)

        game.cells[x][y].isMine = True

        cellsWithMines.append(game.cells[x][y])

    return cellsWithMines


def placeNumbers(game: Game, cellsWithMines: list[Cell]):
    for cell in cellsWithMines:
        neighbours = getCellNeighbours(game, cell.x, cell.y)
        for neighbourCell in neighbours:
            neighbourCell.number += 1


def moveMine(game: Game, cell: Cell):
    moved = False
    for y in range(game.maxY):
        for x in range(game.maxX):
            if game.cells[x][y].isMine:
                continue
            game.cells[x][y].isMine = True
            neighbours = getCellNeighbours(game, x, y)
            for neighbour in neighbours:
                neighbour.number += 1
            moved = True
            break
        if moved:
            break

    cell.isMine = False
    neighbours = getCellNeighbours(game, cell.x, cell.y)
    for neighbour in neighbours:
        neighbour.number -= 1


def openMultiple(game: Game, cell: Cell):
    myStack = Stack()
    cell.isOpen = True
    myStack.push(cell)
    cellsToDraw: list[Cell] = []
    while myStack.size() > 0:
        poppedCell = myStack.pop()
        neighbours = getCellNeighbours(game, poppedCell.x, poppedCell.y)

        for neighbour in neighbours:
            if not neighbour.isFlagged and not neighbour.isOpen:
                neighbour.isOpen = True
                game.nonMineCellsOpened += 1
                if neighbour.number == 0:
                    myStack.push(neighbour)
                cellsToDraw.append(neighbour)
    drawCellsBatch(game, cellsToDraw)


def endGame(game: Game, won: bool):
    game.gameOver = True
    if not won:
        game.hitMine = True
        for row in game.cells:
            for cell in row:
                cell.isOpen = True

    else:
        for row in game.cells:
            for cell in row:
                if cell.isOpen:
                    continue
                cell.isFlagged = True

    timeDiff = (time.time() * 1000) - game.startTime
    drawBoard(game)
    drawTimer(math.floor(timeDiff / 1000))
    drawFlagCount(0)


def checkWin(game: Game):
    if game.nonMineCellsOpened < (game.maxX * game.maxY) - game.minesCount:
        return
    endGame(game, True)


def flagCell(game: Game, cell: Cell):
    if cell.isFlagged:
        cell.isFlagged = False
        game.flagsPlaced -= 1
    else:
        if not cell.isOpen:
            cell.isFlagged = True
            game.flagsPlaced += 1

    drawCell(game, cell)
    drawFlagCount(game.minesCount - game.flagsPlaced)


def openCell(game: Game, cell: Cell):
    if game.clicks == 0:
        if cell.isMine:
            moveMine(game, cell)
            openCell(game, cell)
            return
        game.startTime = int(time.time() * 1000)

    if not cell.isFlagged and not cell.isOpen:
        if cell.isMine:
            cell.isOpen = True
            endGame(game, False)
        else:
            if cell.number == 0:
                openMultiple(game, cell)
            else:
                cell.isOpen = True
            game.nonMineCellsOpened += 1

    game.clicks += 1
    drawCell(game, cell)
    checkWin(game)


def createGame(x: int, y: int, mines: int):
    currentGame = Game(generateGrid(x, y), x, y, mines)
    cellsWithMines = placeMines(
        currentGame, currentGame.minesCount)
    placeNumbers(currentGame, cellsWithMines)
    return currentGame


def drawBoard(game: Game):
    enableRefresh()
    drawSmile(game)
    drawTimer(0)
    drawFlagCount(game.minesCount)
    drawCloseIcon()
    disableRefresh()
    refreshScreen()
    cellsToDraw: list[Cell] = []
    for cell1 in game.cells:
        for cell2 in cell1:
            cellsToDraw.append(cell2)

    drawCellsBatch(game, cellsToDraw)


def getCellTouched(game: Game, touchX: int, touchY: int):
    for rows in game.cells:
        for cell in rows:
            x = cell.screenX
            y = cell.screenY
            x2 = x + cell.size
            y2 = y + cell.size
            if x <= touchX <= x2 and y <= touchY <= y2:
                return cell


def isSmileTouched(game: Game, touchX: int, touchY: int):
    x1, x2, y1, y2 = game.smileRect
    if x1 <= touchX <= x2 and y1 <= touchY <= y2:
        return True
    return False


def isCloseTouched(touchX: int, touchY: int):
    if 0 <= touchX <= 120 and 0 <= touchY < 120:
        return True
    return False


def handleTap(game: Game, touchX: int, touchY: int):
    global running
    closeTouched = isCloseTouched(touchX, touchY)

    if closeTouched:
        running = False
        return

    smileTouched = isSmileTouched(game, touchX, touchY)

    if smileTouched:
        removeListeners(game)
        newGame = createGame(game.maxX, game.maxY, game.minesCount)
        t = threading.Thread(target=drawBoard, args=(newGame,))
        t.start()
        addListeners(newGame)
        return

    if game.gameOver:
        return

    touchedCell = getCellTouched(game, touchX, touchY)

    if touchedCell is None:
        return

    openCell(game, touchedCell)


def handleHoldEnd(game: Game, touchX: int, touchY: int):
    if game.gameOver:
        return
    touchedCell = getCellTouched(game, touchX, touchY)

    if touchedCell is None:
        return

    flagCell(game, touchedCell)


def addListeners(game: Game):
    tapListener = addKoboInputListener(ListenerName.onTap, lambda x,
                                       y: handleTap(game, x, y))
    holdEndListener = addKoboInputListener(ListenerName.onHoldEnd, lambda x,
                                           y, _: handleHoldEnd(game, x, y))
    game.tapListener = tapListener
    game.holdEndListener = holdEndListener


def removeListeners(game: Game):
    if game.tapListener is not None:
        removeKoboInputListener(ListenerName.onTap, game.tapListener)
    if game.holdEndListener is not None:
        removeKoboInputListener(ListenerName.onHoldEnd, game.holdEndListener)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', dest='x', type=int, help='Number of rows')
    parser.add_argument('-y', dest='y', type=int, help='Number of columns')
    parser.add_argument('-mines', dest='mines',
                        type=int, help='Number of mines')
    args = parser.parse_args()
    x = args.x or 9
    y = args.y or 9
    mines = args.mines or 10

    if mines >= x * y:
        mines = (x*y) - 1

    killNickel()
    initDraw()
    screenWidth, _ = getScreenSize()
    initKoboInput(screenWidth, grabInput=False)

    currentGame = createGame(x, y, mines)
    drawBoard(currentGame)
    addListeners(currentGame)

    while running:
        continue

    closeKoboInput()
    closeDraw()
    restartNickel()
    print("Goodbye")


if __name__ == "__main__":
    main()
