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
from core.core import Game, Phase, Turn, EndOfGame
from core.player import IllegalMoveError
from core.decision import Decision
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
        # Client chooses decisions before doing a thing
        # and sends decision / other thing at once
        self._activeDecision = None

    def onConnectedToServer(self):
        self.guiScene = hud.MainMenu()

    @property
    def active(self):
        return self.player.active

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
    def activeDecision(self):
        return self._activeDecision

    @activeDecision.setter
    def activeDecision(self, value):
        self._activeDecision = value
        self.mouseHandler.targeting = value is not None

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
            return (-1, -1, False)

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

        self.activeDecision = None
        self.mouseHandler.targeting = False

    def playCard(self, handCard):
        """
        If it's our reveal phase and the card is fast, play it face-up,
        otherwise play it face-down.
        """
        idx = self.playerHandNodes.index(handCard)

        if self.phase == Phase.reveal:
            try:
                self.player.playFaceup(idx)
            except Decision as d:
                self.activeDecision = d

            self.networkManager.playFaceup(idx)
        else:
            self.player.play(idx)
            self.networkManager.play(idx)
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)

        try:
            self.player.revealFacedown(index)
        except Decision as d:
            self.activeDecision = d
        except EndOfGame:
            pass

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
        try:
            self.player.endPhase()
        except Decision as d:
            self.activeDecision = d
        except EndOfGame:
            pass

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
