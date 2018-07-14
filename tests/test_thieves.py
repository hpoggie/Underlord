from .util import newGame
import factions.base as base
import factions.thieves as thieves
from core.player import IllegalMoveError


def testThiefAbility():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Sweep')
    c.zone = p1.facedowns

    p1.endTurn()
    p0.thiefAbility(p0.hand[0], 'Sweep', c)
    assert c.zone is p0.faceups

    try:
        p0.thiefAbility(p0.hand[0], 'Sweep', c)
    except IllegalMoveError:
        pass
    else:
        assert False


def testFog():
    game, p0, p1 = newGame([thieves.fog()], [base.spellBlade()])
    game.start()

    p0.endPhase()
    p0.play(0)
    p0.endTurn()

    p1.mana = 3
    p1.playFaceup(0, p0.facedowns[0])
    assert len(p0.facedowns) == 1


def testHydra():
    game, p0, p1 = newGame(
        [thieves.hydra()],
        [thieves.fog() for i in range(4)])
    game.start()

    hydra = p0.hand[0]
    hydra.zone = p0.faceups
    for c in p1.hand[:]:
        c.zone = p1.faceups

    p0.endPhase()
    for i in range(3):
        p0.attack(hydra, p1.faceups[0])

    assert len(p1.faceups) == 1
    try:
        p0.attack(hydra, p1.faceups[0])
    except IllegalMoveError:
        pass
    else:
        assert False


def testHeadLightning():
    game, p0, p1 = newGame(thieves.Thief)

    hl = next(c for c in p0.deck if c.name == "Head Lightning")
    hl.zone = p0.hand
    hl.playsFaceUp = True

    oldHandSize = len(p0.hand)
    p0.playFaceup(hl)
    assert len(p0.hand) == oldHandSize + 2  # Play 1, draw 3
    p0.replace([p0.hand[0], p0.hand[1]])
    assert len(p0.hand) == oldHandSize
