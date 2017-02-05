import __init__
import unittest
from core.player import Player
from core.core import Game
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
    def testPlay(self):
        game = Game()
        game.start()
        player = game.players[0]
        newCard = base.one()
        newCard.owner = player
        player.deck = [newCard]
        player.drawCard()
        player.endPhase()
        player.endPhase()
        player.endPhase()
        player.play(newCard)
        self.failUnlessEqual(newCard.zone, Zone.facedown)

if __name__ == '__main__':
    unittest.main(verbosity=2)
