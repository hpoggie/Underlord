from core.core import destroy
from core.card import Card


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
        for c in player.faceups[:]:
            destroy(c)


def sweep():
    sweep = Card(
        name="Sweep",
        image="wind-slap.png",
        cost=4,
        rank="s",
        spell=True,
        onSpawn=sweepAbility,
        desc="Destroy all face-up units."
    )

    return sweep


def spellBlade():
    def spellBladeAbility(self, target):
        if target in self.owner.getEnemy().facedowns:
            destroy(target)

        self.zone = self.owner.graveyard

    spellBlade = Card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=3,
        rank="s",
        spell=True,
        playsFaceUp=True,
        onSpawn=spellBladeAbility,
        desc="Destroy target face-down card."
    )

    return spellBlade


deck = [one() for i in range(5)]\
    + [two() for i in range(4)]\
    + [three() for i in range(3)]\
    + [four() for i in range(2)]\
    + [five()]\
    + [sweep(), sweep()]\
    + [spellBlade()]
