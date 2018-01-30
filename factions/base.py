from core.core import destroy
from core.card import Card


def elephant():
    return Card(
        name="Elephant",
        image="elephant.png",
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


def mindControlTrap():
    def mctAbility(self):
        self.owner.drawCard()

    def mctOnFight(self, enemy):
        enemy.owner.faceups.remove(enemy)
        self.owner.faceups.append(enemy)
        enemy.owner = self.owner

    return Card(
        name="Mind Control Trap",
        image="magic-swirl.png",
        cost=2,
        rank="s",
        spell=True,
        onSpawn=mctAbility,
        onFight=mctOnFight,
        desc="""
            Draw a card.\nIf this is attacked while face-down,
            gain control of the attacking unit.""")


deck = [sweep(), spellBlade(), mindControlTrap()]
