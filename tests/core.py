import context
import unittest
from core.player import Player
from core.core import Game
from core.card import Faction
from factions import base
from factions.templars import Templars
from core.enums import *


def deckContainsDuplicates(deck):
    for i, card in enumerate(deck):
        for card2 in deck[i+1:]:
            if card == card2:
                return True
    return False


class PlayerTest(unittest.TestCase):
    def testForDuplicates(self):
        player = Player(Templars)
        self.failIf(deckContainsDuplicates(player.deck))

    def testForDuplicatesBetweenPlayers(self):
        player1 = Player(Templars)
        player2 = Player(Templars)

        for card1 in player1.deck:
            for card2 in player2.deck:
                if card1 == card2:
                    self.fail('' + card1.name + ' equals ' + card2.name)


class ActionsTest(unittest.TestCase):
    def testReveal(self):
        game = Game(Faction(deck=[base.one()]), Faction())
        player = game.players[0]
        player.endPhase()  # draw the card
        newCard = player.hand[0]
        player.play(newCard)
        player.endPhase()
        game.players[1].endTurn()
        player.revealFacedown(newCard)
        self.failUnlessEqual(newCard.zone, Zone.faceup)

    def testPlay(self):
        game = Game(Faction(deck=[base.one()]), Faction())
        player = game.players[0]
        player.endPhase()
        newCard = player.hand[0]
        player.play(newCard)
        self.failUnlessEqual(newCard.zone, Zone.facedown)

    def testPlayFaceup(self):
        newCard = base.one()
        newCard.playsFaceUp = True
        newCard.cost = 0
        game = Game(Faction(deck=[newCard]), Faction())
        player = game.players[0]
        player.drawCard()
        instance = player.hand[0]
        player.playFaceup(instance)
        self.failUnlessEqual(instance.zone, Zone.faceup)

    def testAttackFace(self):
        newCard = base.one()
        newCard.playsFaceUp = True
        newCard.cost = 0
        game = Game(Faction(deck=[newCard]), Faction())
        player = game.players[0]
        player.drawCard()
        player.playFaceup(player.hand[0])
        player.endPhase()
        player.attackFace(player.faceups[0])
        self.failUnlessEqual(game.players[1].manaCap, 2)

    def testAttackFacedown(self):
        newCard = base.one()
        newCard.playsFaceUp = True
        newCard.cost = 0
        faction = Faction(deck=[newCard])
        game = Game(faction, faction)
        game.start()
        #1st player plays a facedown
        game.players[0].endPhase()
        game.players[0].play(game.players[0].hand[0])
        game.players[0].endTurn()
        #2nd player attacks it
        game.players[1].playFaceup(game.players[1].hand[0])
        game.players[1].endPhase()
        game.players[1].attack(game.players[1].faceups[0], game.players[0].facedowns[0])
        self.failUnlessEqual(len(game.players[0].facedowns), 0)
        self.failUnlessEqual(len(game.players[1].faceups), 0)

    def testAttackFacedown(self):
        newCard = base.one()
        newCard.playsFaceUp = True
        newCard.cost = 0
        faction = Faction(deck=[newCard])
        game = Game(faction, faction)
        game.start()
        #1st player plays a facedown
        game.players[0].playFaceup(game.players[0].hand[0])
        game.players[0].endTurn()
        #2nd player attacks it
        game.players[1].playFaceup(game.players[1].hand[0])
        game.players[1].endPhase()
        game.players[1].attack(game.players[1].faceups[0], game.players[0].faceups[0])
        self.failUnlessEqual(len(game.players[0].facedowns), 0)
        self.failUnlessEqual(len(game.players[1].faceups), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
