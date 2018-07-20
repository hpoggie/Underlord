from . import base
from core.game import destroy, Phase
from core.card import Card
from core.faction import deck
from core.player import Player


class equus(Card):
    name = "Equus"
    image = "horse-head.png"
    cost = 3
    desc = ("Has rank 2 if your mana cap is even and rank 5 if your mana cap "
            "is odd.")

    @property
    def rank(self):
        return 2 if (self.controller.manaCap % 2 == 0) else 5


class archangel(Card):
    name = "Archangel"
    image = "angel-wings.png"
    cost = 13
    rank = 15


class holyHandGrenade(Card):
    name = "Holy Hand Grenade"
    image = "holy-hand-grenade.png"
    fast = True
    cost = 4
    rank = 's'
    desc = "Destroy target card."

    def onSpawn(self, target):
        destroy(target)


class wrathOfGod(Card):
    name = "Wrath of God"
    image = "wind-hole.png"
    cost = 5
    rank = 's'
    fast = True
    desc = "Destroy all face-up units."

    def onSpawn(self):
        for player in self.game.players:
            player.faceups.destroyAllUnits()


class corvus(Card):
    name = "Corvus"
    image = "raven.png"
    cost = 1
    rank = 1
    desc = "When this spawns, add 1 to your mana cap."

    def onSpawn(self):
        self.controller.manaCap += 1


class miracle(Card):
    name = "Miracle"
    image = "sundial.png"
    cost = 8
    rank = 's'
    desc = "Draw until you have 5 cards in hand."

    def onSpawn(self):
        self.controller.drawTo(5)


class crystalElemental(Card):
    name = "Crystal Elemental"
    image = "crystal-cluster.png"
    cost = 7
    rank = 4
    desc = "Whenever you destroy an enemy face-down card, draw a card."

    def beforeDestroy(self, card):
        if card.zone is self.controller.opponent.facedowns:
            self.controller.drawCard()


class invest(Card):
    name = "Invest"
    image = "profit.png"
    cost = 1
    rank = 's'
    desc = "Add 1 to your mana cap. Draw a card."

    def onSpawn(self):
        self.controller.manaCap += 1
        self.controller.drawCard()


class leftGrail(Card):
    name = "Left Grail"
    image = "holy-grail.png"
    cost = 2
    taunt = True
    desc = ("Taunt. Has rank 2 if your mana cap is even and rank 3 if your "
            "mana cap is odd.")

    @property
    def rank(self):
        return 2 if (self.controller.manaCap % 2 == 0) else 3


class rightGrail(Card):
    name = "Right Grail"
    image = "holy-grail.png"
    cost = 2
    taunt = True
    desc = ("Taunt. Has rank 3 if your mana cap is even and rank 2 if your "
            "mana cap is odd.")

    @property
    def rank(self):
        return 3 if (self.controller.manaCap % 2 == 0) else 2


class guardianAngel(Card):
    name = "Guardian Angel"
    image = "winged-shield.png"
    cost = 4
    taunt = True
    desc = ("Taunt. Has rank 5 if your mana cap is even and rank 3 if your "
            "mana cap is odd.")

    @property
    def rank(self):
        return 5 if (self.controller.manaCap % 2 == 0) else 3


class crystalLance(Card):
    name = "Crystal Lance"
    image = "ice-spear.png"
    cost = 5
    rank = 's'
    desc = ("Destroy target face-down card. "
            "If this is attacked while face-down, "
            "destroy the attacking unit and draw a card.")
    targetDesc = "Destroy target face-down card."

    def onSpawn(self, target):
        if target.facedown:
            destroy(target)

    def afterFight(self, enemy):
        destroy(enemy)
        self.controller.drawCard()


class crystalRain(Card):
    name = "Crystal Rain"
    image = "crystal-bars.png"
    cost = 5
    rank = 's'
    desc = ("Destroy target face-down card. "
            "If this is attacked while face-down, "
            "destroy all face-up units.")
    targetDesc = "Destroy target face-down card."

    def onSpawn(self, target):
        if target.facedown:
            destroy(target)

    def afterFight(self, enemy):
        base.sweepAbility(self)


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

    def endPhase(self, target=None):
        if self.game.phase == Phase.play:
            self.templarAbility(target)
        super().endPhase()
