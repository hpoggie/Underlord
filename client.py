"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue

from network import ClientNetworkManager
from server import Zone
from core.enums import Phase
from core.player import IllegalMoveError

from panda3d.core import loadPrcFileData
from direct.task import Task
from factions import templars

import sys
from client.mouse import MouseHandler
from client.zoneMaker import ZoneMaker
import client.hud as hud
from client.connectionManager import ConnectionManager
import client.networkInstructions
from network_manager import ConnectionClosed

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Underlord
    fullscreen 0
    """)


class App (ShowBase):
    def __init__(self, argv):
        super().__init__()

        # Set up mouse input
        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()
        self.taskMgr.add(self.inputTask, "InputTask")

        # Set up the UI
        self.fonts = hud.Fonts()

        # View the cards at an angle
        self.camera.setPosHpr(4, -15, -15, 0, 45, 0)

        # Connect to the default server if no argument provided
        ip = argv[1] if len(argv) > 1 else "174.138.119.84"
        port = 9099
        self.serverAddr = (ip, port)

        # Set up the NetworkManager
        instr = client.networkInstructions.NetworkInstructions()
        self.networkManager = ClientNetworkManager(instr, ip, port)
        self.networkManager.verbose = '-v' in argv

        # Connect to the server
        self.connectionManager = ConnectionManager(self.serverAddr, self)
        self.connectionManager.tryConnect()
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")

        self.availableFactions = [templars.Templars]

    def onConnectedToServer(self):
        self.guiScene = hud.MainMenu()

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        """
        Update whose turn it is. If we haven't started the game, start it.
        """
        self._active = value
        if not self._started:
            self.onGameStarted()
            self._started = True

    @property
    def guiScene(self):
        return self._guiScene

    @guiScene.setter
    def guiScene(self, value):
        """
        Used to control which menu is being shown
        """
        if hasattr(self, '_guiScene') and self._guiScene:  # TODO: kludge
            self._guiScene.unmake()
        self._guiScene = value

    def readyUp(self):
        """
        We are ready to play a game.
        """
        self.networkManager.addPlayer()
        self.guiScene.showWaitMessage()

    def onEnteredGame(self):
        self.guiScene = hud.FactionSelect()

    def pickFaction(self, index):
        """
        Tell the server we've picked a faction and are ready to start the game.
        """
        self.networkManager.selectFaction(index)
        self.faction = self.availableFactions[index]
        self._active = False
        self._started = False  # Don't show game yet; it hasn't started
        self.guiScene.showWaitMessage() # Tell the user we're waiting for opponent

    def onGameStarted(self):
        # Set up game state information
        self.player = self.faction.player(self.faction)
        self.enemy = self.enemyFaction.player(self.enemyFaction)
        self.phase = Phase.reveal
        self.hasMulliganed = False
        self.toMulligan = []

        # Set up the game UI
        self.guiScene = hud.GameHud()
        self.zoneMaker = ZoneMaker()

    def mulligan(self):
        print("Mulligan")
        self.networkManager.mulligan(
            *[self.playerHandNodes.index(card) for card in self.toMulligan])
        self.hasMulliganed = True
        self.toMulligan = []  # These get GC'd

    def findCard(self, card):
        """
        Given a card node, get its zone, index in that zone, and whether we
        control it
        """
        enemy = True
        index = -1
        zone = -1

        if card.getTag('zone') == 'face-down':
            index = self.playerFacedownNodes.index(card)
            zone = Zone.facedown
            enemy = False
        elif card.getTag('zone') == 'enemy face-down':
            index = self.enemyFacedownNodes.index(card)
            zone = Zone.facedown
        elif card.getTag('zone') == 'face-up':
            # TODO: hack
            # Search player faceup nodes to see if we own the card
            if card in self.playerFaceupNodes:
                index = self.playerFaceupNodes.index(card)
                enemy = False
            else:
                index = self.enemyFaceupNodes.index(card)
            zone = Zone.faceup
        elif card.getTag('zone') == 'hand':
            index = self.playerHandNodes.index(card)
            zone = Zone.hand
            enemy = False
        elif card.getTag('zone') == 'face':
            zone = Zone.face
            if card is self.playerFaceNode:  # TODO: hack
                enemy = False

        return (zone, index, enemy)

    def acceptTarget(self, target):
        """
        Give the server the target for the currently active ability
        """
        targetZone, targetIndex, targetsEnemy = self.findCard(target)

        self.networkManager.acceptTarget(
            int(targetsEnemy),
            targetZone,
            targetIndex)

    def playCard(self, handCard):
        """
        If it's our reveal phase and the card is fast, play it face-up,
        otherwise play it face-down.
        """
        if self.phase == Phase.reveal:
            self.networkManager.playFaceup(
                self.playerHandNodes.index(handCard))
        else:
            self.networkManager.play(
                self.playerHandNodes.index(handCard))
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.networkManager.revealFacedown(index)
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def attack(self, card, target):
        try:
            zone, index, enemy = self.findCard(card)
            targetZone, targetIndex, targetsEnemy = self.findCard(target)
        except ValueError as e:
            print("Card not found: " + e)
            return

        if enemy:
            raise IllegalMoveError("Card is not yours.")
        if zone is not Zone.faceup:
            raise IllegalMoveError("Can only attack with faceups.")

        if not targetsEnemy:
            raise IllegalMoveError("Can't attack your own stuff.")
        if targetZone not in (Zone.faceup, Zone.facedown, Zone.face):
            raise IllegalMoveError("Not a valid attack target.")

        self.networkManager.attack(index, targetIndex, targetZone)

        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()
        self.zoneMaker.makeEnemyBoard()

    def endPhase(self):
        self.networkManager.endPhase()

    def redraw(self):
        self.zoneMaker.redrawAll()
        self.guiScene.redraw()

    def quitToMainMenu(self):
        self.taskMgr.doMethodLater(
            1, self._quitToMainMenuTask, "QuitToMainMenu")

    def _quitToMainMenuTask(self, task):
        if hasattr(self, 'zoneMaker'):  # TODO: kludge
            self.zoneMaker.unmake()
        self.guiScene = hud.MainMenu()
        self.networkManager.requestNumPlayers()
        return Task.done

    def inputTask(self, task):
        try:
            self.mouseHandler.mouseOverTask()
        except IllegalMoveError as e:
            print(e)

        return Task.cont

    def networkUpdateTask(self, task):
        try:
            self.networkManager.recv()
        except ConnectionClosed:
            return Task.done
        return Task.cont


app = App(sys.argv)
app.run()
