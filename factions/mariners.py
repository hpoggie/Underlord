from . import base
from core.game import Phase
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


Mariners = Faction(
    name="Mariners",
    iconPath="mariner_icons",
    cardBack="nautilus-shell.png",
    deck=deck(kraken,
              nuisanceFlooding, 3,
              voidstar,
              grandJelly, 2) + base.deck)


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
            card.zone = card.owner.deck

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
