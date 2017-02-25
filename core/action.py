import types
from enums import *

"""
Most actions have many different ways they can fail.
Also, more code can be added to an action at runtime.
This is a way to handle that.
"""


class Action:
    def __init__(self, player, funcs):
        self.funcs = [types.MethodType(func, player) for func in funcs]

    def __call__(self, *args):
        for func in self.funcs:
            func(*args)


def failIfInactive(self, *args):
    if not self.isActivePlayer():
        raise IllegalMoveError("Can only play facedowns during your turn.")


def play(self, card):
    if self.game.phase != Phase.play:
        raise IllegalMoveError("Can only play facedowns during play phase.")

    if card.zone != Zone.hand:
        raise IllegalMoveError("Can't play a card that's not in your hand.")

    self.cancelTarget()

    card.moveZone(Zone.facedown)
    card.hasAttacked = False


def revealFacedown(self, card):
    if self.game.phase != Phase.reveal:
        raise IllegalMoveError("Can only reveal facedowns during reveal phase.")

    if self.mana < card.cost:
        raise IllegalMoveError("Not enough mana.")

    if card.zone != Zone.facedown:
        raise IllegalMoveError("Can't reveal a card that's not face-down.")

    self.cancelTarget()

    self.mana -= card.cost
    card.moveZone(Zone.faceup)


def playFaceup(self, card):
    if self.game.phase != Phase.reveal:
        raise IllegalMoveError("Can only play faceups during reveal phase.")

    if card not in self.hand:
        raise IllegalMoveError("Can't play a card face-up that's not in hand.")

    if not card.playsFaceUp:
        raise IllegalMoveError("That card does not play face-up.")

    if self.mana < card.cost:
        raise IllegalMoveError("Not enough mana.")

    self.cancelTarget()

    self.mana -= card.cost
    card.moveZone(Zone.faceup)


def attack(self, attacker, target):
    if attacker.hasAttacked:
        raise IllegalMoveError("Can only attack once per turn.")

    if self.game.phase != Phase.attack:
        raise IllegalMoveError("Can only attack during attack phase.")

    if attacker.zone != Zone.faceup:
        raise IllegalMoveError("Can only attack with face-up cards.")

    if target != Zone.face and target.zone not in [Zone.faceup, Zone.facedown]:
        raise IllegalMoveError("Can only attack face-up / face-down targets or a player.")

    attacker.hasAttacked = True

    if target == Zone.face:
        self.attackFace(attacker)
    else:
        self.game.fight(target, attacker)


def attackFace(self, attacker):
    self.getEnemy().manaCap += attacker.rank
    if self.getEnemy().manaCap > 15:
        print "You're winner"
        self.win()


def acceptTarget(self, target):
    self.activeAbility.execute(target)
    self.activeAbility = None


def cancelTarget(self):
    if self.activeAbility is not None:
        self.activeAbility.execute(None)
        self.activeAbility = None


def endPhase(self):
    self.game.endPhase()

actions = {
    'play': [failIfInactive, play],
    'revealFacedown': [failIfInactive, revealFacedown],
    'playFaceup': [failIfInactive, revealFacedown],
    'attack': [failIfInactive, attack],
    'acceptTarget': [failIfInactive, acceptTarget],
    'cancelTarget': [failIfInactive, cancelTarget],
    'endPhase': [failIfInactive, endPhase]
}


def setupActions(player):
    global actions
    from action import Action
    vars(player).update(dict((key, Action(player, value)) for key, value in actions.iteritems()))
