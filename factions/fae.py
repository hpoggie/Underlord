from core.player import Player
from core.exceptions import InvalidTargetError
from core.faction import deck
from core.card import Card
from core.game import destroy
import factions.base as base


class faerieMoth(Card):
    name = "Faerie Moth"
    image = 'butterfly.png'
    cost = 1
    rank = 1
    fast = True
    desc = "Fast."


class oberonsGuard(Card):
    name = "Oberon's Guard"
    image = 'elf-helmet.png'
    cost = 2
    rank = 2
    desc = ("When this spawns, you may return target face-down card you "
            "control to its owner's hand.")

    def onSpawn(self, target):
        if target.zone is not self.controller.facedowns:
            raise InvalidTargetError()

        target.zone = target.owner.hand


class titaniasGuard(Card):
    name = "Titania's Guard"
    image = 'batwing-emblem.png'
    cost = 4
    rank = 4
    desc = "When this spawns, turn target face-up unit face-down."

    def onSpawn(self, target):
        if target is None or not target.faceup or target.spell:
            raise InvalidTargetError()

        target.zone = target.controller.facedowns


class preciseDiscard(Card):
    name = "Precise Discard"
    image = 'card-pick.png'
    cost = 2
    rank = 'il'
    desc = "Look at your opponent's hand and discard a card from it."

    def onSpawn(self):
        for c in self.controller.opponent.hand:
            c.visible = True

        def discard(card):
            if card.zone is not self.controller.opponent.hand:
                raise InvalidTargetError()

            card.zone = card.owner.graveyard

        self.controller.pushAction(discard)


class faerieDragon(Card):
    name = "Faerie Dragon"
    image = 'chameleon-glyph.png'
    cost = 5
    rank = 4
    desc = ("If this would be destroyed while face-up, return it to its "
            "owner's hand instead.")

    def moveToZone(self, zone):
        if self.faceup and zone is self.owner.graveyard:
            super().moveToZone(self.owner.hand)
        else:
            super().moveToZone(zone)


class mesmerism(Card):
    name = "Mesmerism"
    image = 'night-vision.png'
    cost = 2
    rank = 'il'
    desc = "Destroy all your opponent's face-up units."

    def onSpawn(self):
        self.controller.opponent.faceups.destroyAllUnits()


class returnToSender(Card):
    name = "Return to Sender"
    image = 'return-arrow.png'
    cost = 3
    rank = 'il'
    desc = "Return all face-down cards to their owners' hands."

    def onSpawn(self):
        for pl in self.game.players:
            for fd in pl.facedowns[:]:
                fd.zone = fd.owner.hand


class enchantersTrap(Card):
    name = "Enchanter's Trap"
    image = 'portal.png'
    cost = 16
    rank = 15
    desc = "Can't be face-up."

    def moveToZone(self, zone):
        if (zone is self.game.players[0].faceups or
                zone is self.game.players[1].faceups):
            return

        super().moveToZone(zone)


class radiance(Card):
    name = "Radiance"
    image = 'sun.png'
    cost = 4
    rank = 'il'
    continuous = True
    desc = ("Until end of turn, for every 1 damage you deal to your opponent,"
            "they must discard a random card.")

    def afterDealDamage(self, player, amount):
        if player is self.controller.opponent:
            for i in range(amount):
                player.discardRandom()

    def beforeEndTurn(self):
        destroy(self)


class fireDust(Card):
    name = "Fire Dust"
    image = 'hot-spices.png'
    cost = 3
    rank = 'il'
    continuous = True
    desc = "Your units have +1 rank while attacking."

    def beforeAnyFight(self, c1, c2):
        if c2.controller is self.controller:
            c2.rank += 1

    def afterAnyFight(self, c1, c2):
        if c2.controller is self.controller:
            c2.rank -= 1


class Faerie(Player):
    name = "Fae"
    iconPath = "fae_icons"
    cardBack = "fairy.png"
    deck = deck(
        faerieMoth, 5,
        oberonsGuard, 4,
        titaniasGuard, 2,
        preciseDiscard, 2,
        mesmerism, 1,
        returnToSender, 1,
        enchantersTrap, 2,
        radiance, 2,
        fireDust, 3) + base.deck

    def endPhase(self, card=None):
        self.failIfInactive()
        self.game.endPhase(keepFacedown=[card])
