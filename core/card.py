import types
import inspect
from .decision import Decision


class Ability:
    """
    Used for any event that can raise a Decision
    """
    def __init__(self, func, source):
        # Bind the method to the source so we can invoke it later
        self.func = types.MethodType(func, source)
        self.source = source

    def __call__(self):
        if len(inspect.getargspec(self.func).args) > 1:
            raise Decision(self.execute, self)
        else:
            self.execute()

    def execute(self, *args):
        self.func(*args)
        if self.source.spell:
            self.source.zone = self.source.owner.graveyard


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
        self._taunt = False
        self.owner = None
        self._zone = None
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

    @property
    def taunt(self):
        return self._taunt

    @taunt.setter
    def taunt(self, value):
        self._taunt = value

    def _onSpawn(self):
        if self.spell:
            self.zone = self.owner.graveyard

    def _onDeath(self):
        pass

    def _onFight(self, enemy):
        pass

    @property
    def onSpawn(self):
        return self._onSpawn

    @onSpawn.setter
    def onSpawn(self, func):
        self._onSpawn = Ability(func, self)

    @property
    def onDeath(self):
        return self._onDeath

    @onDeath.setter
    def onDeath(self, func):
        self._onSpawn = Ability(func, self)

    @property
    def onFight(self):
        return self._onFight

    @onFight.setter
    def onFight(self, func):
        self._onFight = types.MethodType(func, self)

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

        if self._zone == self.owner.faceups:
            self.onSpawn()
