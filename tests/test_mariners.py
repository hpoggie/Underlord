from .util import newGame
from core.exceptions import IllegalMoveError
import factions.mariners as mariners
import factions.base as base


def testFish():
    game, p0, p1 = newGame(mariners.Mariner)
    game.start()

    p0.endTurn()

    p1.endPhase(fish=True)
    toReplace = p1.hand[:3]
    p1.replace(*toReplace)

    # Make sure cards are bottomdecked
    assert p1.deck[:3] == toReplace

    # Can't put back cards unless we're fishing
    try:
        p1.replace(p1.hand[:3])
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
        p0.replace(*(p1.hand[:2] + [None]))
    except IllegalMoveError:
        pass
    else:
        assert False


def testAquatic():
    game, p0, p1 = newGame([mariners.nuisanceFlooding(),
                           mariners.kraken()])

    for i in range(2):
        p0.drawCard()
        p1.drawCard()

    game.start()
    p0.manaCap = 7  # Make sure we have enough to play our stuff

    p0.endPhase()
    p0.play(0)
    p0.endTurn()

    p1.endTurn()

    # We can't reveal aquatic cards
    try:
        p0.revealFacedown(0)
    except IllegalMoveError:
        pass
    else:
        assert False

    # Cheat Nuisance Flooding into play
    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(0)

    # Try revealing the kraken again
    p0.revealFacedown(0)


def testRipCurrent():
    game, p0, p1 = newGame([mariners.ripCurrent()],
                           [mariners.kraken() for i in range(2)])
    game.start()
    game.flooded = True  # So we can play the cards

    p0.endPhase()
    p0.play(0)
    p0.endTurn()
    p0.manaCap = 9  # Cheat

    p1.hand[0].cost = 0
    p1.hand[0].fast = True
    p1.playFaceup(0)
    p1.endPhase()
    p1.play(0)
    p1.endTurn()

    p0.revealFacedown(0)

    assert len(p1.faceups) == 0
    assert len(p1.facedowns) == 0


def testShark():
    game, p0, p1 = newGame([mariners.highTide()],
                           [mariners.unexpectedShark()])
    game.start()

    p0.endPhase()
    p0.play(0)
    p0.endTurn()

    p1.hand[0].cost = 0
    p1.playFaceup(0)
    p1.endPhase()
    p1.attack(0, p0.facedowns[0])

    assert len(p0.facedowns) == 0

    p1.endTurn()

    assert len(p1.faceups) == 0


def testBraintwister():
    game, p0, p1 = newGame([mariners.braintwister()],
                           [mariners.kraken() for i in range(5)])
    game.start()
    game.flooded = True

    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(0)

    assert(len(p1.hand) == 4)


def testBraintwisterEmptyHand():
    game, p0, p1 = newGame([mariners.braintwister()],
                           [])
    game.start()
    game.flooded = True

    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(0)

    assert(len(p1.hand) == 0)


def testSquid():
    game, p0, p1 = newGame([mariners.grandJelly()],
                           [mariners.humboldtSquid()])
    game.start()
    game.flooded = True

    # play the elephant
    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(0)
    p0.endTurn()

    # Play and attack with the squid
    squid = p1.hand[0]
    squid.fast = True
    p1.playFaceup(squid)
    p1.endPhase()
    assert squid.rank == 1
    assert len(p0.faceups) == 1
    p1.attack(squid, p0.faceups[0])
    assert len(p0.faceups) == 0

    # The squid returns to rank 1 after it's finished fighting
    assert squid.rank == 1


def testAquaticMCT():
    game, p0, p1 = newGame([mariners.highTide(), mariners.humboldtSquid()],
                           [base.mindControlTrap()])
    p0.drawCard()  # Make sure hand is in order
    game.start()

    p0.endPhase()

    # Play the high tide & squid
    squid, highTide = p0.hand
    p0.play(highTide)
    p0.play(squid)

    p0.endTurn()

    p1.endPhase()
    p1.play(0)  # Play the MCT
    p1.endTurn()

    p0.revealFacedown(highTide)
    p0.revealFacedown(squid)
    p0.endPhase()
    p0.attack(squid, p1.facedowns[0])

    p0.endTurn()

    assert squid.zone is p0.hand
