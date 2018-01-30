from . import base
from core.core import destroy
from core.card import Card
from core.faction import Faction, deck
from core.player import Player


def equus():
    class Equus(Card):
        @property
        def rank(self):
            return 2 if (self.owner.manaCap % 2 == 0) else 5

    equus = Equus(
        name="Equus",
        image="horse-head.png",
        cost=3,
        desc="Has rank 2 if your mana cap is even and rank 5 if your mana cap "
             "is odd."
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
        destroy(target)
        self.zone = self.owner.graveyard

    hhg = Card(
        name="Holy Hand Grenade",
        image="holy-hand-grenade.png",
        playsFaceUp=True,
        cost=4,
        spell=True,
        onSpawn=_onSpawn,
        desc="Destroy target card."
    )

    return hhg


def wrathOfGod():
    return Card(
        name="Wrath of God",
        image="wind-hole.png",
        cost=5,
        spell=True,
        playsFaceUp=True,
        onSpawn=base.sweepAbility,
        desc=base.sweep().desc
    )


def corvus():
    def _onSpawn(self):
        self.owner.manaCap += 1

    return Card(
        name="Corvus",
        image="raven.png",
        cost=1,
        rank=1,
        onSpawn=_onSpawn,
        desc="When this spawns, add 1 to your mana cap."
    )


def miracle():
    def _onSpawn(self):
        while(len(self.owner.hand) < 5 and len(self.owner.deck) > 0):
            self.owner.drawCard()
        self.zone = self.owner.graveyard

    return Card(
        name="Miracle",
        image="sundial.png",
        cost=8,
        spell=True,
        onSpawn=_onSpawn,
        desc="Draw until you have 5 cards in hand."
    )


def crystalElemental():
    class CrystalElemental(Card):
        def beforeEvent(self, eventName, *args, **kwargs):
            if eventName == "destroy" and args[0].owner != self.owner\
                    and args[0].zone == args[0].owner.facedowns:
                self.owner.drawCard()

    return CrystalElemental(
        name="Crystal Elemental",
        image="crystal-cluster.png",
        cost=7,
        rank=4,
        desc="Whenever you destroy an enemy face-down card, draw a card."
    )


def invest():
    def _onSpawn(self):
        self.owner.manaCap += 1
        self.owner.drawCard()
        self.zone = self.owner.graveyard

    return Card(
        name="Invest",
        image="profit.png",
        cost=1,
        spell=True,
        onSpawn=_onSpawn,
        desc="Add 1 to your mana cap. Draw a card."
    )


def leftGrail():
    class LeftGrail(Card):
        @property
        def rank(self):
            return 2 if (self.owner.manaCap % 2 == 0) else 3

    return LeftGrail(
        name="Left Grail",
        image="holy-grail.png",
        cost=2,
        taunt=True,
        desc="Has taunt if your mana cap is odd.",
    )


def rightGrail():
    class RightGrail(Card):
        @property
        def rank(self):
            return 3 if (self.owner.manaCap % 2 == 0) else 2

    return RightGrail(
        name="Right Grail",
        image="holy-grail.png",
        cost=2,
        taunt=True,
        desc="Has taunt if your mana cap is even.",
    )


def guardianAngel():
    class GuardianAngel(Card):
        @property
        def rank(self):
            return 5 if (self.owner.manaCap % 2 == 0) else 3

    return GuardianAngel(
        name="Guardian Angel",
        image="winged-shield.png",
        cost=4,
        taunt=True,
        desc="Has taunt if your mana cap is odd.",
    )


Templars = Faction(
    name="Templars",
    iconPath="./templar_icons",
    cardBack="templar-shield.png",
    deck=deck(
        corvus, 5,
        leftGrail, 2,
        rightGrail, 2,
        equus, 3,
        guardianAngel, 2,
        base.elephant,
        holyHandGrenade,
        wrathOfGod,
        archangel,
        miracle,
        crystalElemental,
        invest) + base.deck
)


class Templar(Player):
    def __init__(self):
        super().__init__(Templars)
