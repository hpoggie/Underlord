class Turn ():
    p1 = 0
    p2 = 1


class Phase ():
    reveal = 0
    play = 1


class Zone ():
    face = 0
    faceup = 1
    facedown = 2
    hand = 3
    graveyard = 4


class IllegalMoveError (Exception):
    pass
