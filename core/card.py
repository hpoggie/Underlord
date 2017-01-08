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
        self.cost = 0
        self.rank = 0
        self.spell = False
        self.playsFaceUp = False
        self.owner = None
        self.zone = None

        vars(self).update(kwargs.copy())

    def defaultGetCost(self):
        return self.cost

    def defaultGetRank(self):
        return self.rank

    def defaultOnSpawn(self):
        print "card has spawned"
        if self.spell:
            self.moveZone(Zone.graveyard)

    def defaultOnDeath(self):
        print "card has died"

    getCost = defaultGetCost
    getRank = defaultGetRank
    onSpawn = defaultOnSpawn
    onDeath = defaultOnDeath

    def setCostAbility(self, func):
        self.getCost = types.MethodType(func, self)

    def setRankAbility(self, func):
        self.getRank = types.MethodType(func, self)

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


def one():
    return Card(
        name="One",
        image="dice-six-faces-one.png",
        cost=1,
        rank=1
        )


def two():
    return Card(
        name="Two",
        image="dice-six-faces-two.png",
        cost=2,
        rank=2
        )


def three():
    return Card(
        name="Three",
        image="dice-six-faces-three.png",
        cost=3,
        rank=3
        )


def four():
    return Card(
        name="Four",
        image="dice-six-faces-four.png",
        cost=4,
        rank=4
        )


def five():
    return Card(
        name="Five",
        image="dice-six-faces-five.png",
        cost=5,
        rank=5
        )


def sweep():
    def sweepAbility(self):
        for player in self.game.players:
            for c in player.faceups:
                c.moveZone(Zone.graveyard)

        self.moveZone(Zone.graveyard)

    sweep = Card(
        name="Sweep",
        image="wind-slap.png",
        cost=0,
        spell=True
    )
    sweep.setSpawnAbility(sweepAbility)

    return sweep


def spellBlade():
    def spellBladeAbility(self, target):
        if target in self.owner.getEnemy().facedowns:
            self.game.destroy(target)

        self.moveZone(Zone.graveyard)

    spellBlade = Card(
        name="Spell Blade",
        image="wave-strike.png",
        cost=0,
        spell=True,
        playsFaceUp=True
    )
    spellBlade.onSpawn = TargetedAbility(spellBladeAbility, spellBlade)

    return spellBlade
