import unittest
import sys
sys.path.insert(0, "..")


class PlayerTest(unittest.TestCase):
    def checkDeckForDuplicates(self, deck):
        for i, card in enumerate(deck):
            for card2 in deck[i+1:]:
                if card == card2:
                    self.fail('' + card.name + ' equals ' + card2.name)

    def testForDuplicates(self):
        from core.player import Player
        player = Player()
        self.checkDeckForDuplicates(player.deck)

    def testForDuplicatesBetweenPlayers(self):
        from core.player import Player
        player1 = Player()
        player2 = Player()

        for card1 in player1.deck:
            for card2 in player2.deck:
                if card1 == card2:
                    self.fail('' + card1.name + ' equals ' + card2.name)


class ActionsTest(unittest.TestCase):
    def testPlay(self):
        from core.core import Game
        from factions import base
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
