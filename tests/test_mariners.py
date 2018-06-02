from .util import newGame
from core.player import IllegalMoveError
import factions.mariners as mariners


def testFish():
    game, p0, p1 = newGame(mariners.Mariner)
    game.start()

    p0.endTurn()

    p1.endPhase(fish=True)
    toReplace = p1.hand[:3]
    p1.fishReplace(toReplace)

    # Make sure cards are bottomdecked
    assert p1.deck[:3] == toReplace

    # Can't put back cards unless we're fishing
    try:
        p1.fishReplace(p1.hand[:3])
    except IllegalMoveError:
        pass
    else:
        assert False

    p1.endTurn()

    p0.endPhase(fish=True)

    # Have to decide what to put back
    try:
        p0.endTurn()
    except IllegalMoveError:
        pass
    else:
        assert False

    # Must put back 3
    try:
        p0.fishReplace(p1.hand[:2])
    except IllegalMoveError:
        pass
    else:
        assert False
