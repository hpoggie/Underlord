import types
from . import base
from core.player import Player
from core.exceptions import IllegalMoveError, InvalidTargetError
from core.card import Card
from core.game import destroy, Phase
from core.faction import deck


class MultiattackCard(Card):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attackedTargets = []

    def onSpawn(self):
        self._attackedTargets = []

    def afterEndTurn(self):
        self._attackedTargets = []

    def attack(self, target):
        if target in self._attackedTargets:
            raise IllegalMoveError("Can't attack the same target twice.")

        super().attack(target)
        self._attackedTargets.append(target)

    @property
    def hasAttacked(self):
        return len(self._attackedTargets) == self.nAttacks

    @hasAttacked.setter
    def hasAttacked(self, value):
        pass


class spectralCrab(Card):
    name = "Spectral Crab"
    image = 'crab.png'
    cost = 2
    desc = "Has rank 4 while face-down."

    @property
    def rank(self):
        return 4 if self.facedown else 2


class timeBeing(Card):
    name = "Time Being"
    image = 'dead-eye.png'
    cost = 12
    rank = 3
    desc = "When this spawns, take an extra turn after this one."

    def onSpawn(self):
        self.controller.takeExtraTurn()


class spellScalpel(Card):
    name = "Spell Scalpel"
    image = 'scalpel-strike.png'
    cost = 5
    rank = 's'
    desc = "Destroy target card. Draw a card."

    def onSpawn(self, target):
        destroy(target)
        self.controller.drawCard()


class fog(Card):
    name = "Fog"
    image = 'frog.png'
    cost = 1
    rank = 1
    isValidTarget = False
    desc = "This can't be the target of spells or abilities."


class hydra(MultiattackCard):
    name = "Hydra"
    image = 'hydra.png'
    cost = 6
    rank = 3
    nAttacks = 3
    desc = "Can attack up to 3 different targets per turn."


class doubleDragon(MultiattackCard):
    name = "Double Dragon"
    image = 'double-dragon.png'
    cost = 4
    rank = 2
    nAttacks = 2
    desc = "Can attack up to 2 different targets per turn."


class headLightning(Card):
    name = "Head Lightning"
    image = 'brainstorm.png'
    cost = 1
    rank = 's'
    desc = ("Draw 3 cards, then put 2 cards from your hand on top of"
            "your deck.")

    def onSpawn(self):
        self.controller.drawCards(3)

        def replace(c1, c2):
            self.controller.topdeck([c1, c2])

        self.controller.pushAction(replace)


class roseEmblem(Card):
    name = "Rose Emblem"
    image = 'rose.png'
    cost = 3
    rank = 's'
    desc = "Draw 2 cards. When you discard this from your hand, draw a card."

    def onSpawn(self):
        self.controller.drawCards(2)

    def onDiscard(self):
        self.controller.drawCard()


class spellHound(Card):
    name = "Spell Hound"
    image = 'wolf-howl.png'
    cost = 3
    rank = 2
    desc = "When this spawns, look at your opponent's hand."

    def onSpawn(self):
        for c in self.controller.opponent.hand:
            c.visible = True


class daggerEmblem(Card):
    name = "Dagger Emblem"
    image = 'stiletto.png'
    cost = 2
    rank = 's'
    desc = ("Destroy target face-up unit. When you discard this from your"
            " hand, draw a card.")

    def onSpawn(self, target):
        if (target.faceup and not target.spell):
            destroy(target)

    def onDiscard(self):
        self.controller.drawCard()


class heavyLightning(Card):
    name = "Heavy Lightning"
    image = 'heavy-lightning.png'
    cost = 11
    rank = 's'
    desc = ("Destroy all your opponent's face-up units and face-down"
            " cards. Draw 3 cards. When this is attacked, its cost"
            " becomes 5.")

    def afterFight(self, c2):
        self.cost = 5

    def onSpawn(self):
        self.controller.opponent.facedowns.destroyAll()
        self.controller.opponent.faceups.destroyAllUnits()
        self.controller.drawCards(3)


class Thief(Player):
    name = "Thieves"
    iconPath = "thief_icons"
    cardBack = "dagger-rose.png"
    deck = deck(
        base.elephant,
        fog, 5,
        spectralCrab, 4,
        spellHound, 3,
        doubleDragon, 2,
        headLightning, 2,
        roseEmblem,
        daggerEmblem,
        hydra,
        timeBeing,
        heavyLightning,
        spellScalpel) + base.deck

    def onStartOfTurn(self):
        pass

    def thiefAbility(self, discard, name, target):
        self.failIfInactive()

        if self.game.phase != Phase.startOfTurn:
            raise IllegalMoveError("Can only try to steal at start of turn.")

        if discard.zone is not self.hand:
            raise IllegalMoveError("That card is not in your hand.")

        if target.zone is not self.opponent.facedowns:
            raise InvalidTargetError()

        self.pushAction(lambda: self.endPhase())

        if target.name == name:
            if target.requiresTarget:  # Can choose the target of the ability
                def callback(abilityTarget):
                    target.spawn(target=abilityTarget, newController=self)
                    discard.zone = discard.owner.graveyard

                self.pushAction(callback)
            else:
                target.spawn(target=None, newController=self)
        else:
            target.visible = True

        discard.zone = discard.owner.graveyard

        self.popAction()
