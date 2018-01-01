"""
Server script.
Takes the client's actions and computes the results, then sends them back.
"""

from network_manager import ConnectionClosed
from network import ServerNetworkManager
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


class Server:
    def __init__(self):
        self.networkManager = ServerNetworkManager(self)
        self.networkManager.startServer()
        self.addrs = []
        self.factions = [None, None]

        self.waitingOnDecision = None

    # actions

    def addPlayer(self, addr):
        if len(self.addrs) < 2:
            self.addrs.append(addr)
        else:
            raise ServerError("Cannot add more players.")

    def selectFaction(self, addr, index):
        self.factions[self.addrs.index(addr)] = availableFactions[index]

    def start(self):
        self.game = Game(*self.factions)
        self.game.start()
        self.players = dict([
            (addr, self.game.players[i])
            for i, addr in enumerate(self.addrs)])
        # Make it easy to find connections by addr
        self.connections = dict([
            (addr, self.networkManager.connections[i])
            for i, addr in enumerate(self.addrs)])

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
            self.networkManager.connections[
                (i + 1) % len(self.factions)].updateEnemyFaction(
                availableFactions.index(self.factions[i]))

        self.redraw()

    def revealFacedown(self, addr, index):
        pl = self.players[addr]
        pl.revealFacedown(pl.facedowns[index])
        self.redraw()

    def playFaceup(self, addr, index):
        pl = self.players[addr]
        pl.playFaceup(pl.hand[index])
        self.redraw()

    def attack(self, addr, cardIndex, targetIndex, targetZone):
        pl = self.players[addr]
        attacker = pl.faceups[cardIndex]
        if targetZone == Zone.face:
            target = pl.getEnemy().face
        else:
            target = pl.getEnemy().zones[targetZone][targetIndex]

        pl.attack(attacker, target)
        self.redraw()

    def play(self, addr, index):
        pl = self.players[addr]
        pl.play(pl.hand[index])
        self.redraw()

    def acceptTarget(self, addr, targetsEnemy, targetZone, targetIndex):
        pl = self.players[addr]
        if targetsEnemy:
            target = pl.getEnemy().zones[targetZone][targetIndex]
        else:
            target = pl.zones[targetZone][targetIndex]
        self.waitingOnDecision.execute(target)
        self.waitingOnDecision = None
        self.redraw()

    def endPhase(self, addr):
        self.players[addr].endPhase()
        self.redraw()

    def requestTarget(self, addr):
        self.connections[addr].requestTarget()

    def redraw(self):
        def getCard(pl, c):
            for i, tc in enumerate(pl.faction.deck):
                if tc.name == c.name:
                    return i

        for addr, pl in self.players.items():
            c = self.connections[addr]
            c.setActive(int(pl.isActivePlayer()))
            c.updatePlayerHand(*(getCard(pl, c) for c in pl.hand))
            c.updatePlayerFacedowns(*(getCard(pl, c) for c in pl.facedowns))
            c.updatePlayerFaceups(*(getCard(pl, c) for c in pl.faceups))
            c.updatePlayerManaCap(pl.manaCap)
            c.updatePlayerMana(pl.mana)
            c.updatePhase(self.game.phase)

            enemyPlayer = pl.getEnemy()
            c.updateEnemyHand(len(enemyPlayer.hand))
            c.updateEnemyFacedowns(
                *(getCard(enemyPlayer, c) if c.visibleWhileFacedown else -1
                    for c in enemyPlayer.facedowns)
            )
            c.updateEnemyFaceups(
                *(getCard(enemyPlayer, c) for c in enemyPlayer.faceups)
            )
            c.updateEnemyManaCap(enemyPlayer.manaCap)

    def endGame(self, winner):
        for addr, pl in self.players.items():
            if pl == winner:
                self.connections[addr].winGame()
            else:
                self.connections[addr].loseGame()

    def run(self):
        while 1:
            try:
                self.networkManager.recv()
                started = hasattr(self, 'game')
                if None not in self.factions and not started:
                    self.start()
            except IndexError as e:
                print(e)
            except IllegalMoveError as e:  # Client sent us an illegal move
                print(e)
            except Decision as d:
                self.waitingOnDecision = d
                self.requestTarget(d.addr)
            except EndOfGame as e:
                self.endGame(e.winner)
                exit(0)
            except ConnectionClosed as c:
                # If you DC, your opponent wins
                print(c.conn)
                self.endGame(self.players[c.conn.addr].getEnemy())
                exit(0)

            time.sleep(0.01)


if __name__ == "__main__":
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    service = Server()
    while 1:
        for i in range(2):
            service.networkManager.accept()
        if os.fork() == 0:
            service.run()
        else:
            service.networkManager.sock.setblocking(1)
