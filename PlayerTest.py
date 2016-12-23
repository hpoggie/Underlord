class DuplicateCardError (Exception):
    def __init__(self, card):
        self.card = card

    def __print__(self):
        print "Card " + card + " appears more than once."


def checkDeckForDuplicates(deck):
    for i, card in enumerate(deck):
        for j, card2 in enumerate(deck, start=i+1):
            if card == card2:
                raise DuplicateCardError(card)
