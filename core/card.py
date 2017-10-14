import types
import inspect
from .decision import Decision
from .enums import Zone


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
        self._cost = 0
        self._rank = 0
        self.playsFaceUp = False
        self.owner = None
        self.zone = None
        self.visibleWhileFacedown = False
        self.desc = ""

        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def beforeEvent(self, eventName, *args, **kwargs):
        pass

    def afterEvent(self, eventName, *args, **kwargs):
        pass

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, value):
        self._cost = value

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, value):
        self._rank = value

    def _onSpawn(self):
        if self.spell:
            self.moveZone(Zone.graveyard)

    def _onDeath(self):
        pass

    @property
    def onSpawn(self):
        return self._onSpawn

    @onSpawn.setter
    def onSpawn(self, func):
        if len(inspect.getargspec(func).args) > 1:
            self._onSpawn = Decision(func, self)
        else:
            self._onSpawn = types.MethodType(func, self)

    @property
    def onDeath(self):
        return self._onDeath

    @onDeath.setter
    def onDeath(self, func):
        if len(inspect.getargspec(func).args) > 1:
            self._onDeath = Decision(func, self)
        else:
            self._onDeath = types.MethodType(func, self)

    def moveZone(self, zone):
        self.owner.moveCard(self, zone)
        self.visibleWhileFacedown = False
