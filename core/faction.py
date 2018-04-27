from . import player


def deck(*args):
    deck = []

    for i, arg in enumerate(args):
        if hasattr(arg, '__call__'):
            if i + 1 < len(args) and args[i + 1] is int:
                deck += [arg() for i in range(args[i + 1])]
            else:
                deck.append(arg())

    return deck


class Faction:
    def __init__(self, **kwargs):
        self.name = "My Faction"
        self.iconPath = "./my_faction_icons"
        self.cardBack = "my-faction-back.png"
        self.deck = []
        self.player = player.Player

        vars(self).update(kwargs.copy())

    def __repr__(self):
        return "Faction " + self.name + " at 0x%x" %  id(self)
