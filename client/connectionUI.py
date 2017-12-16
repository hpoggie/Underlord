from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText


class ConnectionUI(DirectObject):
    def __init__(self, ip):
        self.connectingLabel = OnscreenText(
            text="connecting to server",
            scale=(0.1, 0.1, 0.1))

        try:
            # connect to the remote server if no arg given
            base.connect(ip)
            base.makeFactionSelectUI()
            self.connectingLabel.detachNode()
        except ConnectionRefusedError:
            self.showConnectionError()
            return

    def showConnectionError(self):
        self.connectingLabel.hide()
        self.connectionFailedLabel = OnscreenText(
            text="Error. Could not connect to server",
            pos=(0, 0, 0),
            scale=(0.1, 0.1, 0.1))
        self.reconnectButton = DirectButton(
            pos=(0, 0, -0.25),
            scale=(0.1, 0.1, 0.1),
            image="./reconnect.png",
            relief=None,
            command=self.retryConnection)

    def retryConnection(self):
        try:
            self.connectingLabel.show()
            base.connect(self.serverIp)
            self.connectingLabel.detachNode()
            self.connectionFailedLabel.detachNode()
            self.reconnectButton.detachNode()
            base.makeFactionSelectUI()
        except ConnectionRefusedError:
            pass
