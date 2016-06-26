import types

class Card:
    owner = None

    name = "Placeholder Name"
    image = "missing.png"
    cost = 0
    rank = 0
    spell = False
    playsFaceUp = False

    def defaultGetCost (self):
        return self.cost

    def defaultGetRank (self):
        return self.rank

    def defaultOnSpawn (self):
        print "card has spawned"

    getCost = defaultGetCost
    getRank = defaultGetRank
    onSpawn = defaultOnSpawn

    def __init__ (self, attributes):
        self.__dict__ = attributes.copy()

    def setCostAbility (self):
        self.getCost = types.MethodType(func, self)

    def setRankAbility (self, func):
        self.getRank = types.MethodType(func, self)

    def setSpawnAbility (self, func):
        self.onSpawn = types.MethodType(func, self)

    def setTargetCallback (self, func):
        self.onGetTarget = types.MethodType(func, self)

    def exposed_getName (self):
        return self.name

    def exposed_getImage (self):
        return self.image

    def exposed_getCost (self):
        return self.getCost()

    def exposed_getRank (self):
        return self.getRank()

    def __print__ (self):
        print self.name + " cost " + cost

class Faction:
    name = "My Faction"
    iconPath = "./my_faction_icons"
    cardBack = "my-faction-back.png"
    deck = []

    def __init__ (self, attributes):
        self.__dict__ = attributes.copy()

def one ():
    return Card({
        'name': "One",
        'image': "dice-six-faces-one.png",
        'cost': 1,
        'rank': 1
        })

def two ():
    return Card({
        'name': "Two",
        'image': "dice-six-faces-two.png",
        'cost': 2,
        'rank': 2
        })

def three ():
    return Card({
        'name': "Three",
        'image': "dice-six-faces-three.png",
        'cost': 3,
        'rank': 3
        })

def four ():
    return Card({
        'name': "Four",
        'image': "dice-six-faces-four.png",
        'cost': 4,
        'rank': 4
        })

def five ():
    return Card({
        'name': "Five",
        'image': "dice-six-faces-five.png",
        'cost': 5,
        'rank': 5
        })

def sweep ():
    def sweepAbility (self):
        for player in self.owner.instances:
            player.faceups = []

    sweep = Card ({
        'name': "Sweep",
        'image': "wind-slap.png",
        'cost': 0,
        'spell': True
    })
    sweep.setSpawnAbility(sweepAbility)

    return sweep

def spellBlade ():
    def onGetTarget (self, target):
        self.owner.overlordService.destroy(target)

    def spellBladeAbility (self):
        self.owner.requestTarget(self)

    spellBlade = Card ({
        'name': "Spell Blade",
        'cost': 0,
        'spell': True,
        'playsFaceUp': True
    })
    spellBlade.setSpawnAbility(spellBladeAbility)
    spellBlade.setTargetCallback(onGetTarget)

    return spellBlade
