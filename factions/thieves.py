from . import base
from core.player import Player, IllegalMoveError
from core.card import card
from core.game import destroy
from core.faction import deck


def spectralCrab():
    @property
    def rank(self):
        return 4 if self.zone is self.controller.facedowns else 2

    return card(
        name="Spectral Crab",
        image='crab.png',
        cost=2,
        rank=rank,
        desc="Has rank 4 while face-down.")


def timeBeing():
    def onSpawn(self):
        self.controller.takeExtraTurn()

    return card(
        name="Time Being",
        image='dead-eye.png',
        cost=12,
        rank=3,
        onSpawn=onSpawn,
        desc="When this spawns, take an extra turn after this one.")


def spellScalpel():
    def onSpawn(self, target):
        destroy(target)
        self.controller.drawCard()

    return card(
        name="Spell Scalpel",
        image='scalpel-strike.png',
        cost=5,
        rank='s',
        onSpawn=onSpawn,
        desc="Destroy target card. Draw a card.")


class Thief(Player):
    name = "Thieves"
    iconPath = "thief_icons"
    cardBack = "dagger-rose.png"
    deck = deck(
        base.elephant,
        spectralCrab, 4,
        timeBeing,
        spellScalpel) + base.deck

    def thiefAbility(self, discard, name, target):
        self.failIfInactive()

        if target.zone is not self.opponent.facedowns:
            raise IllegalMoveError("Invalid target.")

        if target.name == name:
            target.zone = self.faceups
        else:
            target.visibleWhileFacedown = True
