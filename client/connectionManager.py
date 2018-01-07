from direct.showbase.DirectObject import DirectObject
from client.connectionUI import ConnectionUI


class ConnectionManager(DirectObject):
    """
    Handles the task of connecting to the server.
    """
    def __init__(self, addr, networkInstructions):
        self.connectionUI = ConnectionUI()
        self.addr, self.networkInstructions = (addr, networkInstructions)

    def tryConnect(self):
        try:
            # connect to the remote server if no arg given
            self.connect()
            self.connectionUI.destroy()
        except ConnectionRefusedError:
            self.connectionUI.showConnectionError(self.retryConnection)
            return

    def connect(self):
        base.networkManager.connect(self.addr)

    def startGame(self):
        base.networkManager.addPlayer()
        base.hud.makeFactionSelectUI()

    def retryConnection(self):
        self.connectionUI.connectingLabel.show()
        self.tryConnect()
