from dataclasses import dataclass
import argparse
from common import Cell, Game
from random import randrange
import math
from draw import drawCell, drawSmile, getScreenSize
import KIP
import time
from stack import Stack

touchPath = "/dev/input/event1"

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

def getCellNeighbours(cells: list[list[Cell]], x: int, y: int):
    neighbours: list[Cell] = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            newX = i+x
            newY = j+y
            if (x != newX or y != newY) and newX > -1 and newY > -1 and newX < len(cells) and newY < len(cells[newX]):
                neighbours.append(cells[newY][newX])

    return neighbours

def generateGrid(x: int, y: int) -> list[list[Cell]]:
    return [[Cell(i, j) for i in range(x)] for j in range(y)]

def placeMines(cells: list[list[Cell]], maxX: int, mineCount: int) -> list[Cell]:
    randomNumberGenerator = nonRepeatingNumbers(len(cells) * len(cells[0]))
    cellsWithMines: list[Cell] = []
    for _ in range(mineCount):
        randomNumber = randomNumberGenerator()
        if randomNumber == None:
            continue

        x = math.floor(randomNumber % maxX)
        y = math.floor(randomNumber / maxX)

        cells[x][y].isMine = True

        cellsWithMines.append(cells[x][y])

    return cellsWithMines


def placeNumbers(cells: list[list[Cell]], cellsWithMines: list[Cell]):
    for cell in cellsWithMines:
        neighbours = getCellNeighbours(cells, cell.x, cell.y)
        for neighbourCell in neighbours:
            neighbourCell.number += 1

def moveMine(game: Game, cell: Cell):
    moved = False
    for y in range(game.maxY):
        for x in range(game.maxX):
            if game.cells[y][x].isMine:
                continue
            game.cells[y][x].isMine = True
            neighbours = getCellNeighbours(game.cells, x, y)
            for neighbour in neighbours:
                neighbour.number += 1
            moved = True
            break
        if moved:
            break

    cell.isMine = False
    neighbours = getCellNeighbours(game.cells, cell.x, cell.y)
    for neighbour in neighbours:
        neighbour.number -= 1
    
    

def openMultiple(game: Game, cell: Cell):
    myStack = Stack()
    cell.isOpen = True
    myStack.push(cell)

    while myStack.size() > 0:
        poppedCell = myStack.pop()
        neighbours = getCellNeighbours(game.cells, poppedCell.x, poppedCell.y)

        for neighbour in neighbours:
            if not neighbour.isFlagged and not neighbour.isOpen:
                neighbour.isOpen = True
                game.nonMineCellsOpened += 1
                if neighbour.number == 0:
                    myStack.push(neighbour)
                drawCell(game, neighbour)

def openCell(game: Game, cell: Cell):
    if game.clicks == 0:
        if cell.isMine:
            moveMine(game, cell)
            openCell(game, cell)
            return
        # start timer 
        
    if not cell.isFlagged and not cell.isOpen:
        if cell.isMine:
            cell.isOpen = True
            game.gameOver = True
            # end game
        else:
            if cell.number == 0:
                openMultiple(game, cell)
            else:
                cell.isOpen = True
            game.nonMineCellsOpened += 1

    game.clicks += 1
    drawCell(game, cell)
    # check win
    

def createGame(x: int, y: int, mines: int):
    currentGame = Game(generateGrid(x,y), x, y, mines)
    cellsWithMines = placeMines(currentGame.cells, currentGame.maxX, currentGame.minesCount)
    placeNumbers(currentGame.cells, cellsWithMines)
    return currentGame

def drawBoard(game: Game):
    for cell1 in game.cells:
        for cell2 in cell1:
            drawCell(game, cell2)
    drawSmile(game)

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

def debouncer(timeMs: int):
    lastTouchTime = time.time() * 1000

    def checkDebounce():
        nonlocal lastTouchTime
        if lastTouchTime + timeMs > time.time() * 1000:
            return True

        lastTouchTime = time.time() * 1000
        return False
    return checkDebounce

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', dest='x', type=int, help='')
    parser.add_argument('-y', dest='y', type=int, help='')
    parser.add_argument('-mines', dest='mines', type=int, help='')
    args = parser.parse_args()
    x = args.x or 9
    y = args.y or 9
    mines = args.mines or 10

    # check if mines is greater then board size
    
    currentGame = createGame(x,y,mines)
    drawBoard(currentGame)
    screenWidth, screenHeight = getScreenSize()
    touch = KIP.inputObject(touchPath, screenWidth, screenHeight, grabInput=True)
    debounce = debouncer(200)
    
    while True:
        touchX, touchY, err = touch.getInput()

        if err:
            continue

        if debounce():
            continue
        print("touch input") # gets spammed on restart for some reason
        smileTouched = isSmileTouched(currentGame, touchX, touchY)
    
        if smileTouched:
            currentGame = createGame(x,y,mines)
            drawBoard(currentGame)
            continue

        if currentGame.gameOver:
            continue

        touchedCell = getCellTouched(currentGame, touchX, touchY)

        if touchedCell is None:
            continue
        openCell(currentGame, touchedCell)

if __name__ == "__main__":
    main()
