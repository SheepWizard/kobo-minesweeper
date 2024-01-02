from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Cell:
    x: int
    y: int
    number: int = 0
    isFlagged: bool = False
    isMine: bool = False
    isOpen: bool = False
    screenX: int = 0
    screenY: int = 0
    size: int = 0


@dataclass
class Game:
    cells: list[list[Cell]]
    maxX: int
    maxY: int
    minesCount: int
    flagsPlaced: int = 0
    nonMineCellsOpened: int = 0
    clicks: int = 0
    startTime: int = 0
    smileRect: tuple[int, int, int, int] = (0, 0, 0, 0)
    gameOver: bool = False
    hitMine: bool = False
    tapListener: Optional[Callable] = None
    holdEndListener: Optional[Callable] = None
