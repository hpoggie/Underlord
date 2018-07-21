import factions.fae as fae
from .util import newGame


def test_fae_ability():
    game, p0, p1 = newGame(fae.Faerie)
    game.start()
    p0.hand[0].zone = p0.facedowns
    p0.hand[0].zone = p0.facedowns
    p0.endPhase(p0.facedowns[0])
    assert len(p0.facedowns) == 1
