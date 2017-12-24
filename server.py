"""
Server script.
Takes the client's actions and computes the results, then sends them back.
"""

from network_manager import ConnectionClosed
from network import ClientNetworkManager, ServerNetworkManager
from core.core import Game, EndOfGame
from core.decision import Decision
from factions.templars import Templar
import time
from core.player import IllegalMoveError
from core.enums import numericEnum
import os
import signal


class ServerError(BaseException):
    pass


Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


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
            raise ServerError("Cannot add more players.")

    def selectFaction(self, addr, index):
        self.factions[dict(self.connections)[addr]] = availableFactions[index]

    def start(self):
        self.game = Game(*self.factions)
        self.game.start()
        self.players = dict([
            (conn[0], self.game.players[conn[1]])
            for conn in self.connections])

        # Add extra data so we can find zones by index
        for pl in self.game.players:
            pl.zones = [
                pl.face,
                pl.faceups,
                pl.facedowns,
                pl.hand,
                pl.graveyard
            ]

        # TODO: kludge
        for i in range(len(self.factions)):
            self.networkManager.connections[self.connections[
                (i + 1) % len(self.factions)][1]].updateEnemyFaction(
                availableFactions.index(self.factions[i]))

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

        self.redraw()

    def attack(self, addr, cardIndex, targetIndex, targetZone):
        pl = self.players[addr]
        try:
            attacker = pl.faceups[cardIndex]
        except IndexError as e:
            print(e)
            return
        if targetZone == Zone.face:
            target = pl.getEnemy().face
        else:
            target = pl.getEnemy().zones[targetZone][targetIndex]

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
                target = pl.getEnemy().zones[targetZone][targetIndex]
            else:
                target = pl.zones[targetZone][targetIndex]
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
                    *(getCard(enemyPlayer, c) if c.visibleWhileFacedown else -1
                        for c in enemyPlayer.facedowns)
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
                    started = hasattr(service, 'game')
                    if None not in service.factions and not started:
                        service.start()
                except Decision as d:
                    service.waitingOnDecision = d
                    service.requestTarget(d.addr)
                except EndOfGame as e:
                    service.endGame(e.winner)
                    exit(0)
                except ConnectionClosed as c:
                    # If you DC, your opponent wins
                    print(c.conn)
                    service.endGame(service.players[c.conn.addr].getEnemy())
                    exit(0)

                time.sleep(0.01)
        else:
            service.networkManager.sock.setblocking(1)
