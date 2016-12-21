"""
Server script. Takes the client's actions and computes the results, then sends them back.
"""

from ServerNetworkManager import ServerNetworkManager
from ClientNetworkManager import ClientNetworkManager
from Player import Player
from enums import *
from Templars import Templars
import time


class DuplicateCardError (Exception):
    def __init__(self, card):
        self.card = card

    def __print__(self):
        print "Card " + card + " appears more than once."


class OverlordService:
    def __init__(self):
        self.networkManager = ServerNetworkManager()
        self.networkManager.startServer()
        self.networkManager.base = self

        self.turn = Turn.p1
        self.phase = Phase.reveal

    players = []

    redrawCallbacks = []
    targetCallbacks = {}

    def addPlayer(self, addr):
        if len(self.players) < 2:
            p = Player("Player " + str(len(self.players)))
            p.index = len(self.players)
            p.addr = addr
            p.overlordService = self
            self.players.append(p)
            self.redraw()
        else:
            print "Cannot add more players."

    def getActivePlayer(self):
        return self.players[self.turn]

    def endTurn(self):
        player = self.getActivePlayer()
        self.getActivePlayer().manaCap += 1
        if self.getActivePlayer().manaCap > 15:
            self.getActivePlayer().getEnemy().win()
        self.getActivePlayer().mana = self.getActivePlayer().manaCap
        print "player " + player.name + " mana cap is " + str(player.manaCap)
        self.turn = not self.turn
        self.phase = Phase.reveal

    def endPhase(self, addr):
        if self.phase == Phase.reveal:
            self.getActivePlayer().facedowns = []

        self.phase += 1

        if self.phase == Phase.draw:
            self.getActivePlayer().drawCard()
        elif self.phase == Phase.attack:
            for f in self.getActivePlayer().faceups:
                f.hasAttacked = False
        elif self.phase == Phase.play:
            pass
        else:
            self.endTurn()

        self.redraw()

    def getTarget(self, playerKey):
        self.targetCallbacks[playerKey]()

    def destroy(self, card):
        card.moveZone(Zone.graveyard)

    def fight(self, c1, c2):
        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    def redraw(self):
        def getCard(c):
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
                self.phase
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
    i = 0
    while 1:
        service.networkManager.recv()
        i = (i+1) % 100
        if i == 0:
            service.networkManager.sendUnrecievedPackets()
        time.sleep(0.01)
