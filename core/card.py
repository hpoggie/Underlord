import types
import inspect
from enums import Zone


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

        vars(self).update(kwargs.copy())

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

    def onSpawn(self):
        print "card has spawned"
        if self.spell:
            self.moveZone(Zone.graveyard)

    def onDeath(self):
        print "card has died"

    def setSpawnAbility(self, func):
        self.onSpawn = types.MethodType(func, self)

    def setDeathAbility(self, func):
        self.onDeath = types.MethodType(func, self)

    def getName(self):
        return self.name

    def getImage(self):
        return self.image

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
        self.numTargets = len(inspect.getargspec(func))  # TODO: support multiple targets
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
