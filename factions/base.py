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


def sweep():
    def sweepAbility(self):
        for player in self.game.players:
            cards = player.faceups
            player.faceups = []
            for c in cards:
                player.graveyard.append(c)
                c.zone = Zone.graveyard
                c.moveZone(Zone.graveyard)

        self.moveZone(Zone.graveyard)

    sweep = Card(
        name="Sweep",
        image="wind-slap.png",
        cost=0,
        spell=True
    )
    sweep.setSpawnAbility(sweepAbility)

    return sweep


def spellBlade():
    def spellBladeAbility(self, target):
        if target in self.owner.getEnemy().facedowns:
            self.game.destroy(target)

        self.moveZone(Zone.graveyard)

    spellBlade = Card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=0,
        spell=True,
        playsFaceUp=True
    )
    spellBlade.onSpawn = TargetedAbility(spellBladeAbility, spellBlade)

    return spellBlade
