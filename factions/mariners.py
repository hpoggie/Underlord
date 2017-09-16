from . import base
from core.card import Card
from core.faction import Faction, deck
from core.player import Player


def aquatic(func):
    def aquaticCard():
        card = func()
        card._oldOnSpawn = card.onSpawn

        def _onSpawn(self):
            if not self.game.flooded:
                self.moveZone(self.owner.hand)
            else:
                self._oldOnSpawn()

        card.onSpawn = _onSpawn

        return card
    return aquaticCard


@aquatic
def kraken():
    return Card(
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
        def afterEvent(self, eventName, *args, **kwargs):
            if eventName == "endTurn" and self.owner.isActivePlayer():
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


Mariners = Faction(
    name="Mariners",
    iconPath="mariner_icons",
    cardBack="nautilus-shell.png",
    deck=deck(kraken,
              nuisanceFlooding, 3) + base.deck)


class Mariner(Player):
    def __init__(self):
        super().__init__(Mariners)

    @property
    def game(self):
        return self._game

    @game.setter
    def game(self, value):
        self._game = value
        if not hasattr(self.game, "flooded"):
            self.game.flooded = False

    def fish(self):
        for i in range(3):
            drawCard()

        def fishDiscard(self, cards):
            for card in cards:
                self.deck.append(card)
                card.zone = card.owner.deck

        disc = TargetedAbility(fishDiscard)
        disc.execute()
