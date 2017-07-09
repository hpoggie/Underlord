from core.card import Card, TargetedAbility
from core.enums import *


def one():
    return Card(
        name="One",
        image="dice-six-faces-one.png",
        cost=1,
        rank=1
        )


def two():
    return Card(
        name="Two",
        image="dice-six-faces-two.png",
        cost=2,
        rank=2
        )


def three():
    return Card(
        name="Three",
        image="dice-six-faces-three.png",
        cost=3,
        rank=3
        )


def four():
    return Card(
        name="Four",
        image="dice-six-faces-four.png",
        cost=4,
        rank=4
        )


def five():
    return Card(
        name="Five",
        image="dice-six-faces-five.png",
        cost=5,
        rank=5
        )

def sweepAbility(self):
    for player in self.game.players:
        cards = player.faceups
        player.faceups = []
        for c in cards:
            player.graveyard.append(c)
            c.zone = Zone.graveyard
            c.moveZone(Zone.graveyard)

    self.moveZone(Zone.graveyard)

def sweep():
    sweep = Card(
        name="Sweep",
        image="wind-slap.png",
        cost=4,
        rank="s",
        spell=True,
        onSpawn=sweepAbility
    )

    return sweep


def spellBlade():
    def spellBladeAbility(self, target):
        if target in self.owner.getEnemy().facedowns:
            self.game.destroy(target)

        self.moveZone(Zone.graveyard)

    spellBlade = Card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=3,
        rank="s",
        spell=True,
        playsFaceUp=True,
        onSpawn = spellBladeAbility
    )

    return spellBlade

deck = [one() for i in range(5)]\
    + [two() for i in range(4)]\
    + [three() for i in range(3)]\
    + [four() for i in range(2)]\
    + [five()]\
    + [sweep(), sweep()]\
    + [spellBlade()]