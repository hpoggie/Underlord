from core.game import destroy
import core.card


def card(**kwargs):
    """
    Override the image path to use base_icons
    """
    return core.card.card(**{'imagePath': property(
        lambda self: 'base_icons/' + self.image)}, **kwargs)


def elephant():
    return card(
        name="Elephant",
        image="elephant.png",
        cost=5,
        rank=5)


def sweepAbility(self):
    for player in self.game.players:
        player.faceups.destroyAll()


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
        if target.facedown:
            destroy(target)

    return card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=3,
        rank="s",
        spell=True,
        fast=True,
        onSpawn=spellBladeAbility,
        desc="Destroy target face-down card.")


def mindControlTrap():
    def onSpawn(self):
        self.controller.drawCard()

    def beforeFight(self, enemy):
        enemy.zone = self.controller.faceups

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
