import context
import unittest
import factions.templars as templars
import core.core


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

        grail = templars.grail()
        grail.owner = self.player
        self.player.deck = [grail]

        self.game.start()

if __name__ == "__main__":
    unittest.main(verbosity=2)
