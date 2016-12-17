from copy import deepcopy
from random import shuffle
from enums import *
from ClientNetworkManager import ClientNetworkManager
from Templars import Templars

startHandSize = 5
maxManaCap = 15


class Player ():
    instances = []

    addr = None

    mana = 0

    def __init__(self, name, faction=Templars):
        self.__class__.instances.append(self)

        self.name = name

        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.manaCap = 1
        self.deck = deepcopy(faction.deck)
        self.graveyard = []

        for card in self.deck:
            card.owner = self

            i = 0
            for card2 in self.deck:
                if card == card2:
                    i += 1
                    if i > 1:
                        raise DuplicateCardError(card)

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        shuffle(self.deck)
        for i in range(0, startHandSize):
            self.drawCard()

        self.targetingCardInstance = None

    def drawCard(self):
        if len(self.deck) != 0:
            self.hand.append(self.deck.pop())

    def printHand(self):
        print "Hand:"
        for card in self.hand:
            print card.name

    def printFacedowns(self):
        print "Facedowns:"
        for card in self.facedowns:
            print card.name

    def isActivePlayer(self):
        return self.overlordService.turn == self.index

    def requestTarget(self, card):
        try:
            index = self.faceups.index(card)
            zone = Zone.faceup
        except ValueError:
            try:
                index = self.facedowns.index(card)
                zone = Zone.facedown
            except ValueError:
                pass

        self.overlordService.networkManager.sendInts(
            self.addr,
            ClientNetworkManager.Opcodes.requestTarget,
            zone,
            index
        )

    def getEnemy(self):
        index = 1 if self.__class__.instances[0] == self else 0
        return self.__class__.instances[index]

    def getCard(self, zone, index):
        if zone == Zone.faceup:
            return self.faceups[index]
        elif zone == Zone.facedown:
            return self.facedowns[index]

    # actions

    def play(self, index):
        if not self.isActivePlayer():
            print "Can only play facedowns during your turn."
        elif self.overlordService.phase != Phase.play:
            print "Can only play facedowns during play phase."
        else:
            card = self.hand.pop(index)
            self.facedowns.append(card)
            card.hasAttacked = False
            self.overlordService.redraw()

    def revealFacedown(self, index):
        if not self.isActivePlayer():
            print "Can only reveal facedowns during your turn."
        elif self.overlordService.phase != Phase.reveal:
            print "Can only reveal facedowns during reveal phase."
        elif self.mana < self.facedowns[index].cost:
            print "Not enough mana."
        else:
            card = self.facedowns.pop(index)
            self.mana -= card.cost
            # TODO: change this also.
            if not card.spell:
                self.faceups.append(card)
            else:
                self.graveyard.append(card)
            card.onSpawn()
            self.overlordService.redraw()

    def playFaceup(self, index):
        if not self.isActivePlayer():
            print "Can only play faceups during your turn."
        elif self.overlordService.phase != Phase.reveal:
            print "Can only play faceups during reveal phase."
        elif not self.hand[index].playsFaceUp:
            print "That card does not play face-up."
        elif self.mana < self.hand[index].cost:
            print "Not enough mana."
        else:
            card = self.hand.pop(index)
            self.mana -= card.cost
            self.faceups.append(card)
            self.overlordService.redraw()
            card.onSpawn()
            if card.spell:
                self.graveyard.append(card)
            self.overlordService.redraw()

    def attack(self, cardIndex, targetIndex, zone):
        if not self.isActivePlayer():
            print "It is not your turn."
            return

        attacker = self.faceups[cardIndex]

        if attacker.hasAttacked:
            print "Can only attack once per turn."
        else:
            attacker.hasAttacked = True

            enemy = self.getEnemy()
            if zone == Zone.face:
                enemy.manaCap += attacker.rank
                if enemy.manaCap > 15:
                    print "You're winner"
                    self.win()
            elif zone == Zone.faceup:
                try:
                    self.overlordService.fight(enemy.faceups[targetIndex], attacker)
                except IndexError as e:
                    print "Trying to attack card index that does not exist"
            elif zone == Zone.facedown:
                try:
                    self.overlordService.fight(enemy.facedowns[targetIndex], attacker)
                except IndexError as e:
                    print "Trying to attack card index that does not exist"
            else:
                print "Not a recognized zone."

        self.overlordService.redraw()

    def acceptTarget(self, cardIndex, targetZone, targetIndex):
        enemy = self.getEnemy()
        card = self.getCard(Zone.faceup, cardIndex)

        if targetZone == Zone.facedown:
            card.onGetTarget(enemy.facedowns[targetIndex])
        elif targetZone == Zone.faceup:
            card.onGetTarget(enemy.faceups[targetIndex])
        else:
            raise Exception("Bad zone.")

        self.overlordService.redraw()

    def win(self):
        self.overlordService.networkManager.sendInts(
            self.addr,
            ClientNetworkManager.Opcodes.win,
        )
        self.overlordService.networkManager.sendInts(
            self.getEnemy().addr,
            ClientNetworkManager.Opcodes.lose,
        )
