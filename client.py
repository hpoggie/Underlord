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
from client.hud import Hud
from client.connectionManager import ConnectionManager
import client.networkInstructions

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """)


class App (ShowBase):
    def __init__(self, argv):
        ShowBase.__init__(self)

        self.scene = self.render.attachNewNode('empty')
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.taskMgr.add(self.inputTask, "InputTask")

        self._active = False
        self._started = False

        self.availableFactions = [templars.Templars]

        self.hud = Hud()

        # Connect to the default server if no argument provided
        ip = argv[1] if len(argv) > 1 else "174.138.119.84"
        port = 9099
        self.serverAddr = (ip, port)

        instr = client.networkInstructions.NetworkInstructions()

        self.networkManager = ClientNetworkManager(instr, ip, port)

        self.connectionManager = ConnectionManager(self.serverAddr, instr)
        self.connectionManager.tryConnect()
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")

        # View the cards at an angle
        self.camera.setPosHpr(4, -15, -15, 0, 45, 0)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        if not self._started:
            self.startGame()
            self._started = True

    def pickFaction(self, index):
        self.networkManager.selectFaction(index)
        self.faction = self.availableFactions[index]

    def startGame(self):
        self.player = self.faction.player(self.faction)
        self.enemy = self.enemyFaction.player(self.enemyFaction)
        self.phase = Phase.reveal

        self.playerIconPath = self.faction.iconPath
        self.enemyIconPath = self.enemyFaction.iconPath
        self.playerCardBack = self.faction.cardBack
        self.enemyCardBack = self.enemyFaction.cardBack

        self.hud.makeGameUi()
        self.zoneMaker = ZoneMaker()

    def findCard(self, card):
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
        targetZone, targetIndex, targetsEnemy = self.findCard(target)

        self.networkManager.acceptTarget(
            int(targetsEnemy),
            targetZone,
            targetIndex)

    def playCard(self, handCard):
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
        self.hud.redraw()

    def inputTask(self, task):
        try:
            self.mouseHandler.mouseOverTask()
        except IllegalMoveError as e:
            print(e)

        return Task.cont

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        return Task.cont


app = App(sys.argv)
app.run()
