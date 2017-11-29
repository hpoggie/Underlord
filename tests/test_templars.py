from factions.templars import *
from core.decision import Decision
from factions import base
from .util import newGame
from core.enums import *
from core.player import IllegalMoveError


def testEquus():
    game, p0, p1 = newGame(equus())
    p0.deck[0].zone = p0.faceups
    p0.manaCap = 3
    assert p0.faceups[0].rank == 5
    p0.manaCap = 4
    assert p0.faceups[0].rank == 2


def testHolyHandGrenade():
    game, p0, p1 = newGame(
        [base.one(), base.one()],
        [holyHandGrenade(), holyHandGrenade()])
    p0.mana = 5
    p0.drawCard()
    p0.hand[0].playsFaceUp = True
    p0.playFaceup(p0.hand[0])
    p0.endPhase()
    p0.play(p0.hand[0])
    p0.endTurn()
    p1.mana = 8
    p1.drawCard()
    p1.drawCard()

    try:
        p1.playFaceup(p1.hand[0])
    except Decision as d:
        d.execute(p0.facedowns[0])

    assert len(p0.facedowns) == 0

    try:
        p1.playFaceup(p1.hand[0])
    except Decision as d:
        d.execute(p0.faceups[0])

    assert len(p0.facedowns) == 0


def testWrathOfGod():
    game, p0, p1 = newGame(
        [base.one(), base.one()],
        [wrathOfGod()])
    p0.drawCard()
    p0.drawCard()
    p0.hand[0].playsFaceUp = True
    p0.hand[0].cost = 0
    p0.hand[1].playsFaceUp = True
    p0.hand[1].cost = 0
    p0.playFaceup(p0.hand[0])
    p0.playFaceup(p0.hand[0])
    p0.endTurn()
    p1.drawCard()
    p1.hand[0].cost = 0
    p1.playFaceup(p1.hand[0])
    assert len(p0.faceups) == 0


def testMiracle():
    # TODO: be able to do something like [base.one()] * 10
    # doesn't currently work because base.one() only evaluates once
    game, p0, p1 = newGame([
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        base.one(),
        miracle()
    ])
    p0.drawCard()
    assert len(p0.hand) == 1
    p0.hand[0].playsFaceUp = True
    p0.hand[0].cost = 0
    p0.playFaceup(p0.hand[0])
    assert len(p0.hand) == 5


def testMiracleNotEnoughCards():
    game, p0, p1 = newGame(
        base.one(),
        base.one(),
        miracle()
    )
    p0.drawCard()
    assert len(p0.hand) == 1
    p0.hand[0].playsFaceUp = True
    p0.hand[0].cost = 0
    p0.playFaceup(p0.hand[0])
    assert len(p0.hand) == 2


def testGrail():
    game, p0, p1 = newGame()
    c = leftGrail()
    c.owner = p0
    c.zone = p0.faceups
    c = base.one()
    c.owner = p1
    c.zone = p1.faceups
    p1.faceups[0].hasAttacked = False
    game.turn = Turn.p2
    game.phase = Phase.play
    p0.manaCap = 3
    # Should fail if attack works
    try:
        p1.attack(p1.faceups[0], p0.face)
        assert False
    except IllegalMoveError:
        pass
    p0.manaCap = 2
    # Should fail if attack doesn't work
    p1.attack(p1.faceups[0], p0.face)
