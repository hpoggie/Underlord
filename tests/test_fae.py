from core.card import Card
from core.game import destroy
from core.exceptions import InvalidTargetError, IllegalMoveError
import factions.fae as fae
from .util import newGame
from . import dummyCards


def test_fae_ability():
    game, p0, p1 = newGame(fae.Faerie)
    game.start()
    p0.hand[0].zone = p0.facedowns
    p0.hand[0].zone = p0.facedowns
    p0.endPhase(p0.facedowns[0])
    assert len(p0.facedowns) == 1


def test_illusions():
    game, p0, p1 = newGame()

    class DummyIllusion(Card):
        name = "Dummy Illusion"
        cost = 1
        rank = 'il'

    one = dummyCards.one(owner=p0, game=game)
    one.zone = p0.faceups
    di = DummyIllusion(owner=p1, game=game)
    assert di.illusion
    di.zone = p1.facedowns

    p0.endPhase()
    p0.attack(one, di)

    assert di.zone == p1.graveyard


def test_precise_discard():
    game, p0, p1 = newGame()

    pd = fae.preciseDiscard(owner=p0, game=game, zone=p0.facedowns)
    one = dummyCards.one(owner=p1, game=game, zone=p1.hand)

    p0.mana = 2
    p0.revealFacedown(pd)
    p0.replace(one)
    assert one.zone is p1.graveyard


def test_faerie_dragon():
    game, p0, p1 = newGame()

    fd = fae.faerieDragon(owner=p0, game=game, zone=p0.faceups)
    destroy(fd)

    assert fd.zone is p0.hand


def test_mesmerism():
    game, p0, p1 = newGame()

    c1 = dummyCards.one(owner=p1, game=game, zone=p1.faceups)
    c2 = dummyCards.one(owner=p1, game=game, zone=p1.faceups)
    c3 = dummyCards.one(owner=p1, game=game, zone=p1.faceups)

    mes = fae.mesmerism(owner=p0, game=game, zone=p0.facedowns)
    p0.mana = 2
    p0.revealFacedown(mes)

    assert len(p1.faceups) == 0


def test_return_to_sender():
    game, p0, p1 = newGame()

    for i in range(3):
        dummyCards.one(owner=p1, game=game, zone=p1.facedowns)

    rts = fae.returnToSender(owner=p0, game=game, zone=p0.facedowns)
    p0.mana = 3
    p0.revealFacedown(rts)

    assert len(p1.facedowns) == 0
    assert len(p1.hand) == 3


def test_enchanters_trap():
    game, p0, p1 = newGame()

    et = fae.enchantersTrap(owner=p0, game=game, zone=p0.facedowns)
    assert et.zone is p0.facedowns
    et.zone = p0.faceups
    assert et.zone is p0.facedowns


def test_radiance():
    game, p0, p1 = newGame()

    rad = fae.radiance(owner=p0, game=game, zone=p0.facedowns)
    one = dummyCards.one(owner=p0, game=game, zone=p0.faceups)
    dummyCards.one(owner=p1, game=game, zone=p1.hand)
    dummyCards.one(owner=p1, game=game, zone=p1.hand)
    assert len(p1.hand) == 2
    p0.mana = 4
    p0.revealFacedown(rad)
    p0.endPhase()
    p0.attack(one, p1.face)
    assert p1.manaCap == 2
    assert len(p1.hand) == 1


def test_fire_dust():
    game, p0, p1 = newGame()

    one = dummyCards.one(owner=p0, game=game, zone=p0.faceups)
    two = dummyCards.one(owner=p1, game=game, zone=p1.faceups)
    two.rank = 2
    fae.fireDust(owner=p0, game=game, zone=p0.faceups)
    assert one.rank == 1
    assert two.rank == 2

    p0.endPhase()
    p0.attack(one, two)
    assert one.zone is p0.graveyard
    assert two.zone is p1.graveyard


def test_titanias_guard():
    game, p0, p1 = newGame()

    tg = fae.titaniasGuard(owner=p0, game=game, zone=p0.facedowns)

    p0.mana = 4

    try:
        p0.revealFacedown(tg, None)
    except InvalidTargetError:
        pass


def test_oberons_guard():
    game, p0, p1 = newGame()

    og = fae.oberonsGuard(owner=p0, game=game, zone=p0.facedowns)
    p0.mana = 2
    p0.revealFacedown(og, None)
