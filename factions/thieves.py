from . import base
from core.player import Player, IllegalMoveError
from core.card import Card, card
from core.game import destroy
from core.faction import deck


class MultiattackCard(Card):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attackedTargets = []

    def onSpawn(self):
        self._attackedTargets = []

    def afterEndTurn(self):
        self._attackedTargets = []

    def attack(self, target):
        if target in self._attackedTargets:
            raise IllegalMoveError("Can't attack the same target twice.")

        super().attack(target)
        self._attackedTargets.append(target)

    @property
    def hasAttacked(self):
        return len(self._attackedTargets) == self.nAttacks

    @hasAttacked.setter
    def hasAttacked(self, value):
        pass


def multiattackCard(**kwargs):
    return card(MultiattackCard, **kwargs)


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


def fog():
    return card(
        name="Fog",
        image='frog.png',
        cost=1,
        rank=1,
        isValidTarget=False,
        desc="This can't be the target of spells or abilities.")


class Thief(Player):
    name = "Thieves"
    iconPath = "thief_icons"
    cardBack = "dagger-rose.png"
    deck = deck(
        base.elephant,
        fog, 5,
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
