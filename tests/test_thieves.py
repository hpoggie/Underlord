from .util import newGame
import factions.base as base
import factions.thieves as thieves
from core.exceptions import IllegalMoveError


def testThiefAbility():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Elephant')
    c.zone = p1.facedowns

    p1.endTurn()
    p0.thiefAbility(p0.hand[0], 'Elephant', c)
    assert c.zone is p0.faceups

    try:
        p0.thiefAbility(p0.hand[0], 'Elephant', c)
    except IllegalMoveError:
        pass
    else:
        assert False

def testThiefAbilityWrongPhase():
    game, p0, p1 = newGame(thieves.Thief)
    game.start()

    p0.endTurn()
    p1.endPhase()
    p1.endPhase()
    c = next(c for c in p1.deck + p1.hand if c.name == 'Sweep')
    c.zone = p1.facedowns

    p1.endTurn()
    p0.endPhase()

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
    hl.fast = True

    oldHandSize = len(p0.hand)
    p0.playFaceup(hl)
    assert len(p0.hand) == oldHandSize + 2  # Play 1, draw 3
    p0.replace(p0.hand[0], p0.hand[1])
    assert len(p0.hand) == oldHandSize


def testEmblem():
    game, p0, p1 = newGame([thieves.roseEmblem() for i in range(2)])

    emblem = p0.deck[0]
    emblem.zone = p0.hand
    emblem.zone = p0.graveyard
    assert len(p0.hand) == 1


def testHeavyLightning():
    game, p0, p1 = newGame([thieves.heavyLightning()],
            [thieves.fog() for i in range(5)])
    game.start()

    p0.deck[:] = [thieves.fog() for i in range(5)]
    for c in p0.deck:
        c.owner = p0
        c._zone = p0.deck

    for c in p1.hand[:2]:
        c.zone = p1.faceups

    for c in p1.hand[:]:
        c.zone = p1.facedowns

    ltng = p0.hand[0]
    p0.mana = 11
    ltng.fast = True
    p0.playFaceup(ltng)

    assert len(p1.faceups) == 0
    assert len(p1.facedowns) == 0
    assert len(p0.hand) == 3
