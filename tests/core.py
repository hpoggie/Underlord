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

if __name__ == '__main__':
    unittest.main()
