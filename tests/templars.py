import context
import unittest
from factions.templars import *
from core.core import Game
from factions import base

class TemplarTest(unittest.TestCase):
    def testEquus(self):
        game = Game(Faction(deck=[equus()]), Faction())
        game.players[0].moveCard(game.players[0].deck[0], Zone.faceup)
        game.players[0].manaCap = 3
        self.failUnlessEqual(game.players[0].faceups[0].rank, 5)
        game.players[0].manaCap = 4
        self.failUnlessEqual(game.players[0].faceups[0].rank, 2)

    def testHolyHandGrenade(self):
        game = Game(
                Faction(deck=[base.one(), base.one()]),
                Faction(deck=[holyHandGrenade(), holyHandGrenade()]))
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
        self.failUnlessEqual(game.players[0].facedowns, [])
        game.players[1].playFaceup(game.players[1].hand[0])
        game.players[1].acceptTarget(game.players[0].faceups[0])
        self.failUnlessEqual(game.players[0].facedowns, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
