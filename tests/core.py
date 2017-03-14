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
    def setUp(self):
        empty = Faction(setup=lambda x: None)
        self.game = Game(empty, empty)
        self.game.start()
        self.player1 = self.game.players[0]
        self.player2 = self.game.players[1]

    def testPlay(self):
        newCard = base.one()
        newCard.owner = self.player1
        self.player1.deck = [newCard]
        self.player1.drawCard()
        self.player1.endPhase()
        self.player1.play(newCard)
        self.failUnlessEqual(newCard.zone, Zone.facedown)

if __name__ == '__main__':
    unittest.main(verbosity=2)
