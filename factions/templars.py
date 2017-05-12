import base
from core.card import Card, Faction, TargetedAbility
from core.enums import Zone
from core.core import IllegalMoveError


def strix():
    return Card(
        name="Strix",
        image="owl.png",
        cost=1,
        rank=1
        )


def equus():
    import types

    class Equus(Card):
        @property
        def rank(self):
            return 2 if (self.owner.manaCap % 2 == 0) else 5

    equus = Equus(
        name="Equus",
        image="horse-head.png",
        cost=3
        )

    return equus

def archangel():
    return Card(
            name="Archangel",
            image="angel-wings.png",
            cost=13,
            rank=15
            )

def holyHandGrenade():
    def _onSpawn(self, target):
        self.game.destroy(target)
        self.moveZone(target)

    hhg = Card(
            name="Holy Hand Grenade",
            image="holy-hand-grenade.png",
            playsFaceUp=True,
            cost=5,
            spell=True,
            onSpawn=_onSpawn
            )

    return hhg

def wrathOfGod():
    return Card(
            name="Wrath of God",
            image="wind-hole.png",
            cost=5,
            spell=True,
            playsFaceUp=True,
            onSpawn=base.sweepAbility
            )

def corvus():
    def _onSpawn(self):
        self.owner.manaCap += 1

    return Card(
            name="Corvus",
            image="raven.png",
            cost=1,
            rank=1,
            onSpawn=_onSpawn
            )

def miracle():
    def _onSpawn(self):
        while(len(self.owner.hand) < 5):
            self.owner.drawCard()

    return Card(
            name="Miracle",
            image="sundial.png",
            cost=6,
            spell=True,
            onSpawn=_onSpawn
            )


Templars = Faction(
    name="Templars",
    iconPath="./templar_icons",
    cardBack="templar-shield.png",
    deck=[
        base.one(), base.one(), base.one(), base.one(),
        base.sweep(), base.sweep(),
        base.spellBlade(),
        strix(),
        equus(), equus(),
        corvus(),
        holyHandGrenade(),
        wrathOfGod(),
        archangel()
        ],
    )
