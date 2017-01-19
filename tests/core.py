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
        player = Player("Test Player")
        self.checkDeckForDuplicates(player.deck)

    def testForDuplicatesBetweenPlayers(self):
        from core.player import Player
        player1 = Player("Player 1")
        player2 = Player("Player 2")

        for card1 in player1.deck:
            for card2 in player2.deck:
                if card1 == card2:
                    self.fail('' + card1.name + ' equals ' + card2.name)


class ActionsTest(unittest.TestCase):
    def testPlay(self):
        from core.core import Game
        from core import card
        game = Game()
        game.start()
        player = game.players[0]
        newCard = card.one()
        newCard.owner = player
        player.deck = [newCard]
        player.drawCard()
        game.endPhase(player)
        game.endPhase(player)
        game.endPhase(player)
        player.play(0)

if __name__ == '__main__':
    unittest.main()
