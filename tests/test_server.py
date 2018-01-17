import server
import network
from client.networkInstructions import NetworkInstructions


lobbyServer = server.LobbyServer("-v")
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
