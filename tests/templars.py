import context
import unittest
import factions.templars as templars
import factions.base as base
import core.core
from core.enums import *


class TestImport(unittest.TestCase):
    def testImport(self):
        game = core.core.Game(templars.Templars, templars.Templars)
        game.start()
        player = game.players[0]
        grail = templars.grail()
        grail.owner = player
        player.deck = [grail]
        player.endPhase()


class TestGrail(unittest.TestCase):
    def setUp(self):
        self.game = core.core.Game(templars.Templars, templars.Templars)
        self.player1 = self.game.players[0]
        self.player2 = self.game.players[1]

        self.grail = templars.grail()
        self.grail.owner = self.player1
        self.player1.deck = [self.grail]

        self.one = base.one()
        self.one.owner = self.player2
        self.player2.deck = [self.one]

        self.game.start()

    def testGrail(self):
        self.player1.endPhase()
        self.player1.play(self.grail)
        self.player1.endPhase()

        self.player2.endPhase()
        self.player2.play(self.one)
        self.player2.endPhase()

        self.player1.revealFacedown(self.grail)
        self.player1.endPhase()
        self.player1.endPhase()

        self.player2.revealFacedown(self.one)
        self.player2.endPhase()
        self.player2.endPhase()
        try:
            self.player2.attack(self.one, Zone.face)
            self.fail()
        except IllegalMoveError:
            pass

if __name__ == "__main__":
    unittest.main(verbosity=2)
