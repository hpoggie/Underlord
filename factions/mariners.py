import random

from . import base
from core.game import Phase, destroy
from core.card import Card
from core.faction import Faction, deck
from core.player import Player, IllegalMoveError


class AquaticCard(Card):
    @property
    def flooded(self):
        return hasattr(self.game, 'flooded') and self.game.flooded

    def cast(self):
        if not self.flooded:
            raise IllegalMoveError("You can't cast aquatic spells unless the "
                                   "battlefield is flooded.")

        super().cast()

    def afterEndTurn(self):
        if not self.flooded:
            self.zone = self.owner.hand


def kraken():
    return AquaticCard(
        name="Kraken",
        image="squid.png",
        cost=7,
        rank=8,
        desc="Aquatic.")


def nuisanceFlooding():
    def _onSpawn(self):
        self.remainingTurns = 4
        self.game.flooded = True

    class NuisanceFlooding(Card):
        def beforeEndTurn(self):
            self.remainingTurns -= 1
            if self.remainingTurns <= 0:
                self.game.flooded = False
                self.game.destroy(self)

    return NuisanceFlooding(
        name="Nuisance Flooding",
        image="at-sea.png",
        cost=3,
        rank='s',
        spell=True,
        onSpawn=_onSpawn,
        desc="Flood the battlefield for 4 turns.")


def voidstar():
    return AquaticCard(
        name="Voidstar",
        image='voidstar.png',
        cost=5,
        rank=5,
        playsFaceUp=True,
        desc="Aquatic. Fast.")


def grandJelly():
    return AquaticCard(
        name="Grand Jelly",
        image='jellyfish.png',
        cost=4,
        rank=4,
        taunt=True,
        desc="Aquatic. Taunt.")


def ripCurrent():
    def _onSpawn(self):
        for c in self.owner.opponent.facedowns[:]:
            destroy(c)
        for c in self.owner.opponent.faceups[:]:
            destroy(c)

    return AquaticCard(
        name="Rip Current",
        image='water-bolt.png',
        cost=9,
        rank='s',
        onSpawn=_onSpawn,
        desc="Aquatic. Destroy all your opponent's face-up units "
             "and face-down cards.")


def highTide():
    def _onSpawn(self):
        self.game.flooded = True

    class HighTide(Card):
        def beforeEndTurn(self):
            self.game.flooded = False
            destroy(self)

    return HighTide(
        name="High Tide",
        image='lighthouse.png',
        cost=0,
        rank='s',
        spell=True,
        onSpawn=_onSpawn,
        desc="Flood the battlefield until end of turn. Draw a card.")


def unexpectedShark():
    class UnexpectedShark(Card):
        def afterEndTurn(self):
            if not hasattr(self.game, 'flooded') or not self.game.flooded:
                destroy(self)

        def onFight(self, target):
            if hasattr(target, 'spell') and target.spell:
                destroy(target)

    return UnexpectedShark(
        name="Unexpected Shark",
        image='shark-jaws.png',
        cost=3,
        rank=3,
        playsFaceUp=True,
        desc="Fast. Dies at end of turn if the battlefield isn't flooded. "
             "Can kill spells.")


def braintwister():
    def _onSpawn(self):
        h = self.owner.opponent.hand
        h[random.randint(0, len(h) - 1)].zone = self.owner.opponent.graveyard

    return AquaticCard(
        name="Braintwister",
        image='braintwister.png',
        cost=2,
        rank=2,
        onSpawn=_onSpawn,
        desc="Aquatic. When this spawns, your opponent discards a random "
             "card.")


def humboldtSquid():
    class HumboldtSquid(AquaticCard):
        def beforeFight(self, target, attacker):
            # TODO: black magic
            # 2nd arg is always the attacker
            # find cleaner way to do this
            if attacker == self and isinstance(target, Card):
                self.rank = 5

        def afterFight(self, target, attacker):
            self.rank = 1

    return HumboldtSquid(
        name="Humboldt Squid",
        image='tentacle-strike.png',
        cost=1,
        rank=1,
        desc="Aquatic. This has rank 5 while attacking a unit.")


Mariners = Faction(
    name="Mariners",
    iconPath="mariner_icons",
    cardBack="nautilus-shell.png",
    deck=deck(humboldtSquid, 5,
              braintwister, 4,
              nuisanceFlooding, 3,
              highTide, 3,
              grandJelly, 2,
              unexpectedShark, 3,
              kraken,
              voidstar,
              ripCurrent) + base.deck)


class Mariner(Player):
    def __init__(self):
        super().__init__(Mariners)
        self.fishing = False

    def fishReplace(self, cards):
        """
        Bottomdeck the 3 cards
        """
        if not self.fishing:
            raise IllegalMoveError("Not fishing.")

        if len(cards) != 3:
            raise IllegalMoveError("Must replace exactly 3 cards.")

        for card in cards:
            if card is None or card.zone is not self.hand:
                raise IllegalMoveError("Must choose a valid target.")

        # append to front
        self.deck = cards + self.deck
        self.hand = [c for c in self.hand if c not in cards]
        for card in cards:
            card.zone = self.deck

        self.fishing = False

    def fish(self):
        # Draw 2 more cards
        for i in range(2):
            self.drawCard()

        # If you have <= 3 cards in hand, put all of them back
        if len(self.hand) <= 3:
            for card in self.hand:
                card.zone = card.owner.deck
        else:
            self.fishing = True  # Can't do anything until calling fishReplace

    def endPhase(self, fish=False):
        super().endPhase(self)

        if self.game.phase == Phase.play and fish:
            self.fish()

    def failIfInactive(self):
        super().failIfInactive(self)

        if self.fishing:
            raise IllegalMoveError("Must complete fishing first.")


Mariners.player = Mariner
