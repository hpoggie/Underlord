import types
import inspect


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
        self.isValidTarget = True
        self.owner = None
        self._zone = None
        self.visible = False
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

    def cast(self, target=None):
        self.owner.mana -= self.cost
        self.zone = self.owner.faceups
        if self.requiresTarget:
            if target is not None and target.isValidTarget:
                self.onSpawn(target)
        else:
            self.onSpawn()

        if self.spell and not self.continuous:
            self.zone = self.owner.graveyard

    def attack(self, target):
        self.hasAttacked = True

        if target is self.owner.opponent.face:
            self.attackFace()
        else:
            self.game.fight(target, self)

    def attackFace(self):
        self.owner.opponent.manaCap += self.rank

    def onSpawn(self):
        pass

    def onDeath(self):
        pass

    def onDiscard(self):
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
        elif self._zone == self.owner.hand and value == self.owner.graveyard:
            self.onDiscard()

        if self._zone is not None:
            self._zone.remove(self)
        self._zone = value
        self._zone.append(self)
        self.visible = False
        self.hasAttacked = False

    @property
    def controller(self):
        for pl in self.game.players:
            if self.zone in pl.zones:
                return pl

        return self.owner

    @property
    def targetDesc(self):
        if hasattr(self, '_targetDesc'):
            return self._targetDesc
        else:
            return self.desc

    @targetDesc.setter
    def targetDesc(self, value):
        self._targetDesc = value

    @property
    def imagePath(self):
        return self.owner.iconPath + '/' + self.image


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
