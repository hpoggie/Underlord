from . import base
from core.player import Player, IllegalMoveError


class Thief(Player):
    name = "Thieves"
    iconPath = "thief_icons"
    cardBack = "dagger-rose.png"
    deck = base.deck

    def thiefAbility(self, discard, name, target):
        self.failIfInactive()

        if target.zone is not self.opponent.facedowns:
            raise IllegalMoveError("Invalid target.")

        if target.name == name:
            target.zone = self.faceups
