import types
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

    owner = None

    name = "Placeholder Name"
    image = "missing.png"
    cost = 0
    rank = 0
    spell = False
    playsFaceUp = False

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

    def __init__(self, attributes):
        self.__dict__ = attributes.copy()
        self.zone = None

    def setCostAbility(self, func):
        self.getCost = types.MethodType(func, self)

    def setRankAbility(self, func):
        self.getRank = types.MethodType(func, self)

    def setSpawnAbility(self, func):
        self.onSpawn = types.MethodType(func, self)

    def setDeathAbility(self, func):
        self.onDeath = types.MethodType(func, self)

    def setTargetCallback(self, func):
        self.onGetTarget = types.MethodType(func, self)

    def getName(self):
        return self.name

    def getImage(self):
        return self.image

    def __print__(self):
        print self.name + " cost " + cost

    def moveZone(self, zone):
        if self.zone == Zone.faceup:
            self.owner.faceups.remove(self)
        elif self.zone == Zone.facedown:
            self.owner.facedowns.remove(self)
        elif self.zone == Zone.hand:
            self.owner.hand.remove(self)
        elif self.zone == Zone.graveyard:
            self.owner.graveyard.remove(self)

        if zone == Zone.faceup:
            self.owner.faceups.append(self)
            self.zone = Zone.faceup

            if self.owner.overlordService:
                self.owner.overlordService.redraw()

            self.onSpawn()
        elif zone == Zone.facedown:
            self.owner.facedowns.append(self)
            self.zone = Zone.facedown
        elif zone == Zone.hand:
            self.owner.hand.append(self)
            self.zone = Zone.hand
        elif zone == Zone.graveyard:
            if self.zone == Zone.faceup:
                self.onDeath()
            self.owner.graveyard.append(self)
            self.zone = Zone.graveyard

        if self.owner.overlordService:
            self.owner.overlordService.redraw()


class Faction:
    name = "My Faction"
    iconPath = "./my_faction_icons"
    cardBack = "my-faction-back.png"
    deck = []

    def __init__(self, attributes):
        self.__dict__ = attributes.copy()


def one():
    return Card({
        'name': "One",
        'image': "dice-six-faces-one.png",
        'cost': 1,
        'rank': 1
        })


def two():
    return Card({
        'name': "Two",
        'image': "dice-six-faces-two.png",
        'cost': 2,
        'rank': 2
        })


def three():
    return Card({
        'name': "Three",
        'image': "dice-six-faces-three.png",
        'cost': 3,
        'rank': 3
        })


def four():
    return Card({
        'name': "Four",
        'image': "dice-six-faces-four.png",
        'cost': 4,
        'rank': 4
        })


def five():
    return Card({
        'name': "Five",
        'image': "dice-six-faces-five.png",
        'cost': 5,
        'rank': 5
        })


def sweep():
    def sweepAbility(self):
        for player in self.owner.instances:
            for c in player.faceups:
                c.moveZone(Zone.graveyard)

        self.moveZone(Zone.graveyard)

    sweep = Card({
        'name': "Sweep",
        'image': "wind-slap.png",
        'cost': 0,
        'spell': True
    })
    sweep.setSpawnAbility(sweepAbility)

    return sweep


def spellBlade():
    def onGetTarget(self, target):
        if target in self.owner.getEnemy().facedowns:
            self.owner.overlordService.destroy(target)

        self.moveZone(Zone.graveyard)

    def spellBladeAbility(self):
        self.owner.requestTarget(self)

    spellBlade = Card({
        'name': "Spell Blade",
        'image': "wave-strike.png",
        'cost': 0,
        'spell': True,
        'playsFaceUp': True
    })
    spellBlade.setSpawnAbility(spellBladeAbility)
    spellBlade.setTargetCallback(onGetTarget)

    return spellBlade
