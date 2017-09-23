"""
Server script. Takes the client's actions and computes the results, then sends them back.
"""

from network import *
from core.core import Game, EndOfGame
from core.card import Decision
from factions.templars import Templar
import time
from core.enums import IllegalMoveError, Zone
import os
import signal

availableFactions = [Templar]

class OverlordService:
    def __init__(self):
        self.networkManager = ServerNetworkManager(self)
        self.networkManager.startServer()
        self.connections = []
        self.factions = [None, None]

        self.waitingOnDecision = None

    # actions

    def addPlayer(self, addr):
        if len(self.connections) < 2:
            self.connections.append((addr, len(self.connections)))
        else:
            print("Cannot add more players.")

    def selectFaction(self, addr, index):
        self.factions[dict(self.connections)[addr]] = availableFactions[index]
        if None not in self.factions:
            self.start()

    def start(self):
        self.game = Game(*self.factions)
        self.game.start()
        self.players = dict([(conn[0], self.game.players[conn[1]]) for conn in self.connections])

        # TODO: kludge
        for i in range(len(self.factions)):
            self.networkManager.sendInts(
                    self.connections[(i + 1) % len(self.factions)][0],
                    ClientNetworkManager.Opcodes.updateEnemyFaction,
                    availableFactions.index(self.factions[i])
                    )

        self.redraw()

    def revealFacedown(self, addr, index):
        pl = self.players[addr]
        try:
            pl.revealFacedown(pl.facedowns[index])
        except IllegalMoveError as e:
            print(e)
            return
        except IndexError as e:
            print(e)
            return
        except Decision as d:
            self.waitingOnDecision = d
            self.requestTarget(addr)

        self.redraw()

    def playFaceup(self, addr, index):
        pl = self.players[addr]
        try:
            pl.playFaceup(pl.hand[index])
        except IllegalMoveError as e:
            print(e)
            return
        except IndexError as e:
            print(e)
            return
        except Decision as d:
            self.waitingOnDecision = d
            self.requestTarget(addr)

        self.redraw()

    def attack(self, addr, cardIndex, targetIndex, targetZone):
        pl = self.players[addr]
        try:
            attacker = pl.faceups[cardIndex]
        except IndexError as e:
            print(e)
            return
        if targetZone == Zone.face:
            target = Zone.face
        else:
            target = pl.getEnemy().getCard(targetZone, targetIndex)

        try:
            pl.attack(attacker, target)
        except IllegalMoveError as e:
            print(e)
        self.redraw()

    def play(self, addr, index):
        pl = self.players[addr]
        try:
            pl.play(pl.hand[index])
        except IllegalMoveError as e:
            print(e)
        except IndexError as e:
            print(e)
            return
        self.redraw()

    def acceptTarget(self, addr, targetsEnemy, targetZone, targetIndex):
        pl = self.players[addr]
        try:
            if targetsEnemy:
                target = pl.getEnemy().getCard(targetZone, targetIndex)
            else:
                target = pl.getCard(targetZone, targetIndex)
            self.waitingOnDecision.execute(target)
            self.waitingOnDecision = None
        except IllegalMoveError as e:
            print(e)
        except IndexError as e:
            print(e)
            return
        self.redraw()

    def endPhase(self, addr):
        try:
            self.players[addr].endPhase()
        except IllegalMoveError as e:
            print(e)
        self.redraw()

    def requestTarget(self, addr):
        self.networkManager.sendInts(
            addr,
            ClientNetworkManager.Opcodes.requestTarget
        )

    def redraw(self):
        def getCard(pl, c):
            for i, tc in enumerate(pl.faction.deck):
                if tc.name == c.name:
                    return i

        for addr, pl in self.players.items():
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.setActive,
                int(pl.isActivePlayer())
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerHand,
                *(getCard(pl, c) for c in pl.hand)
                )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFacedowns,
                *(getCard(pl, c) for c in pl.facedowns)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFaceups,
                *(getCard(pl, c) for c in pl.faceups)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerManaCap,
                pl.manaCap
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerMana,
                pl.mana
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
                    *(getCard(enemyPlayer, c) if c.visibleWhileFacedown else -1 for c in enemyPlayer.facedowns)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyFaceups,
                    *(getCard(enemyPlayer, c) for c in enemyPlayer.faceups)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyManaCap,
                    enemyPlayer.manaCap
                )
            except IndexError:
                pass

    def endGame(self, winner):
        for addr, pl in self.players.items():
            if pl == winner:
                opcode = ClientNetworkManager.Opcodes.winGame
            else:
                opcode = ClientNetworkManager.Opcodes.loseGame

            self.networkManager.sendInts(
                addr,
                opcode
            )

if __name__ == "__main__":
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    service = OverlordService()
    while 1:
        service.networkManager.accept()
        if os.fork() == 0:
            while 1:
                try:
                    service.networkManager.recv()
                except EndOfGame as e:
                    service.endGame(e.winner)
                    exit(0)

                time.sleep(0.01)
        else:
            service.networkManager.close()
            service.networkManager.sock.setblocking(1)
