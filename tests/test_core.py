from core.player import Player
from core.core import Game
from factions import base
from factions.templars import Templars
from tests.dummyFaction import dummyFactionPlayer
from core.enums import *


def deckContainsDuplicates(deck):
    for i, card in enumerate(deck):
        for card2 in deck[i + 1:]:
            if card == card2:
                return True
    return False


def testForDuplicates():
    player = Player(Templars)
    assert not deckContainsDuplicates(player.deck)


def testForDuplicatesBetweenPlayers():
    player1 = Player(Templars)
    player2 = Player(Templars)

    for card1 in player1.deck:
        for card2 in player2.deck:
            assert card1 != card2


def testReveal():
    dfp = dummyFactionPlayer([base.one()])
    game = Game(dfp, dfp)
    player = game.players[0]
    player.endPhase()  # draw the card
    newCard = player.hand[0]
    player.play(newCard)
    player.endPhase()
    game.players[1].endTurn()
    player.revealFacedown(newCard)
    assert newCard.zone == Zone.faceup


def testPlay():
    dfp = dummyFactionPlayer([base.one()])
    game = Game(dfp, dfp)
    player = game.players[0]
    player.endPhase()
    newCard = player.hand[0]
    player.play(newCard)
    assert newCard.zone == Zone.facedown


def testPlayFaceup():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    dfp = dummyFactionPlayer([newCard])
    game = Game(dfp, dfp)
    player = game.players[0]
    player.drawCard()
    instance = player.hand[0]
    player.playFaceup(instance)
    assert instance.zone == Zone.faceup


def testAttackFace():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    dfp = dummyFactionPlayer([newCard])
    game = Game(dfp, dfp)
    player = game.players[0]
    player.drawCard()
    player.playFaceup(player.hand[0])
    player.endPhase()
    player.attackFace(player.faceups[0])
    assert game.players[1].manaCap == 2


def testAttackFacedown():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    dfp = dummyFactionPlayer([newCard])
    game = Game(dfp, dfp)
    game.start()
    # 1st player plays a facedown
    game.players[0].endPhase()
    game.players[0].play(game.players[0].hand[0])
    game.players[0].endTurn()
    # 2nd player attacks it
    game.players[1].playFaceup(game.players[1].hand[0])
    game.players[1].endPhase()
    game.players[1].attack(game.players[1].faceups[0],
                           game.players[0].facedowns[0])
    assert len(game.players[0].facedowns) == 0
    assert len(game.players[1].faceups) == 0


def testAttackFacedown():
    newCard = base.one()
    newCard.playsFaceUp = True
    newCard.cost = 0
    dfp = dummyFactionPlayer([newCard])
    game = Game(dfp, dfp)
    game.start()
    # 1st player plays a facedown
    game.players[0].playFaceup(game.players[0].hand[0])
    game.players[0].endTurn()
    # 2nd player attacks it
    game.players[1].playFaceup(game.players[1].hand[0])
    game.players[1].endPhase()
    game.players[1].attack(game.players[1].faceups[0],
                           game.players[0].faceups[0])
    assert len(game.players[0].facedowns) == 0
    assert len(game.players[1].faceups) == 0
