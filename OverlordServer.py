from NetworkManager import NetworkManager
from random import shuffle
from Templars import Templars
from copy import deepcopy
import time

startHandSize = 5
maxManaCap = 15

class Turn ():
    p1 = 0
    p2 = 1

class Phase ():
    reveal = 0
    draw = 1
    attack = 2
    play = 3

class IllegalMoveError (Exception):
    pass

class DuplicateCardError (Exception):
    def __init__ (self, card):
        self.card = card

    def __print__ (self):
        print "Card " + card + " appears more than once."

class ClientNetworkManager (NetworkManager):
    base = None

    class Opcodes:
        updatePlayerHand = 0
        updateEnemyHand = 1
        updatePlayerFacedowns = 2
        updateEnemyFacedowns = 3
        updatePlayerFaceups = 4
        updateEnemyFaceups = 5
        updatePlayerManaCap = 6
        updateEnemyManaCap = 7
        updatePhase = 8

    def onGotPacket (self, packet, addr):
        base = self.base
        Opcodes = self.Opcodes
        segments = [int(x) for x in packet.split(":")]
        print "got opcode, ", segments[0]
        if segments[0] == Opcodes.updatePlayerHand:
            base.updatePlayerHand(segments[1:])
        elif segments[0] == Opcodes.updateEnemyHand:
            base.enemyHandSize = segments[1]
        elif segments[0] == Opcodes.updatePlayerFacedowns:
            base.updatePlayerFacedowns(segments[1:])
        elif segments[0] == Opcodes.updateEnemyFacedowns:
            base.enemyFacedownSize = segments[1]
        elif segments[0] == Opcodes.updatePlayerFaceups:
            base.updatePlayerFaceups(segments[1:])
        elif segments[0] == Opcodes.updatePlayerManaCap:
            base.playerManaCap = segments[1]
        elif segments[0] == Opcodes.updateEnemyManaCap:
            base.enemyManaCap = segments[1]
        elif segments[0] == Opcodes.updatePhase:
            base.phase = segments[1]

class ServerNetworkManager (NetworkManager):
    base = None

    class Opcodes:
        connect = 0
        revealFacedown = 1
        playFaceup = 2
        attack = 3
        playCard = 4
        acceptTarget = 5
        endPhase = 6

    def onGotPacket (self, packet, addr):
        base = self.base
        Opcodes = self.__class__.Opcodes
        operands = [int(x) for x in packet.split(":")]
        print "got opcode, ", operands[0]
        pls = { p.addr : p for p in base.players }
        if operands[0] == Opcodes.connect:
            if len(base.players) < 2:
                p = Player("Player " + str(len(base.players)))
                p.addr = addr
                p.overlordService = self.base
                base.players.append(p)
                base.redraw()
            else:
                print "Cannot add more players."
        elif operands[0] == Opcodes.revealFacedown:
            pls[addr].revealFacedown(operands[1])
        elif operands[0] == Opcodes.playFaceup:
            pls[addr].playFaceup(operands[1])
        elif operands[0] == Opcodes.attack:
            pls[addr].attack(operands[1], operands[2])
        elif operands[0] == Opcodes.playCard:
            pls[addr].play(operands[1])
        elif operands[0] == Opcodes.acceptTarget:
            pls[addr].acceptTarget(operands[1])
        elif operands[0] == Opcodes.endPhase:
            if not pls[addr].isActivePlayer():
                raise IllegalMoveError("It is not your turn.")

            base.endPhase()

turn = Turn.p1
phase = Phase.reveal

class Player ():
    instances = []

    addr = None

    mana = 0

    def __init__ (self, name, faction=Templars):
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
                    if i > 1: raise DuplicateCardError(card)

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        shuffle(self.deck)
        for i in range(0, startHandSize):
            self.drawCard()

        self.targetingCardInstance = None

    def drawCard (self):
        if len(self.deck) != 0:
            self.hand.append(self.deck.pop())

    def printHand (self):
        print "Hand:"
        for card in self.hand:
            print card.name

    def printFacedowns (self):
        print "Facedowns:"
        for card in self.facedowns:
            print card.name

    def isActivePlayer (self):
        return turn == Turn.p1 if self.name == "Player 1" else turn == Turn.p2

    def requestTarget (self, cardInstance):
        self.targetingCardInstance = cardInstance
        key = [key for key in self.overlordService.players if self.overlordService.players[key] == self][0]
        self.overlordService.getTarget(key)

    #actions

    def play (self, index):
        if not self.isActivePlayer():
            raise IllegalMoveError("Can only play facedowns during your turn.")
        elif phase != Phase.play:
            raise IllegalMoveError("Can only play facedowns during play phase.")
        else:
            card = self.hand.pop(index)
            self.facedowns.append(card)
            card.hasAttacked = False

    def revealFacedown (self, index):
        global phase
        if not self.isActivePlayer():
            raise IllegalMoveError("Can only reveal facedowns during your turn.")
        elif phase != Phase.reveal:
            raise IllegalMoveError("Can only reveal facedowns during reveal phase.")
        elif self.mana < self.facedowns[index].cost:
            raise IllegalMoveError("Not enough mana.")
        else:
            card = self.facedowns.pop(index)
            self.mana -= card.cost
            if not card.spell:
                self.faceups.append(card)
            else:
                self.graveyard.append(card)
            card.onSpawn()

    def playFaceup (self, index):
        if not self.isActivePlayer(): raise IllegalMoveError("Can only play faceups during your turn.")
        elif phase != Phase.reveal: raise IllegalMoveError("Can only play faceups during reveal phase.")
        elif not self.hand[index].playsFaceUp: raise IllegalMoveError("That card does not play face-up.")
        elif self.mana < self.hand[index].cost: raise IllegalMoveError("Not enough mana.")
        else:
            card = self.hand.pop(index)
            self.mana -= card.cost
            if not card.spell:
                self.faceups.append(card)
            else:
                self.graveyard.append(card)
            card.onSpawn()

    def acceptTarget (self, targetIndex):
        enemy = None
        for pl in self.instances:
            if pl != self:
                enemy = pl
        self.targetingCardInstance.onGetTarget(enemy.facedowns[targetIndex])
        self.targetingCardInstance = None

class OverlordService:

    def __init__ (self):
        self.networkManager = ServerNetworkManager()
        self.networkManager.startServer()
        self.networkManager.base = self

    players = []

    redrawCallbacks = []
    targetCallbacks = {}

    def getActivePlayer (self):
        return self.players[0] if turn == Turn.p1 else self.players[1]

    def endTurn (self):
        global turn, phase
        player = self.getActivePlayer()
        self.getActivePlayer().manaCap += 1
        self.getActivePlayer().mana = self.getActivePlayer().manaCap
        print "player " +player.name +" mana cap is " +str(player.manaCap)
        turn = not turn
        phase = Phase.reveal

    def endPhase (self, addr):
        global phase

        if phase == Phase.reveal:
            self.getActivePlayer().facedowns = []

        phase += 1

        if phase == Phase.draw:
            self.getActivePlayer().drawCard()
        elif phase == Phase.attack:
            for f in self.getActivePlayer().faceups:
                f.hasAttacked = False
        elif phase == Phase.play:
            pass
        else:
            self.endTurn()

        self.redraw()

    def getTarget (self, playerKey):
        self.targetCallbacks[playerKey]()

    def destroy (self, card):
        for pl in self.exposed_Player.instances:
            try:
                pl.faceups.remove(card)
                pl.graveyard.append(card)
            except ValueError:
                pass
            try:
                pl.facedowns.remove(card)
                pl.graveyard.append(card)
            except ValueError:
                pass

    def fight (self, c1, c2):
        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    def attack (self, cardIndex, targetIndex, zone, playerKey):
        if not self.players[playerKey].isActivePlayer():
            raise IllegalMoveError("It is not your turn.")

        p1 = self.exposed_getLocalPlayer(playerKey)
        p2 = self.exposed_getEnemyPlayer(playerKey)

        if p1.faceups[cardIndex].hasAttacked:
            raise IllegalMoveError("Can only attack once per turn.")
        else:
            p1.faceups[cardIndex].hasAttacked = True

            if zone == 'face':
                p2.manaCap += p1.faceups[cardIndex].rank
            elif zone == 'face-up':
                self.fight(p2.faceups[targetIndex], p1.faceups[cardIndex])
            elif zone == 'face-down':
                self.fight(p2.facedowns[targetIndex], p1.faceups[cardIndex])
            else:
                raise IllegalMoveError("Not a recognized zone.")

    def redraw (self):
        global phase
        def getCard (c):
            for i, tc in enumerate(Templars.deck):
                if tc.name == c.name:
                    return i

        for i, pl in enumerate(self.players):
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerHand,
                *(getCard(c) for c in pl.hand)
                )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerFacedowns,
                *(getCard(c) for c in pl.facedowns)
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerFaceups,
                *(getCard(c) for c in pl.faceups)
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerManaCap,
                pl.manaCap
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePhase,
                phase
            )

            try:
                enemyPlayer = self.players[(i+1) % 2]
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyHand,
                    len(enemyPlayer.hand)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyFacedowns,
                    len(enemyPlayer.facedowns)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyFaceups,
                    *(getCard(c) for c in enemyPlayer.faceups)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyManaCap,
                    enemyPlayer.manaCap
                )
            except IndexError:
                pass


if __name__ == "__main__":
    service = OverlordService()
    while 1:
        service.networkManager.update()
        time.sleep(0.1)
