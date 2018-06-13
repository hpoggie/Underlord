import random

from . import base
from core.game import Phase, destroy
from core.card import Card, card
from core.faction import deck
from core.player import Player, IllegalMoveError


def flood(game):
    if hasattr(game, 'flooded'):
        game.flooded += 1
    else:
        game.flooded = 1


def unflood(game):
    game.flooded -= 1
    if game.flooded < 0:
        raise ValueError("Flood counter can't go below 0.")


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


def aquaticCard(**kwargs):
    return card(AquaticCard, **kwargs)


def kraken():
    return aquaticCard(
        name="Kraken",
        image="squid.png",
        cost=7,
        rank=8,
        desc="Aquatic.")


def nuisanceFlooding():
    def onSpawn(self):
        self.remainingTurns = 4
        flood(self.game)

    def beforeEndTurn(self):
        self.remainingTurns -= 1
        if self.remainingTurns <= 0:
            self.game.destroy(self)

    def onDeath(self):
        unflood(self.game)

    return card(
        name="Nuisance Flooding",
        image="at-sea.png",
        cost=3,
        rank='s',
        continuous=True,
        onSpawn=onSpawn,
        beforeEndTurn=beforeEndTurn,
        onDeath=onDeath,
        desc="Flood the battlefield for 4 turns.")


def voidstar():
    return aquaticCard(
        name="Voidstar",
        image='voidstar.png',
        cost=5,
        rank=5,
        playsFaceUp=True,
        desc="Aquatic. Fast.")


def grandJelly():
    return aquaticCard(
        name="Grand Jelly",
        image='jellyfish.png',
        cost=4,
        rank=4,
        taunt=True,
        desc="Aquatic. Taunt.")


def ripCurrent():
    def onSpawn(self):
        for c in self.owner.opponent.facedowns[:]:
            destroy(c)
        for c in self.owner.opponent.faceups[:]:
            destroy(c)

    return aquaticCard(
        name="Rip Current",
        image='water-bolt.png',
        cost=9,
        rank='s',
        onSpawn=onSpawn,
        desc="Aquatic. Destroy all your opponent's face-up units "
             "and face-down cards.")


def highTide():
    def onSpawn(self):
        flood(self.game)

    def beforeEndTurn(self):
        destroy(self)

    def onDeath(self):
        unflood(self.game)

    return card(
        name="High Tide",
        image='lighthouse.png',
        cost=0,
        rank='s',
        continuous=True,
        onSpawn=onSpawn,
        beforeEndTurn=beforeEndTurn,
        onDeath=onDeath,
        desc="Flood the battlefield until end of turn. Draw a card.")


def unexpectedShark():
    def afterEndTurn(self):
        if not hasattr(self.game, 'flooded') or not self.game.flooded:
            destroy(self)

    def beforeFight(self, target):
        if hasattr(target, 'spell') and target.spell:
            destroy(target)

    return card(
        name="Unexpected Shark",
        image='shark-jaws.png',
        cost=3,
        rank=3,
        playsFaceUp=True,
        afterEndTurn=afterEndTurn,
        beforeFight=beforeFight,
        desc="Fast. Dies at end of turn if the battlefield isn't flooded. "
             "Can kill spells.")


def braintwister():
    def onSpawn(self):
        h = self.owner.opponent.hand
        try:
            idx = random.randint(0, len(h) - 1)
            h[idx].zone = self.owner.opponent.graveyard
        except ValueError:  # Do nothing if they have no cards
            pass

    return aquaticCard(
        name="Braintwister",
        image='braintwister.png',
        cost=2,
        rank=2,
        onSpawn=onSpawn,
        desc="Aquatic. When this spawns, your opponent discards a random "
             "card.")


def humboldtSquid():
    def beforeAnyFight(self, target, attacker):
        # TODO: black magic
        # 2nd arg is always the attacker
        # find cleaner way to do this
        if attacker == self and isinstance(target, Card):
            self.rank = 5

    def afterFight(self, target):
        self.rank = 1

    return card(
        name="Humboldt Squid",
        image='tentacle-strike.png',
        cost=1,
        rank=1,
        beforeAnyFight=beforeAnyFight,
        afterFight=afterFight,
        desc="Aquatic. This has rank 5 while attacking a unit.")


class Mariner(Player):
    iconPath = "mariner_icons"
    cardBack = "nautilus-shell.png"
    deck = deck(humboldtSquid, 5,
              braintwister, 4,
              nuisanceFlooding, 3,
              highTide, 3,
              grandJelly, 2,
              unexpectedShark, 3,
              kraken,
              voidstar,
              ripCurrent) + base.deck

    def __init__(self):
        super().__init__()
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

        # append to front in reverse order
        # TODO: This is stupid. do something else
        for card in cards[::-1]:
            self.deck.insert(0, card)
        for card in self.hand[:]:
            if card in cards:
                self.hand.remove(card)
        for card in cards:
            card._zone = self.deck

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
        if self.hasFirstPlayerPenalty and fish:
            raise IllegalMoveError("Can't fish if you're not drawing.")

        super().endPhase()

        if self.game.phase == Phase.play and fish:
            self.fish()

    def failIfInactive(self):
        super().failIfInactive(self)

        if self.fishing:
            raise IllegalMoveError("Must complete fishing first.")
