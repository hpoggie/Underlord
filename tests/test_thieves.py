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
