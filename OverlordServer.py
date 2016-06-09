import rpyc
from random import shuffle
from Templars import Templars

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

turn = Turn.p1
phase = Phase.reveal

class OverlordService (rpyc.Service):
    class exposed_Player ():
        mana = 0

        def __init__ (self, name, faction=Templars):
            self.name = name

            self.hand = []
            self.facedowns = []
            self.faceups = []
            self.manaCap = 1
            self.deck = list(faction.deck)

            self.iconPath = faction.iconPath
            self.cardBack = faction.cardBack

            shuffle(self.deck)
            for i in range(0, startHandSize):
                self.drawCard()

        def drawCard (self):
            if len(self.deck) != 0:
                self.hand.append(self.deck.pop())

        def exposed_play (self, index):
            if not self.isActivePlayer():
                raise IllegalMoveError("Can only play facedowns during your turn.")
            elif phase != Phase.play:
                raise IllegalMoveError("Can only play facedowns during play phase.")
            else:
                card = self.hand.pop(index)
                self.facedowns.append(card)
                card.hasAttacked = False

        def printHand (self):
            print "Hand:"
            for card in self.hand:
                print card.name

        def printFacedowns (self):
            print "Facedowns:"
            for card in self.facedowns:
                print card.name

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
                self.faceups.append(card)
                self.mana -= card.cost

        def isActivePlayer (self):
            return turn == Turn.p1 if self.name == "Player 1" else turn == Turn.p2

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

    def on_connect (self):
        print "A player has connected."

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

    def destroy (self, card):
        if card in self.player1.faceups: self.player1.faceups.remove(card)
        if card in self.player1.facedowns: self.player1.faceups.remove(card)
        if card in self.player2.faceups: self.player2.faceups.remove(card)
        if card in self.player2.facedowns: self.player2.facedowns.remove(card)

    def fight (self, c1, c2):
        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    def exposed_attack (self, cardIndex, targetIndex, playerKey):
        if not self.players[playerKey].isActivePlayer():
            raise IllegalMoveError("It is not your turn.")

        p1 = self.getLocalPlayer(playerKey)
        p2 = self.getEnemyPlayer(playerKey)

        if p1.faceups[cardIndex].hasAttacked:
            raise IllegalMoveError("Can only attack once per turn.")
        else:
            p1.faceups[cardIndex].hasAttacked = True

            if targetIndex == "face":
                p2.manaCap += p1.faceups[cardIndex].rank
            else:
                self.fight(p2.faceups[targetIndex], p1.faceups[cardIndex])

    def exposed_attackFacedown (self, cardIndex, targetIndex, playerKey):
        p1 = self.player1
        p2 = self.player2
        self.fight(p2.facedowns[targetIndex], p1.faceups[cardIndex])

    def redraw (self):
        for c in self.redrawCallbacks:
            c()

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(OverlordService, port = 18861)
    t.start()
