from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from . import hud


class ConnectionUI(hud.Scene):
    def __init__(self):
        self.connectingLabel = OnscreenText(
            text="connecting to server",
            scale=(0.1, 0.1, 0.1))

    def showConnectionError(self, callback):
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
            command=callback)

    def unmake(self):
        self.connectingLabel.detachNode()
        if hasattr(self, 'connectionFailedLabel'):
            self.connectionFailedLabel.detachNode()
        if hasattr(self, 'reconnectButton'):
            self.reconnectButton.detachNode()
