from core.game import destroy
from core.card import card


def elephant():
    return card(
        name="Elephant",
        image="elephant.png",
        cost=5,
        rank=5)


def sweepAbility(self):
    for player in self.game.players:
        for c in player.faceups[:]:
            destroy(c)


def sweep():
    return card(
        name="Sweep",
        image="wind-slap.png",
        cost=4,
        rank="s",
        spell=True,
        onSpawn=sweepAbility,
        desc="Destroy all face-up units.")


def spellBlade():
    def spellBladeAbility(self, target):
        if target in self.owner.opponent.facedowns:
            destroy(target)

    return card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=3,
        rank="s",
        spell=True,
        playsFaceUp=True,
        onSpawn=spellBladeAbility,
        desc="Destroy target face-down card.")


def mindControlTrap():
    def onSpawn(self):
        self.owner.drawCard()

    def beforeFight(self, enemy):
        enemy.owner.faceups.remove(enemy)
        self.owner.faceups.append(enemy)
        enemy.owner = self.owner

    return card(
        name="Mind Control Trap",
        image="magic-swirl.png",
        cost=2,
        rank="s",
        spell=True,
        onSpawn=onSpawn,
        beforeFight=beforeFight,
        desc="Draw a card. "
             "If this is attacked while face-down, "
             "gain control of the attacking unit.")


deck = [sweep(), spellBlade(), mindControlTrap()]

for c in deck:
    c.imagePath = "base_icons/" + c.image
