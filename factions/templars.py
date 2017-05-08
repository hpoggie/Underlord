import base
from core.card import Card, Faction
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


Templars = Faction(
    name="Templars",
    iconPath="./templar_icons",
    cardBack="templar-shield.png",
    deck=[
        base.one(), base.one(), base.one(), base.one(),
        base.sweep(), base.sweep(),
        base.spellBlade(),
        strix(),
        equus(),
        equus(),
        ],
    )
