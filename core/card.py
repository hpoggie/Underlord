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

    def __repr__(self):
        return "%s at 0x%x owned by %s" % (self.name,
                id(self),
                self.owner)

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
        if hasattr(self._onSpawn, 'bind'):
            self._onSpawn.bind(self)
        return self._onSpawn

    @onSpawn.setter
    def onSpawn(self, func):
        class SpawnAbility:
            """
            Helps discard spells after abilities happen
            """
            def __init__(self, func):
                self.baseFunc = func

            def bind(self, source):
                """
                Bind the method to the source so we can invoke it
                Done when the property is retrieved to prevent copying problems
                """
                if not hasattr(self, 'source'):
                    self.func = types.MethodType(func, source)
                    self.source = source

            @property
            def requiresTarget(self):
                return len(inspect.getargspec(self.func).args) > 1

            @property
            def decision(self):
                if hasattr(self.source, 'targetDesc'):
                    desc = self.source.targetDesc
                else:
                    desc = self.source.desc

                return Decision(self.execute, self, desc)

            def __call__(self):
                if self.requiresTarget:
                    if hasattr(self.source, 'targetDesc'):
                        desc = self.source.targetDesc
                    else:
                        desc = self.source.desc

                    raise Decision(self.execute, self, desc)
                else:
                    self.execute()

            def execute(self, *args):
                self.func(*args)
                if self.source.spell:
                    self.source.zone = self.source.owner.graveyard

        self._onSpawn = SpawnAbility(func)

    @property
    def onDeath(self):
        return self._onDeath

    @onDeath.setter
    def onDeath(self, func):
        self._onSpawn = types.MethodType(func, self)

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

    @property
    def targetDesc(self):
        if hasattr(self, '_targetDesc'):
            return self._targetDesc
        else:
            return self.desc

    @targetDesc.setter
    def targetDesc(self, value):
        self._targetDesc = value
