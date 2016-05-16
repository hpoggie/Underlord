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

        def play (self, index):
            if not self.isActivePlayer():
                raise IllegalMoveError("Can only play facedowns during your turn.")
            elif phase != Phase.play:
                raise IllegalMoveError("Can only play facedowns during play phase.")
            else:
                card = self.hand.pop(index)
                self.facedowns.append(card)

        def printHand (self):
            print "Hand:"
            for card in self.hand:
                print card.name


        def printFacedowns (self):
            print "Facedowns:"
            for card in self.facedowns:
                print card.name

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
                self.faceups.append(card)
                self.mana -= card.cost

        def isActivePlayer (self):
            return turn == Turn.p1 if self.name == "Player 1" else turn == Turn.p2

        def exposed_getHandSize (self):
            return len(self.hand)

    player1 = exposed_Player("Player 1")
    player2 = exposed_Player("Player 2")

    def on_connect (self):
        print "A player has connected."

    def on_disconnect (self):
        print "A player has disconnected."

    def getActivePlayer ():
        global turn, player1, player2
        return player1 if turn == Turn.p1 else player2

    def endTurn ():
        global turn, phase
        player = getActivePlayer()
        getActivePlayer().manaCap += 1
        getActivePlayer().mana = getActivePlayer().manaCap
        print "player " +player.name +" mana cap is " +str(player.manaCap)
        turn = not turn
        phase = Phase.reveal

    def endPhase ():
        global phase
        phase += 1

        if phase == Phase.draw:
            getActivePlayer().drawCard()
        elif phase == Phase.attack:
            pass
        elif phase == Phase.play:
            pass
        else:
            endTurn()

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

    def exposed_getLocalPlayer (self):
        return self.player1

    def exposed_getEnemyPlayer ():
        return self.player2

    def exposed_getPlayerHand (self):
        return self.player1.hand

if __name__ == "__main__":
    from rpyc.utils.server import ThreadedServer
    t = ThreadedServer(OverlordService, port = 18861)
    t.start()
