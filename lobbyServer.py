"""
Use this if you want to run multiple matches at once
This is the way you should usually run the server
"""

import os
import sys
import copy
import random
import time

from network_manager import ConnectionClosed
from network import ServerNetworkManager
from gameServer import GameServer


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
        if conn not in self.readyPlayers:
            self.readyPlayers.append(conn)

    def acceptConnections(self):
        self.networkManager.accept()
        try:
            self.networkManager.recv()
        except ConnectionClosed as c:
            self.networkManager.connections.remove(c.conn)
            try:
                self.readyPlayers.remove(c.conn)
            except ValueError:
                pass
        except AttributeError as e:
            print("Client probably sending stuff it shouldn't: " + str(e))

        # Get the first 2 ready players
        readyPlayers = self.readyPlayers[:2]

        if len(readyPlayers) == 2:
            if self.verbose:
                print("Game time started. Forking subprocess.")
            f = os.fork()
            if f == 0:
                random.seed()  # Regenerate the random seed for this game
                netman = copy.copy(self.networkManager)
                # We need only the players for the game we're currently serving
                netman.connections = self.readyPlayers
                GameServer(netman).run()
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


if __name__ == "__main__":
    lobby = LobbyServer(sys.argv)
    while 1:
        lobby.acceptConnections()
        time.sleep(0.01)
