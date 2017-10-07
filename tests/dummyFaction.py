from core.player import Player
from core.card import Faction


def dummyFactionPlayer(deck):
    class DFP(Player):
        def __init__(self):
            super().__init__(Faction(name="Dummy Faction", deck=deck))

    return DFP
