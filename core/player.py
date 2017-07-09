"""
Player class.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import shuffle
from enums import *

startHandSize = 5
maxManaCap = 15


class Player ():
    def __init__(self, faction):
        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.deck = deepcopy(faction.deck)
        for card in self.deck:
            card.owner = self
        self.graveyard = []
        self.manaCap = 1
        self.mana = 1

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        self.activeAbility = None

    def shuffle(self):
        shuffle(self.deck)

    def drawOpeningHand(self):
        for i in range(0, startHandSize):
            self.drawCard()

    def drawCard(self):
        if len(self.deck) != 0:
            c = self.deck.pop()
            c.moveZone(Zone.hand)

    def isActivePlayer(self):
        return self.game.activePlayer == self

    def getEnemy(self):
        index = 1 if self.game.players[0] == self else 0
        return self.game.players[index]

    def getCard(self, zone, index):
        if zone == Zone.faceup:
            return self.faceups[index]
        elif zone == Zone.facedown:
            return self.facedowns[index]

    def moveCard(self, card, zone):
        if card.zone == Zone.faceup:
            self.faceups.remove(card)
        elif card.zone == Zone.facedown:
            self.facedowns.remove(card)
        elif card.zone == Zone.hand:
            self.hand.remove(card)
        elif card.zone == Zone.graveyard:
            self.graveyard.remove(card)

        if zone == Zone.faceup:
            self.faceups.append(card)
            card.zone = Zone.faceup

            card.onSpawn()
        elif zone == Zone.facedown:
            self.facedowns.append(card)
            card.zone = Zone.facedown
        elif zone == Zone.hand:
            self.hand.append(card)
            card.zone = Zone.hand
        elif zone == Zone.graveyard:
            if card.zone == Zone.faceup:
                card.onDeath()
            self.graveyard.append(card)
            card.zone = Zone.graveyard

    def win(self):
        self.game.end(winner=self)

    # Actions

    def failIfInactive(self, *args):
        if not self.isActivePlayer():
            raise IllegalMoveError("Can only play facedowns during your turn.")

    def play(self, card):
        self.failIfInactive()
        if self.game.phase != Phase.play:
            raise IllegalMoveError("Can only play facedowns during play phase.")

        if card.zone != Zone.hand:
            raise IllegalMoveError("Can't play a card that's not in your hand.")

        self.cancelTarget()

        card.moveZone(Zone.facedown)
        card.hasAttacked = False

    def revealFacedown(self, card):
        self.failIfInactive()
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
        self.failIfInactive()
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
        self.failIfInactive()
        if attacker.hasAttacked:
            raise IllegalMoveError("Can only attack once per turn.")

        if self.game.phase != Phase.play:
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
        self.failIfInactive()
        self.getEnemy().manaCap += attacker.rank
        if self.getEnemy().manaCap > 15:
            self.win()

    def acceptTarget(self, target):
        self.failIfInactive()
        self.activeAbility.execute(target)
        self.activeAbility = None

    def cancelTarget(self):
        self.failIfInactive()
        if self.activeAbility is not None:
            self.activeAbility.execute(None)
            self.activeAbility = None

    def endPhase(self):
        self.failIfInactive()
        self.game.endPhase()

    def endTurn(self):
        self.failIfInactive()
        while self.isActivePlayer():
            self.endPhase()