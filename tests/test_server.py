import types

import network
from lobbyServer import LobbyServer
from gameServer import GameServer
from client.networkInstructions import NetworkInstructions


lobbyServer = LobbyServer("-v")
port = lobbyServer.networkManager.port
netman0 = network.ClientNetworkManager(
    NetworkInstructions(), "localhost", port)
netman0.connect(("localhost", port))
netman1 = network.ClientNetworkManager(
    NetworkInstructions(), "localhost", port)
netman1.connect(("localhost", port))

netman0.addPlayer()
netman1.addPlayer()


def testSelectFaction():
    netman0.selectFaction(0)
    netman1.selectFaction(0)


class FakeNetworkManager:
    def __init__(self):
        self.connections = [FakeConnection() for i in range(2)]


class FakeConnection:
    def __init__(self):
        # Fill the connection with do-nothing functions
        for key in network.ClientNetworkManager.Opcodes.keys:
            setattr(self, key, lambda: None)

        self.addr = None  # Hack to make GameServer work. change?


def testKickPlayer():
    gs = GameServer(FakeNetworkManager())

    def kick(self):
        self.kicked = True

    c = gs.networkManager.connections[0]
    c.kick = types.MethodType(kick, c)

    gs.kickEveryone()
    assert hasattr(gs.networkManager.connections[0], 'kicked')
