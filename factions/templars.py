from . import base
from core.game import destroy, Phase
from core.card import card
from core.faction import deck
from core.player import Player


def equus():
    @property
    def rank(self):
        return 2 if (self.controller.manaCap % 2 == 0) else 5

    return card(
        name="Equus",
        image="horse-head.png",
        cost=3,
        rank=rank,
        desc="Has rank 2 if your mana cap is even and rank 5 if your mana cap "
             "is odd.")


def archangel():
    return card(
        name="Archangel",
        image="angel-wings.png",
        cost=13,
        rank=15)


def holyHandGrenade():
    def onSpawn(self, target):
        destroy(target)

    return card(
        name="Holy Hand Grenade",
        image="holy-hand-grenade.png",
        fast=True,
        cost=4,
        rank='s',
        onSpawn=onSpawn,
        desc="Destroy target card.")


def wrathOfGod():
    return card(
        name="Wrath of God",
        image="wind-hole.png",
        cost=5,
        rank='s',
        fast=True,
        onSpawn=base.sweepAbility,
        desc=base.sweep().desc)


def corvus():
    def onSpawn(self):
        self.controller.manaCap += 1

    return card(
        name="Corvus",
        image="raven.png",
        cost=1,
        rank=1,
        onSpawn=onSpawn,
        desc="When this spawns, add 1 to your mana cap.")


def miracle():
    def onSpawn(self):
        self.controller.drawTo(5)

    return card(
        name="Miracle",
        image="sundial.png",
        cost=8,
        rank='s',
        onSpawn=onSpawn,
        desc="Draw until you have 5 cards in hand.")


def crystalElemental():
    def beforeDestroy(self, card):
        if (card.controller != self.controller and
                card.zone == card.controller.facedowns):
            self.controller.drawCard()

    return card(
        name="Crystal Elemental",
        image="crystal-cluster.png",
        cost=7,
        rank=4,
        beforeDestroy=beforeDestroy,
        desc="Whenever you destroy an enemy face-down card, draw a card.")


def invest():
    def onSpawn(self):
        self.controller.manaCap += 1
        self.controller.drawCard()

    return card(
        name="Invest",
        image="profit.png",
        cost=1,
        rank='s',
        onSpawn=onSpawn,
        desc="Add 1 to your mana cap. Draw a card.")


def leftGrail():
    @property
    def rank(self):
        return 2 if (self.controller.manaCap % 2 == 0) else 3

    return card(
        name="Left Grail",
        image="holy-grail.png",
        cost=2,
        rank=rank,
        taunt=True,
        desc="Taunt. Has rank 2 if your mana cap is even and rank 3 if your "
             "mana cap is odd.",)


def rightGrail():
    @property
    def rank(self):
        return 3 if (self.controller.manaCap % 2 == 0) else 2

    return card(
        name="Right Grail",
        image="holy-grail.png",
        cost=2,
        rank=rank,
        taunt=True,
        desc="Taunt. Has rank 3 if your mana cap is even and rank 2 if your "
             "mana cap is odd.",)


def guardianAngel():
    @property
    def rank(self):
        return 5 if (self.controller.manaCap % 2 == 0) else 3

    return card(
        name="Guardian Angel",
        image="winged-shield.png",
        cost=4,
        rank=rank,
        taunt=True,
        desc="Taunt. Has rank 5 if your mana cap is even and rank 3 if your "
             "mana cap is odd.",)


def crystalLance():
    def onSpawn(self, target):
        if target.facedown:
            destroy(target)

    def afterFight(self, enemy):
        destroy(enemy)
        self.controller.drawCard()

    return card(
        name="Crystal Lance",
        image="ice-spear.png",
        cost=5,
        rank='s',
        onSpawn=onSpawn,
        afterFight=afterFight,
        desc="Destroy target face-down card. "
             "If this is attacked while face-down, "
             "destroy the attacking unit and draw a card.",
        targetDesc="Destroy target face-down card.")


def crystalRain():
    def onSpawn(self, target):
        if target.facedown:
            destroy(target)

    def afterFight(self, enemy):
        base.sweepAbility(self)

    return card(
        name="Crystal Rain",
        image="crystal-bars.png",
        cost=5,
        rank='s',
        onSpawn=onSpawn,
        afterFight=afterFight,
        desc="Destroy target face-down card. "
             "If this is attacked while face-down, "
             "destroy all face-up units.",
        targetDesc="Destroy target face-down card.")


class Templar(Player):
    name = "Templars"
    iconPath = "templar_icons"
    cardBack = "templar-shield.png"
    deck = deck(
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
        crystalLance,
        crystalRain,
        crystalElemental,
        invest) + base.deck

    def templarAbility(self, card):
        if card and card in self.hand:
            card.zone = self.graveyard
            self.manaCap += 1

    def endPhase(self, *args, **kwargs):
        if self.game.phase == Phase.play:
            self.templarAbility(*args, **kwargs)
        super().endPhase()
