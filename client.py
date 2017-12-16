"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText

from network import ClientNetworkManager, ServerNetworkManager
from server import Zone
from core.enums import Phase

from panda3d.core import loadPrcFileData
from direct.task import Task
from factions import templars

import sys
from client.mouse import MouseHandler
from client.connectionUI import ConnectionUI
from client.zoneMaker import ZoneMaker

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """)


class IllegalMoveError (Exception):
    pass


class App (ShowBase):
    def __init__(self, argv):
        ShowBase.__init__(self)

        self.port = 9099

        self.scene = self.render.attachNewNode('empty')
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.taskMgr.add(self.mouseOverTask, "MouseOverTask")

        self._active = False
        self._started = False

        # Connect to the default server if no argument provided
        ip = argv[1] if len(argv) > 1 else "174.138.119.84"
        self.connectionUI = ConnectionUI(ip)

    def connect(self, ip):
        self.serverIp = ip
        self.networkManager = ClientNetworkManager(self, self.serverIp)
        self.serverAddr = (self.serverIp, self.port)
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")
        self.networkManager.connect(self.serverAddr)
        self.networkManager.send("0", self.serverAddr)

    def loadModel(self, name):
        ret = self.loader.loadModel(name + ".bam")
        return ret

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        if not self._started:
            self.startGame()
            self._started = True

    def makeFactionSelectUI(self):
        self.factionSelectLabel = OnscreenText(
            text="faction select",
            pos=(0, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.availableFactions = [templars.Templars]

        self.factionButtons = []

        for i, faction in enumerate(self.availableFactions):
            self.factionButtons.append(DirectButton(
                image=faction.iconPath + '/' + faction.cardBack,
                pos=(i * 0.2, 0, 0),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=self.pickFaction,
                extraArgs=[i]))

    def pickFaction(self, index):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.selectFaction,
            index)

        self.faction = self.availableFactions[index]

        self.factionSelectLabel.detachNode()

    def startGame(self):
        self.player = self.faction.player(self.faction)
        self.enemy = self.enemyFaction.player(self.enemyFaction)
        self.phase = Phase.reveal

        self.playerIconPath = self.faction.iconPath
        self.enemyIconPath = self.enemyFaction.iconPath
        self.playerCardBack = self.faction.cardBack
        self.enemyCardBack = self.enemyFaction.cardBack
        self.makeGameUi()

        for button in self.factionButtons:
            button.destroy()
        del self.factionButtons

    def makeGameUi(self):
        self.turnLabel = OnscreenText(
            text="",
            pos=(0, -0.9, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.playerManaCapLabel = OnscreenText(
            text=str(self.player.manaCap),
            pos=(-0.4, -0.44, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.enemyManaCapLabel = OnscreenText(
            text=str(self.enemy.manaCap),
            pos=(-0.5, 0.77),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.cardNameLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = OnscreenText(
            text="",
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = OnscreenText(
            text="",
            pos=(0.7, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.endPhaseButton = DirectButton(
            image="./end_phase.png",
            pos=(0.7, 0, -0.85),
            scale=(0.1, 0.1, 0.1),
            relief=None,
            command=self.endPhase)

        self.zoneMaker = ZoneMaker()

    def updateEnemyFaction(self, index):
        self.enemyFaction = self.availableFactions[index]

    def updatePlayerHand(self, *cardIds):
        self.player.hand = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.hand[i] = self.faction.deck[x]
            self.player.hand[i].owner = self.player
        self.redraw()

    def updateEnemyHand(self, size):
        self.enemy.hand = [None] * size

    def updatePlayerFacedowns(self, *cardIds):
        self.player.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.facedowns[i] = self.faction.deck[x]
            self.player.facedowns[i].owner = self.player
        self.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        self.enemy.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            card = self.enemyFaction.deck[x]
            self.enemy.facedowns[i] = card if x != -1 else None
            if x != -1:
                self.enemy.facedowns[i].owner = self.enemy
        self.redraw()

    def updatePlayerFaceups(self, *cardIds):
        self.player.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.faceups[i] = self.faction.deck[x]
            self.player.faceups[i].owner = self.player
        self.redraw()

    def updateEnemyFaceups(self, *cardIds):
        self.enemy.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.enemy.faceups[i] = self.enemyFaction.deck[x]
            self.enemy.faceups[i].owner = self.enemy
        self.redraw()

    def updatePlayerManaCap(self, manaCap):
        self.player.manaCap = manaCap
        self.redraw()

    def updatePlayerMana(self, mana):
        self.player.mana = mana
        self.redraw()

    def updateEnemyManaCap(self, manaCap):
        self.enemy.manaCap = manaCap
        self.redraw()

    def updatePhase(self, phase):
        self.phase = phase

    def setActive(self, value):
        self.active = bool(value)

    def winGame(self):
        self.winLabel = OnscreenText(
            text="Victory",
            scale=(0.5, 0.5, 0.5))

    def loseGame(self):
        self.winLabel = OnscreenText(
            text="Defeat",
            scale=(0.5, 0.5, 0.5))

    def requestTarget(self):
        self.mouseHandler.targeting = True

    def acceptTarget(self, target):
        targetsEnemy = True
        targetIndex = -1
        targetZone = -1
        if target.getTag('zone') == 'face-down':
            try:
                targetIndex = self.playerFacedownNodes.index(target)
                targetZone = Zone.facedown
                targetsEnemy = False
            except ValueError as e:
                print(e)
        if target.getTag('zone') == 'enemy face-down':
            try:
                targetIndex = self.enemyFacedownNodes.index(target)
                targetZone = Zone.facedown
            except ValueError as e:
                print(e)
        elif target.getTag('zone') == 'face-up':
            try:
                targetIndex = self.enemyFaceupNodes.index(target)
                targetZone = Zone.faceup
            except ValueError as e:
                print(e)
        elif target.getTag('zone') == 'hand':
            try:
                targetIndex = self.playerHandNodes.index(target)
                targetZone = Zone.hand
                targetsEnemy = False
            except ValueError as e:
                print(e)

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.acceptTarget,
            int(targetsEnemy),
            targetZone,
            targetIndex)

    def playCard(self, handCard):
        if self.phase == Phase.reveal:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.playFaceup,
                self.playerHandNodes.index(handCard)
            )
        else:
            self.networkManager.sendInts(
                self.serverAddr,
                ServerNetworkManager.Opcodes.play,
                self.playerHandNodes.index(handCard)
            )
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.revealFacedown,
            index
        )
        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()

    def attack(self, card, target):
        try:
            index = self.playerFaceupNodes.index(card)
        except ValueError:
            print("That card is not one of your faceups.")
            return
        targetIndex = 0
        zone = 0
        if target.getTag('zone') == 'face':
            if target == self.playerFaceNode:
                print("Can't attack yourself.")
                return
            zone = Zone.face
        elif target.getTag('zone') == 'enemy face-down':
            targetIndex = self.enemyFacedownNodes.index(target)
            zone = Zone.facedown
        else:
            if target in self.playerFaceupNodes:
                print("Can't attack your own faceups.")
                return
            targetIndex = self.enemyFaceupNodes.index(target)
            zone = Zone.faceup

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.attack,
            index,
            targetIndex,
            zone
        )

        self.zoneMaker.makePlayerHand()
        self.zoneMaker.makeBoard()
        self.zoneMaker.makeEnemyBoard()

    def endPhase(self):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.endPhase
        )

    def redraw(self):
        self.zoneMaker.redrawAll()
        self.endPhaseLabel.setText(str(Phase.keys[self.phase]))
        self.turnLabel.setText("Your Turn" if self.active else "Enemy Turn")
        if self.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()
        if self.phase == Phase.reveal and self.active:
            self.playerManaCapLabel.setText(
                str(self.player.mana) + " / " + str(self.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(self.player.manaCap))
        self.enemyManaCapLabel.setText(str(self.enemy.manaCap))

    def mouseOverTask(self, name):
        if self.mouseWatcherNode.hasMouse():
            if hasattr(self, 'cardNameLabel'):
                self.cardNameLabel.setText("")

            if hasattr(self, 'cardStatsLabel'):
                self.cardStatsLabel.setText("")

            if hasattr(self, 'tooltipLabel'):
                if hasattr(self, 'phase') and self.active:
                    self.tooltipLabel.setText(
                        "Reveal face-down cards" if self.phase == Phase.reveal
                        else "Play face-down cards and attack")
                else:
                    self.tooltipLabel.setText("")

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = self.playerIconPath + "/" + self.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            pickedObj = self.mouseHandler.getObjectClickedOn()
            if pickedObj:
                if pickedObj.getTag('zone') == 'hand':
                    card = self.player.hand[
                        self.playerHandNodes.index(pickedObj)]
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(
                        ("Instant. " if card.playsFaceUp else "") + card.desc)
                elif pickedObj.getTag('zone') == 'face-down':
                    card = self.player.facedowns[
                        self.playerFacedownNodes.index(pickedObj)]
                    self._activeObj = pickedObj
                    path = self.playerIconPath + "/" + card.image
                    pickedObj.setTexture(loader.loadTexture(path))
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'enemy face-down':
                    card = self.enemy.facedowns[
                        self.enemyFacedownNodes.index(pickedObj)]
                    if card is not None:
                        self._activeObj = pickedObj
                        path = self.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        label = str(card.cost) + " " + str(card.rank)
                        self.cardStatsLabel.setText(label)
                        self.tooltipLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'face-up':
                    if pickedObj in self.playerFaceupNodes:
                        card = self.player.faceups[
                            self.playerFaceupNodes.index(pickedObj)]
                    else:
                        card = self.enemy.faceups[
                            self.enemyFaceupNodes.index(pickedObj)]
                    self.cardNameLabel.setText(card.name)
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.tooltipLabel.setText(card.desc)

        return Task.cont

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        return Task.cont


app = App(sys.argv)
app.camera.setPosHpr(4, -15, -15, 0, 45, 0)
app.run()
