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
import copy
import sys


class ServerError(BaseException):
    pass


Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


availableFactions = [Templar]


class LobbyServer:
    def __init__(self, argv):
        self.networkManager = ServerNetworkManager(self)
        self.readyPlayers = []
        self.gameServerProcs = {}
        self.verbose = self.networkManager.verbose = '-v' in argv

    def onClientConnected(self, conn):
        for conn in self.networkManager.connections:
            conn.updateNumPlayers(len(self.networkManager.connections))
        if self.verbose:
            print("Client connected from " + str(conn.addr))

    def requestNumPlayers(self, addr):
        for conn in self.networkManager.connections:
            conn.updateNumPlayers(len(self.networkManager.connections))

    def addPlayer(self, addr):
        conn = next(
            conn for conn in self.networkManager.connections
            if conn.addr == addr)
        self.readyPlayers.append(conn)

    def acceptConnections(self):
        self.networkManager.accept()
        try:
            self.networkManager.recv()
        except ConnectionClosed as c:
            self.networkManager.connections.remove(c.conn)
        except AttributeError as e:
            print("Client probably sending stuff it shouldn't: " + str(e))

        # Get the first 2 ready players
        readyPlayers = self.readyPlayers[:2]

        if len(readyPlayers) == 2:
            if self.verbose:
                print("Game time started. Forking subprocess.")
            f = os.fork()
            if f == 0:
                GameServer(self.networkManager, *readyPlayers).run()
            else:
                self.networkManager.connections = [
                    c for c in self.networkManager.connections
                    if c not in readyPlayers]
                self.gameServerProcs[f] = readyPlayers
                # Remove the 2 players from the list of ready players
                self.readyPlayers = self.readyPlayers[2:]

        while len(self.gameServerProcs) > 0:
            # Clean up when the game server finishes
            pid = os.waitpid(-1, os.WNOHANG)[0]
            if pid != 0:
                self.onGameServerFinished(pid)
            else:
                break

    def onGameServerFinished(self, procid):
        """
        Send the player back to the lobby when the child proc finishes
        """
        for pl in self.gameServerProcs[procid]:
            self.networkManager.connections.append(pl)

        self.gameServerProcs.pop(procid)


class GameServer:
    def __init__(self, netman, *connections):
        self.networkManager = copy.copy(netman)
        self.networkManager.base = self
        # We need only the players for the game we're currently serving
        self.networkManager.connections = connections
        self.addrs = [c.addr for c in self.networkManager.connections]
        self.factions = [None, None]

        self.waitingOnDecision = None

    # actions

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

    def kickEveryone(self):
        for c in self.networkManager.connections:
            c.loseGame()

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
                if hasattr(self, 'players'):
                    self.endGame(self.players[c.conn.addr].getEnemy())
                else:
                    self.kickEveryone()
                exit(0)

            time.sleep(0.01)


if __name__ == "__main__":
    lobby = LobbyServer(sys.argv)
    while 1:
        lobby.acceptConnections()
