"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

import sys

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import loadPrcFileData
from direct.task import Task

from network_manager import ConnectionClosed
from network import ClientNetworkManager
from server import Zone
from core.game import Game, Phase, Turn, EndOfGame
from core.player import IllegalMoveError
import core.card
from factions import templars
from client.mouse import MouseHandler
from client.zoneMaker import ZoneMaker
import client.hud as hud
from client.connectionManager import ConnectionManager
import client.networkInstructions

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Underlord
    fullscreen 0
    model-path assets
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
        return self.player.active if hasattr(self, 'player') else False

    @active.setter
    def active(self, value):
        """
        Update whose turn it is. If we haven't started the game, start it.
        """
        if not self._started:
            self.onGameStarted()
            self._started = True

        # Ignore setting active before mulligans
        # b/c the opcode is False instead of None
        # TODO: change this
        if self.hasMulliganed:
            self.game.turn = Turn.p1 if value else Turn.p2

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

        # Tell the user we're waiting for opponent
        self.guiScene.showWaitMessage()

    def onGameStarted(self):
        # Set up game state information
        self.game = Game(templars.Templar, templars.Templar)
        self.player, self.enemy = self.game.players
        self.game.start()
        self.hasMulliganed = False
        self.bothPlayersMulliganed = False
        self.toMulligan = []

        # Set up the game UI
        self.guiScene = hud.GameHud()
        self.zoneMaker = ZoneMaker()

    def decideWhetherToGoFirst(self):
        self.guiScene = hud.GoingFirstDecision()

    @property
    def phase(self):
        return self.game.phase

    @phase.setter
    def phase(self, value):
        self.game.phase = value

    def mulligan(self):
        indices = [self.player.hand.index(c) for c in self.toMulligan]
        self.player.mulligan(*self.toMulligan)
        # Don't know what their cards are but do this to trigger effects
        self.enemy.mulligan()
        self.networkManager.mulligan(*indices)
        self.hasMulliganed = True
        self.toMulligan = []  # These get GC'd

    def findCard(self, card):
        """
        Given a card node, get its zone, index in that zone, and whether we
        control it
        """
        if card is None:
            return (-1, -1, 0)

        enemy = True
        index = -1
        zone = -1

        if card.getPythonTag('zone') is self.player.facedowns:
            zone = Zone.facedown
            enemy = False
        elif card.getPythonTag('zone') is self.enemy.facedowns:
            zone = Zone.facedown
        elif card.getPythonTag('zone') is self.player.faceups:
            zone = Zone.faceup
            enemy = False
        elif card.getPythonTag('zone') is self.enemy.faceups:
            zone = Zone.faceup
        elif card.getPythonTag('zone') is self.player.hand:
            zone = Zone.hand
            enemy = False
        elif card.getPythonTag('zone') is self.player.face:
            zone = Zone.face
            enemy = False
        elif card.getPythonTag('zone') is self.enemy.face:
            zone = Zone.face

        try:
            c = card.getPythonTag('card')
            index = card.getPythonTag('zone').index(c)
        except ValueError:
            pass

        return (zone, index, int(enemy))

    def acceptTarget(self, target):
        self.callback(target)
        self.callback = None
        self.activeDecision = None
        self.mouseHandler.targeting = False
        self.guiScene.hideTargeting()

    def playCard(self, card, target=None):
        """
        If it's our reveal phase and the card is fast, play it face-up,
        otherwise play it face-down.
        """
        idx = self.playerHandNodes.index(card)

        if self.phase == Phase.reveal:
            if core.card.requiresTarget(card.getPythonTag('card').onSpawn):
                self.player.playFaceup(idx, target.getPythonTag('card'))
                self.networkManager.playFaceup(idx, *self.findCard(target))
            else:
                self.networkManager.playFaceup(idx)
        else:
            self.player.play(idx)
            self.networkManager.play(idx)

        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def revealFacedown(self, card, target=None):
        index = self.playerFacedownNodes.index(card)
        card = card.getPythonTag('card')

        try:
            self.player.revealFacedown(index, target)
        except EndOfGame:
            pass

        self.networkManager.revealFacedown(index, *self.findCard(target))
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def attack(self, card, target):
        try:
            zone, index, enemy = self.findCard(card)
            targetZone, targetIndex, targetsEnemy = self.findCard(target)
        except ValueError as e:
            print("Card not found: " + e)
            return

        self.networkManager.attack(index, targetIndex, targetZone)

        self.zoneMaker.makeBoard()
        self.zoneMaker.makeEnemyBoard()

    def endPhase(self, target):
        try:
            self.player.endPhase(target)
        except EndOfGame:
            pass

        self.networkManager.endPhase(*self.findCard(target))

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
