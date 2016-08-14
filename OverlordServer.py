import rpyc
from random import shuffle
from Templars import Templars
from copy import deepcopy

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

turn = Turn.p1
phase = Phase.reveal

class OverlordService (rpyc.Service):
    class exposed_Player ():
        instances = []

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

        def exposed_play (self, index):
            if not self.isActivePlayer():
                raise IllegalMoveError("Can only play facedowns during your turn.")
            elif phase != Phase.play:
                raise IllegalMoveError("Can only play facedowns during play phase.")
            else:
                card = self.hand.pop(index)
                self.facedowns.append(card)
                card.hasAttacked = False

        def exposed_revealFacedown (self, index):
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

        def exposed_playFaceup (self, index):
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

        def exposed_acceptTarget (self, targetIndex):
            enemy = None
            for pl in self.instances:
                if pl != self:
                    enemy = pl
            self.targetingCardInstance.onGetTarget(enemy.facedowns[targetIndex])
            self.targetingCardInstance = None

        #getters

        def exposed_getHandSize (self):
            return len(self.hand)

        def exposed_getHand (self, index):
            return self.hand[index]

        def exposed_getFaceups (self):
            return self.faceups

        def exposed_getFacedowns (self):
            return self.facedowns

        def exposed_getIconPath (self):
            return self.iconPath

        def exposed_getCardBack (self):
            return self.cardBack

        def exposed_getManaCap (self):
            return self.manaCap

    player1 = exposed_Player("Player 1")
    player2 = exposed_Player("Player 2")

    players = {}

    redrawCallbacks = []
    targetCallbacks = {}

    def on_connect (self):
        print "A player has connected."
        self.player1.overlordService = self
        self.player2.overlordService = self

    def on_disconnect (self):
        print "A player has disconnected."

    def getActivePlayer (self):
        return self.player1 if turn == Turn.p1 else self.player2

    def endTurn (self):
        global turn, phase
        player = self.getActivePlayer()
        self.getActivePlayer().manaCap += 1
        self.getActivePlayer().mana = self.getActivePlayer().manaCap
        print "player " +player.name +" mana cap is " +str(player.manaCap)
        turn = not turn
        phase = Phase.reveal

    def exposed_registerPlayer (self, playerName):
        self.players[playerName] = self.player1 if len(self.players) == 0 else self.player2

    def exposed_setRedrawCallback (self, f):
        self.redrawCallbacks.append(rpyc.async(f))

    def exposed_addTargetCallback (self, playerKey, f):
        self.targetCallbacks[playerKey] = f
        print "adding target callback"

    def exposed_endPhase (self, playerKey):
        if not self.players[playerKey].isActivePlayer():
            raise IllegalMoveError("It is not your turn.")

        self.endPhase()

    def endPhase (self):
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

    def exposed_getPhase (self):
        if phase == Phase.reveal:
            return "Reveal"
        elif phase == Phase.draw:
            return "Draw"
        elif phase == Phase.attack:
            return "Attack"
        elif phase == Phase.play:
            return "Play"
        else:
            return "Unknown phase %d" % phase

    def exposed_getLocalPlayer (self, playerKey):
        return self.players[playerKey]

    def exposed_getEnemyPlayer (self, playerKey):
        return self.player1 if self.players[playerKey] == self.player2 else self.player2

    def exposed_getPlayerHand (self, playerKey):
        return self.players[playerKey].hand

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

    def exposed_attack (self, cardIndex, targetIndex, zone, playerKey):
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
        for c in self.redrawCallbacks:
            c()

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(OverlordService, port = 18861)
    t.start()
