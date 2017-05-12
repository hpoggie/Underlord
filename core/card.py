import types
import inspect
from enums import Zone


class Card(object):
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

        for (key, value) in kwargs.iteritems():
            setattr(self, key, value)

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
        print "card has spawned"
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
            self._onSpawn = TargetedAbility(func, self)
        else:
            self._onSpawn = types.MethodType(func, self)

    @property
    def onDeath(self):
        return self._onDeath

    @onDeath.setter
    def onDeath(self, func):
        if len(inspect.getargspec(func).args) > 1:
            self._onDeath = TargetedAbility(func, self)
        else:
            self._onDeath = types.MethodType(func, self)

    def moveZone(self, zone):
        self.owner.moveCard(self, zone)


class TargetedAbility:
    """
    An ability that has targets.

    Called just like a regular ability, but becomes the player's active ability instead of
    immediately executing. Then the player can execute it after getting targets.
    """
    def __init__(self, func, card):
        self.card = card
        self.numTargets = len(inspect.getargspec(func).args)  # TODO: support multiple targets
        self.func = types.MethodType(func, card)

    def __call__(self):
        self.card.owner.activeAbility = self

    def execute(self, *args):
        self.func(*args)


class Faction:
    def __init__(self, **kwargs):
        self.name = "My Faction"
        self.iconPath = "./my_faction_icons"
        self.cardBack = "my-faction-back.png"
        self.deck = []

        vars(self).update(kwargs.copy())
