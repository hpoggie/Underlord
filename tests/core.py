import __init__
import unittest
from core.player import Player
from core.core import Game
from factions import base
from factions.templars import Templars


class PlayerTest(unittest.TestCase):
    def checkDeckForDuplicates(self, deck):
        for i, card in enumerate(deck):
            for card2 in deck[i+1:]:
                if card == card2:
                    self.fail('' + card.name + ' equals ' + card2.name)

    def testForDuplicates(self):
        player = Player(Templars)
        self.checkDeckForDuplicates(player.deck)

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
        game.endPhase(player)
        game.endPhase(player)
        game.endPhase(player)
        player.play(newCard)

if __name__ == '__main__':
    unittest.main()
