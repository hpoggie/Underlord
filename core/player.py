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
