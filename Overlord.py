"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import CollisionNode, GeomNode, CollisionRay
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText

from ClientNetworkManager import ClientNetworkManager
from ServerNetworkManager import ServerNetworkManager
from enums import *
from Player import Player

from panda3d.core import loadPrcFileData
from direct.task import Task
import Templars
import types

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """
    )


class IllegalMoveError (Exception):
    pass


class MouseHandler (DirectObject):
    showCollisions = False

    def __init__(self):
        self.accept('mouse1', self.onMouse1, [])

        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        base.cTrav.addCollider(pickerNP, base.handler)
        if self.showCollisions:
            base.cTrav.showCollisions(render)
        base.disableMouse()

        self.activeCard = None
        self.targeting = None

    def getObjectClickedOn(self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            base.cTrav.traverse(render)
            if (base.handler.getNumEntries() > 0):
                base.handler.sortEntries()
                pickedObj = base.handler.getEntry(0).getIntoNodePath()
                pickedObj = pickedObj.findNetTag('zone')
                return pickedObj

    def doClick(self):
        pickedObj = self.getObjectClickedOn()

        if self.targeting is not None:
            if pickedObj is not None:
                base.acceptTarget(pickedObj)
                self.targeting = None
            return

        if pickedObj and not pickedObj.isEmpty():
            if pickedObj.getTag('zone') == 'hand':
                try:
                    base.playCard(pickedObj)
                except IllegalMoveError as error:
                    print error
            elif pickedObj.getTag('zone') == 'face-down':
                if not self.activeCard:
                    try:
                        base.revealFacedown(pickedObj)
                    except IllegalMoveError as error:
                        print error
                else:
                    print self.activeCard.name + " attacks " + pickedObj.name
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face-up':
                if not self.activeCard:
                    self.activeCard = pickedObj
                else:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face':
                if self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
                else:
                    if pickedObj == base.playerFaceNode:
                        print "p. mc %d" % base.player.manaCap
                    elif pickedObj == base.enemyFaceNode:
                        print "e. mc %d" % base.enemy.manaCap
        else:
            self.activeCard = None

    def onMouse1(self):
        self.doClick()


class App (ShowBase):
    handPos = 0.0
    enemyHandPos = 0.0
    playerFacePos = (0, 0, 1)
    enemyFacePos = (0, 0, -1)
    playerHandNodes = []
    enemyHandNodes = []
    fdPos = 0.0
    enemyFdPos = 0.0
    playerFacedownNodes = []
    enemyFacedownNodes = []
    playerFaceupNodes = []
    enemyFaceupNodes = []

    serverIp = "localhost"
    port = 9099

    player = Player("Player")
    enemy = Player("Enemy")
    phase = Phase.reveal

    def updatePlayerHand(self, cardIds):
        self.player.hand = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.hand[i] = Templars.Templars.deck[x]  # TODO
            self.player.hand[i].owner = self.player
        self.redraw()

    def updateEnemyHand(self, size):
        self.enemy.hand = [None] * size

    def updatePlayerFacedowns(self, cardIds):
        self.player.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.facedowns[i] = Templars.Templars.deck[x]
            self.player.facedowns[i].doIControl = True
        self.redraw()

    def updateEnemyFacedowns(self, size):
        self.enemy.facedowns = [None] * size
        self.redraw()

    def updatePlayerFaceups(self, cardIds):
        self.player.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.player.faceups[i] = Templars.Templars.deck[x]
            self.player.faceups[i].doIControl = True
        self.redraw()

    def updateEnemyFaceups(self, cardIds):
        self.enemy.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            self.enemy.faceups[i] = Templars.Templars.deck[x]
            self.enemy.faceups[i].doIControl = False
        self.redraw()

    def updatePlayerManaCap(self, manaCap):
        self.player.manaCap = manaCap
        self.redraw()

    def updateEnemyManaCap(self, manaCap):
        self.enemy.manaCap = manaCap
        self.redraw()

    def winGame(self):
        self.winLabel = OnscreenText(
            text="Victory",
            scale=(0.5, 0.5, 0.5)
            )

    def loseGame(self):
        self.winLabel = OnscreenText(
            text="Defeat",
            scale=(0.5, 0.5, 0.5)
            )

    def __init__(self):
        ShowBase.__init__(self)
        self.scene = self.loader.loadModel("empty.obj")
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.playerIconPath = Templars.Templars.iconPath
        self.enemyIconPath = Templars.Templars.iconPath
        self.playerCardBack = Templars.Templars.cardBack
        self.enemyCardBack = Templars.Templars.cardBack

        self.endPhaseButton = DirectButton(
                image="./concentric-crescents.png",
                pos=(0, 0, -0.5),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=self.endPhase
                )
        self.endPhaseLabel = OnscreenText(
                text=str(self.phase),
                pos=(0, -0.7, 0),
                scale=(0.1, 0.1, 0.1)
                )
        self.playerManaCapLabel = OnscreenText(
                text=str(self.player.manaCap),
                pos=(-0.5, -0.44, 0),
                scale=(0.1, 0.1, 0.1),
                )
        self.enemyManaCapLabel = OnscreenText(
                text=str(self.enemy.manaCap),
                pos=(-0.5, 0.77),
                scale=(0.1, 0.1, 0.1),
                )
        self.cardStatsLabel = OnscreenText(
                text="",
                pos=(-0.7, -0.7, 0),
                scale=(0.1, 0.1, 0.1)
                )
        self.taskMgr.add(self.mouseOverTask, "MouseOverTask")

        print len(self.player.hand)
        self.makeHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

        self.networkManager = ClientNetworkManager(self)
        self.serverAddr = (self.serverIp, self.port)
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")
        self.networkManager.send("0", self.serverAddr)

    def getTarget(self, zone, index):
        self.mouseHandler.targeting = self.player.getCard(zone, index)

    def acceptTarget(self, target):
        targetIndex = -1
        targetZone = -1
        if target.getTag('zone') == 'face-down':
            targetIndex = self.enemyFacedownNodes.index(target)
            targetZone = Zone.facedown
        elif target.getTag('zone') == 'face-up':
            targetIndex = self.enemyFaceupNodes.index(target)
            targetZone = Zone.faceup

        cardIndex = self.player.faceups.index(self.mouseHandler.targeting)

        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.acceptTarget,
            cardIndex,
            targetZone,
            targetIndex
            )

    def makeHand(self):
        for i in self.playerHandNodes:
            i.detachNode()
            self.handPos = 0.0
        self.playerHandNodes = []
        for i in range(0, len(self.player.hand)):
            self.addHandCard(self.player.hand[i])

    def makeEnemyHand(self):
        for i in self.enemyHandNodes:
            i.detachNode()
            self.enemyHandPos = 0.0
        self.enemyHandNodes = []
        for i in range(0, len(self.enemy.hand)):
            self.addEnemyHandCard()

    def makeBoard(self):
        for i in self.playerFacedownNodes:
            i.detachNode()
        self.playerFacedownNodes = []
        for i in self.playerFaceupNodes:
            i.detachNode()
        self.playerFaceupNodes = []
        self.fdPos = 0.0
        for i in self.player.faceups:
            self.addFaceupCard(i)
        for i in self.player.facedowns:
            self.addFdCard(i)

    def makeEnemyBoard(self):
        for i in self.enemyFacedownNodes:
            i.detachNode()
        self.enemyFacedownNodes = []
        for i in self.enemyFaceupNodes:
            i.detachNode()
        self.enemyFaceupNodes = []
        self.enemyFdPos = 0.0
        for i in self.enemy.faceups:
            self.addEnemyFaceupCard(i)
        for i in range(0, len(self.enemy.facedowns)):
            self.addEnemyFdCard()

    def addHandCard(self, card):
        cm = CardMaker(card.getName())
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + card.getImage()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.handPos, 0, 0)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'hand')
        self.handPos += 1.1
        self.playerHandNodes.append(cardModel)

    def addEnemyHandCard(self):
        cm = CardMaker('enemy hand card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyHandPos, 0, 3.1)
        cardModel.setTag('card', 'enemy hand card')
        cardModel.setTag('zone', 'enemy hand')
        self.enemyHandPos += 1.1
        self.enemyHandNodes.append(cardModel)

    def addFdCard(self, card):
        cm = CardMaker('face-down card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.playerCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.fdPos, 0, 1.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-down')
        self.fdPos += 1.1
        self.playerFacedownNodes.append(cardModel)

    def addEnemyFdCard(self):
        cm = CardMaker('face-down card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyFdPos, 0, 2.1)
        cardModel.setTag('card', 'enemy face-down card')
        cardModel.setTag('zone', 'face-down')
        self.enemyFdPos += 1.1
        self.enemyFacedownNodes.append(cardModel)

    def addFaceupCard(self, card):
        cm = CardMaker(card.getName())
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + card.getImage()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.fdPos, 0, 1.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-up')
        self.fdPos += 1.1
        self.playerFaceupNodes.append(cardModel)

    def addEnemyFaceupCard(self, card):
        cm = CardMaker(card.getName())
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + card.getImage()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyFdPos, 0, 2.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-up')
        self.enemyFdPos += 1.1
        self.enemyFaceupNodes.append(cardModel)

    def makePlayerFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        self.playerFaceNode = cardModel

    def makeEnemyFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setTag('zone', 'face')
        self.enemyFaceNode = cardModel

    def testEvent(self, event):
        print event

    def getCard(self, obj):
        if obj.getTag('zone') == 'hand':
            return obj.getTag('card')

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
                ServerNetworkManager.Opcodes.playCard,
                self.playerHandNodes.index(handCard)
            )
        self.makeHand()
        self.makeBoard()

    def revealFacedown(self, card):
        if card not in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.revealFacedown,
            index
        )
        self.makeHand()
        self.makeBoard()

    def attack(self, card, target):
        index = self.playerFaceupNodes.index(card)
        targetIndex = 0
        zone = 0
        if target.getTag('zone') == 'face':
            if target == self.playerFaceNode:
                print "Can't attack yourself."
                return
            zone = Zone.face
        elif target.getTag('zone') == 'face-down':
            if target in self.playerFacedownNodes:
                print "Can't attack your own facedowns."
                return
            targetIndex = self.enemyFacedownNodes.index(target)
            zone = Zone.facedown
        else:
            if target in self.playerFaceupNodes:
                print "Can't attack your own faceups."
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

        self.makeHand()
        self.makeBoard()
        self.makeEnemyBoard()

    def endPhase(self):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.endPhase
        )

    def redraw(self):
        self.makeHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()
        self.endPhaseLabel.text = str(self.phase)
        self.playerManaCapLabel.text = str(self.player.manaCap)
        self.enemyManaCapLabel.text = str(self.enemy.manaCap)

    def mouseOverTask(self, name):
        if self.mouseWatcherNode.hasMouse():
            pickedObj = self.mouseHandler.getObjectClickedOn()
            if pickedObj and pickedObj.getTag('zone') == 'hand':
                card = self.player.hand[self.playerHandNodes.index(pickedObj)]
                label = "%d %d" % (card.getCost(), card.getRank())
                self.cardStatsLabel.text = label

        return Task.cont

    lastTime = 0.0

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        if task.time - self.lastTime > 1.0:
            self.networkManager.sendUnrecievedPackets()
            self.lastTime = task.time
        return Task.cont

app = App()
app.camera.setPos(4, -20, 1.2)
app.run()
