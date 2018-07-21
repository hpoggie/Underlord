from core.player import Player
import factions.base as base


class Faerie(Player):
    deck = base.deck

    def endPhase(self, card=None):
        self.failIfInactive()
        self.game.endPhase(keepFacedown=[card])
