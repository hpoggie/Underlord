from factions.templars import *
from core.core import Game
from factions import base
from tests.dummyFaction import dummyFactionPlayer


def testEquus():
    dfp = dummyFactionPlayer([equus()])
    game = Game(dfp, dfp)
    game.players[0].moveCard(game.players[0].deck[0], Zone.faceup)
    game.players[0].manaCap = 3
    assert game.players[0].faceups[0].rank == 5
    game.players[0].manaCap = 4
    assert game.players[0].faceups[0].rank == 2


def testHolyHandGrenade():
    dfp1 = dummyFactionPlayer([base.one(), base.one()])
    dfp2 = dummyFactionPlayer([holyHandGrenade(), holyHandGrenade()])
    game = Game(dfp1, dfp2)
    game.players[0].mana = 5
    game.players[0].drawCard()
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].endPhase()
    game.players[0].play(game.players[0].hand[0])
    game.players[0].endTurn()
    game.players[1].mana = 8
    game.players[1].drawCard()
    game.players[1].drawCard()
    game.players[1].playFaceup(game.players[1].hand[0])
    game.players[1].acceptTarget(game.players[0].facedowns[0])
    assert game.players[0].facedowns == []
    game.players[1].playFaceup(game.players[1].hand[0])
    game.players[1].acceptTarget(game.players[0].faceups[0])
    assert game.players[0].facedowns == []


def testWrathOfGod():
    dfp1 = dummyFactionPlayer([base.one(), base.one()])
    dfp2 = dummyFactionPlayer([wrathOfGod()])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    game.players[0].drawCard()
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].hand[1].playsFaceUp = True
    game.players[0].hand[1].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].endTurn()
    game.players[1].drawCard()
    game.players[1].hand[0].cost = 0
    game.players[1].playFaceup(game.players[1].hand[0])
    assert game.players[0].faceups == []


def testMiracle():
    # TODO: be able to do something like [base.one()] * 10
    # doesn't currently work because base.one() only evaluates once
    dfp1 = dummyFactionPlayer([
                base.one(),
                base.one(),
                base.one(),
                base.one(),
                base.one(),
                base.one(),
                miracle()
                ])
    dfp2 = dummyFactionPlayer([])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    assert len(game.players[0].hand) == 1
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    assert len(game.players[0].hand) == 5


def testMiracleNotEnoughCards():
    dfp1 = dummyFactionPlayer([
                base.one(),
                base.one(),
                miracle()
                ])
    dfp2 = dummyFactionPlayer([])
    game = Game(dfp1, dfp2)
    game.players[0].drawCard()
    assert len(game.players[0].hand) == 1
    game.players[0].hand[0].playsFaceUp = True
    game.players[0].hand[0].cost = 0
    game.players[0].playFaceup(game.players[0].hand[0])
    assert len(game.players[0].hand) == 2
