import context
import unittest
from factions.templars import *
from core.core import Game

class TemplarTest(unittest.TestCase):
    def testEquus(self):
        game = Game(Faction(deck=[equus()]), Faction())
        game.players[0].moveCard(game.players[0].deck[0], Zone.faceup)
        game.players[0].manaCap = 3
        self.failUnlessEqual(game.players[0].faceups[0].rank, 5)
        game.players[0].manaCap = 4
        self.failUnlessEqual(game.players[0].faceups[0].rank, 2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
