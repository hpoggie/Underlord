"""
Player class.
It has some actions associated with it that the player can take.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import shuffle
from enums import *

# TODO: add possibility of multiple factions
from factions.templars import Templars


startHandSize = 5
maxManaCap = 15


class Player ():
    def __init__(self, faction=Templars):
        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.deck = deepcopy(faction.deck)
        for card in self.deck:
            card.owner = self
        self.graveyard = []
        self.manaCap = 1
        self.mana = 0

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

    # actions

    def play(self, index):
        if not self.isActivePlayer():
            print "Can only play facedowns during your turn."
        elif self.game.phase != Phase.play:
            print "Can only play facedowns during play phase."
        else:
            self.cancelTarget()

            card = self.hand[index]
            card.moveZone(Zone.facedown)
            card.hasAttacked = False

    def revealFacedown(self, index):
        if not self.isActivePlayer():
            print "Can only reveal facedowns during your turn."
        elif self.game.phase != Phase.reveal:
            print "Can only reveal facedowns during reveal phase."
        elif self.mana < self.facedowns[index].cost:
            print "Not enough mana."
        else:
            self.cancelTarget()

            card = self.facedowns[index]
            self.mana -= card.cost
            card.moveZone(Zone.faceup)

    def playFaceup(self, index):
        if not self.isActivePlayer():
            print "Can only play faceups during your turn."
        elif self.game.phase != Phase.reveal:
            print "Can only play faceups during reveal phase."
        elif not self.hand[index].playsFaceUp:
            print "That card does not play face-up."
        elif self.mana < self.hand[index].cost:
            print "Not enough mana."
        else:
            self.cancelTarget()

            card = self.hand[index]
            self.mana -= card.cost
            card.moveZone(Zone.faceup)

    def attack(self, cardIndex, targetIndex, targetZone):
        enemy = self.getEnemy()
        attacker = self.faceups[cardIndex]
        target = enemy.getCard(targetZone, targetIndex)

        if not self.isActivePlayer():
            print "It is not your turn."
            return

        if attacker.hasAttacked:
            print "Can only attack once per turn."
            return

        if self.game.phase != Phase.attack:
            print "Can only attack during attack phase."
            return

        attacker.hasAttacked = True

        if targetZone == Zone.face:
            self.attackFace(attacker)
        else:
            self.game.fight(target, attacker)

    def attackFace(self, attacker):
        self.getEnemy().manaCap += attacker.rank
        if self.getEnemy().manaCap > 15:
            print "You're winner"
            self.win()

    def acceptTarget(self, targetZone, targetIndex):
        enemy = self.getEnemy()

        if targetZone == Zone.facedown:
            self.activeAbility.execute(enemy.facedowns[targetIndex])
            self.activeAbility = None
        elif targetZone == Zone.faceup:
            self.activeAbility.execute(enemy.faceups[targetIndex])
            self.activeAbility = None
        else:
            raise Exception("Bad zone.")

    def cancelTarget(self):
        if self.activeAbility is not None:
            self.activeAbility.execute(None)
            self.activeAbility = None
