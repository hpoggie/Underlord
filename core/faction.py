from . import player


class Faction:
    def __init__(self, **kwargs):
        self.name = "My Faction"
        self.iconPath = "./my_faction_icons"
        self.cardBack = "my-faction-back.png"
        self.deck = []
        self.player = player.Player

        vars(self).update(kwargs.copy())
