from enum import Enum


class GameStatus(Enum):
    CTA = 0
    COUNTDOWN = 1
    GAME = 2
    GOAL = 3
    OFFSIDE = 4
    END = 5
    BLANK = 6
