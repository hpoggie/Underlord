"""
Server script. Takes the client's actions and computes the results, then sends them back.
"""

from network import *
from core import Game
from Templars import Templars
import time


class OverlordService:
    def __init__(self):
        self.networkManager = ServerNetworkManager(self)
        self.networkManager.startServer()

        self.game = Game()
        self.players = {}

    def getPlayer(self, addr):
        return self.players[addr]

    # actions

    # opcode 0
    def addPlayer(self, addr):
        if len(self.players) < 2:
            self.players[addr] = self.game.players[len(self.players)]
            self.players[addr].overlordService = self
            self.redraw()
        else:
            print "Cannot add more players."

    # opcode 1
    def revealFacedown(self, addr, index):
        self.getPlayer(addr).revealFacedown(index)
        self.redraw()

    # opcode 2
    def playFaceup(self, addr, index):
        self.getPlayer(addr).playFaceup(index)
        self.redraw()

    # opcode 3
    def attack(self, addr, cardIndex, targetIndex, zone):
        self.getPlayer(addr).attack(cardIndex, targetIndex, zone)
        self.redraw()

    # opcode 4
    def play(self, addr, index):
        self.getPlayer(addr).play(index)
        self.redraw()

    # opcode 5
    def acceptTarget(self, addr, cardIndex, targetZone, targetIndex):
        self.getPlayer(addr).acceptTarget(cardIndex, targetZone, targetIndex)
        self.redraw()

    # opcode 6
    def endPhase(self, addr):
        self.game.endPhase(self.getPlayer(addr))
        self.redraw()

    def requestTarget(self, player, zone, index):
        addr = self.players.keys()[self.players.values().index(player)]

        self.networkManager.sendInts(
            addr,
            ClientNetworkManager.Opcodes.requestTarget,
            zone,
            index
        )

    def redraw(self):
        def getCard(c):
            for i, tc in enumerate(Templars.deck):
                if tc.name == c.name:
                    return i

        for addr, pl in self.players.iteritems():
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerHand,
                *(getCard(c) for c in pl.hand)
                )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFacedowns,
                *(getCard(c) for c in pl.facedowns)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFaceups,
                *(getCard(c) for c in pl.faceups)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerManaCap,
                pl.manaCap
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePhase,
                self.game.phase
            )

            try:
                enemyPlayer = pl.getEnemy()
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyHand,
                    len(enemyPlayer.hand)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyFacedowns,
                    len(enemyPlayer.facedowns)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyFaceups,
                    *(getCard(c) for c in enemyPlayer.faceups)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyManaCap,
                    enemyPlayer.manaCap
                )
            except IndexError:
                pass

    def endGame(self, winner):
        for addr, pl in self.players.iteritems():
            if pl == winner:
                opcode = ClientNetworkManager.Opcodes.win
            else:
                opcode = ClientNetworkManager.Opcodes.lose

            self.networkManager.sendInts(
                addr,
                opcode
            )

if __name__ == "__main__":
    service = OverlordService()
    i = 0
    while 1:
        service.networkManager.recv()
        i = (i+1) % 100
        if i == 0:
            service.networkManager.sendUnrecievedPackets()
        time.sleep(0.01)
