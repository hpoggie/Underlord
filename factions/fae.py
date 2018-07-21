from core.player import Player
from core.faction import deck
from core.card import Card
import factions.base as base


class faerieMoth(Card):
    name = "Faerie Moth"
    icon = 'butterfly.png'
    cost = 1
    rank = 1
    fast = True
    desc = "Fast."


class Faerie(Player):
    deck = deck(faerieMoth, 5) + base.deck

    def endPhase(self, card=None):
        self.failIfInactive()
        self.game.endPhase(keepFacedown=[card])
