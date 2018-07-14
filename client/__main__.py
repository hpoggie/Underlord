"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

import argparse

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import loadPrcFileData
from direct.task import Task

from network_manager import ConnectionClosed
from network import ClientNetworkManager
from gameServer import Zone
from core.game import Game, Phase, EndOfGame
from core.player import IllegalMoveError
import core.card
from factions import templars, mariners, thieves
from client.mouse import MouseHandler
from client.zoneMaker import ZoneMaker
import client.hud as hud
from client.connectionManager import ConnectionManager
import client.networkInstructions
import client.templarHud as templarHud
import client.marinerHud as marinerHud
import client.thiefHud as thiefHud

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Underlord
    fullscreen 0
    model-path assets
    """)


class App (ShowBase):
    def __init__(self, ip, port, verbose=False, lagSimulation=0):
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

        # Set up the NetworkManager
        instr = client.networkInstructions.NetworkInstructions()
        self.networkManager = ClientNetworkManager(instr, ip, port)
        self.networkManager.verbose = verbose

        # Connect to the server
        self.connectionManager = ConnectionManager((ip, port), self)
        self.connectionManager.tryConnect()
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")

        # Set up lag simulation
        self.lagTimer = self.lagSimulation = lagSimulation

        self.availableFactions = [
            templars.Templar,
            mariners.Mariner,
            thieves.Thief]

        self.hasMulliganed = False

        self.ready = False

    def onConnectedToServer(self):
        self.guiScene = hud.MainMenu()

    @property
    def active(self):
        return self.player.active if hasattr(self, 'player') else False

    @active.setter
    def active(self, value):
        """
        Update whose turn it is.
        """
        # Ignore setting active before mulligans
        # b/c the opcode is False instead of None
        # TODO: change this
        if self.hasMulliganed:
            # (not value) gives us 0 for player 1 and 1 for player 2
            self.game.turn = not value if (
                self.player == self.game.players[0]) else value

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
        if not self.ready:
            self.networkManager.addPlayer()
            self.guiScene.showWaitMessage()
            self.ready = True

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

    def goFirst(self):
        base.networkManager.decideWhetherToGoFirst(1)
        self.onGameStarted(goingFirst=True)

    def goSecond(self):
        base.networkManager.decideWhetherToGoFirst(0)
        self.onGameStarted(goingFirst=False)

    def onGameStarted(self, goingFirst=True):
        self.isFirstPlayer = goingFirst

        # Set up game state information
        if goingFirst:
            self.game = Game(self.faction, self.enemyFaction)
            self.player, self.enemy = self.game.players
        else:
            self.game = Game(self.enemyFaction, self.faction)
            self.enemy, self.player = self.game.players

        self.hasMulliganed = False
        self.bothPlayersMulliganed = False
        self.toMulligan = []

        # Set up the game UI
        if isinstance(self.player, templars.Templar):
            self.guiScene = templarHud.TemplarHud()
        elif isinstance(self.player, mariners.Mariner):
            self.guiScene = marinerHud.MarinerHud()
        elif isinstance(self.player, thieves.Thief):
            self.guiScene = thiefHud.ThiefHud()
        self.zoneMaker = ZoneMaker()

        self.hasFirstPlayerPenalty = goingFirst

    def decideWhetherToGoFirst(self):
        self.guiScene = hud.GoingFirstDecision()

    @property
    def phase(self):
        return self.game.phase

    @phase.setter
    def phase(self, value):
        self.game.phase = value

    def mulligan(self):
        if not self.hasMulliganed:
            indices = [self.player.hand.index(c) for c in self.toMulligan]
            self.networkManager.mulligan(*indices)
            self.hasMulliganed = True
            self.toMulligan = []  # These get GC'd
        else:
            print("Already mulliganed.")

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

    def finishTargeting(self):
        self.targetCallback = None
        self.activeDecision = None
        self.mouseHandler.targeting = False
        self.guiScene.hideTargeting()

    def playCard(self, card, target=None):
        """
        If it's our reveal phase and the card is fast, play it face-up,
        otherwise play it face-down.
        """
        c = card.getPythonTag('card')
        idx = c.zone.index(c)

        if self.phase == Phase.reveal:
            if c.requiresTarget:
                self.networkManager.playFaceup(idx, *self.findCard(target))
            else:
                self.networkManager.playFaceup(idx)
        else:
            self.networkManager.play(idx)

    def revealFacedown(self, card, target=None):
        card = card.getPythonTag('card')
        index = card.zone.index(card)

        self.networkManager.revealFacedown(index, *self.findCard(target))

    def attack(self, card, target):
        try:
            zone, index, enemy = self.findCard(card)
            targetZone, targetIndex, targetsEnemy = self.findCard(target)
        except ValueError as e:
            print("Card not found: " + e)
            return

        self.networkManager.attack(index, targetIndex, targetZone)

    def endPhase(self, *args, **kwargs):
        # For each value in args, append the indices for that value
        # For each value in kwargs, append it if it's a bool, otherwise
        # assume it's a card and append the indices for it
        args = [i for arg in args for i in findCard(arg)] +\
               [i for arg in kwargs.values() for i in ([arg]
                if isinstance(arg, bool) else self.findCard(arg))]

        self.networkManager.endPhase(*args)

        self.hasFirstPlayerPenalty = False

    def replace(self, cards):
        self.networkManager.replace(
            *[card.getPythonTag('zone').index(card.getPythonTag('card'))
                for card in cards])

    def redraw(self):
        self.player.fishing = False
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
        self.ready = False
        return Task.done

    def inputTask(self, task):
        try:
            self.mouseHandler.mouseOverTask()
        except IllegalMoveError as e:
            print(e)

        return Task.cont

    def networkUpdateTask(self, task):
        if self.lagTimer > 0:
            self.lagTimer -= globalClock.getDt()
        else:
            try:
                self.networkManager.recv()
                self.lagTimer = self.lagSimulation
            except ConnectionClosed:
                return Task.done

        return Task.cont


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-v', action='store_true')
parser.add_argument('-a', type=str, default='174.138.119.84')
parser.add_argument('-p', type=int, default=9099)
parser.add_argument('-l', type=float, default=0)
args = parser.parse_args()

app = App(args.a, args.p, args.v, args.l)
app.run()
