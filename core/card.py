import types
import inspect

from .decision import Decision


def requiresTarget(ability):
    return hasattr(ability, 'requiresTarget') and ability.requiresTarget


class Card:
    """
    A card has the following characteristics:
        Name
        cost
        rank
        abilities
        image

    It is owned by a player.
    """

    def __init__(self, **kwargs):
        self.name = "Placeholder Name"
        self.image = "missing.png"
        self.spell = False
        self.continuous = False  # If spell, do we stay out after spawn
        self.cost = 0
        self._rank = 0
        self.playsFaceUp = False
        self.taunt = False
        self.owner = None
        self._zone = None
        self.visibleWhileFacedown = False
        self.desc = ""

        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return "%s at 0x%x owned by %s" % (self.name,
                id(self),
                self.owner)

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, value):
        self.spell = value == 's'
        self._rank = value

    @property
    def requiresTarget(self):
        return self.onSpawn.__code__.co_argcount > 1

    def cast(self, *args, **kwargs):
        self.owner.mana -= self.cost
        self.zone = self.owner.faceups
        if self.requiresTarget:
            print(args)
            self.onSpawn(*args, **kwargs)
        else:
            self.onSpawn()

        if self.spell and not self.continuous:
            self.zone = self.owner.graveyard

    def onSpawn(self):
        pass

    def onDeath(self):
        pass

    def beforeFight(self, target):
        pass

    def afterFight(self, target):
        pass

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, value):
        if self._zone == self.owner.faceups and value == self.owner.graveyard:
            self.onDeath()

        if self._zone is not None:
            self._zone.remove(self)
        self._zone = value
        self._zone.append(self)
        self.visibleWhileFacedown = False
        self.hasAttacked = False

    @property
    def targetDesc(self):
        if hasattr(self, '_targetDesc'):
            return self._targetDesc
        else:
            return self.desc

    @targetDesc.setter
    def targetDesc(self, value):
        self._targetDesc = value


def card(t=Card, **kwargs):
    name = kwargs['name'].strip()
    funcs = {}
    others = {}

    for key, val in kwargs.items():
        if hasattr(val, '__call__') or isinstance(val, property):
            funcs[key] = val
        else:
            others[key] = val

    return type(name, (t,), funcs)(**others)
