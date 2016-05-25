import rpyc
from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import CollisionNode, GeomNode, CollisionRay
from direct.gui.DirectGui import *
from direct.gui.OnscreenText import OnscreenText

from OverlordServer import IllegalMoveError

from panda3d.core import loadPrcFileData
f = open("overlordrc")
loadPrcFileData("", f.read())
f.close()

class MouseHandler (DirectObject):
    def __init__ (self):
        self.accept('mouse1', self.onMouse1, [])

        pickerNode = CollisionNode('mouseRay')
        pickerNP = camera.attachNewNode(pickerNode)
        pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)
        base.cTrav.addCollider(pickerNP, base.handler)
        #base.cTrav.showCollisions(render)
        base.disableMouse()

    def getObjectClickedOn (self):
        if base.mouseWatcherNode.hasMouse:
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            base.cTrav.traverse(render)
            if (base.handler.getNumEntries() > 0):
                base.handler.sortEntries()
                pickedObj = base.handler.getEntry(0).getIntoNodePath()
                pickedObj = pickedObj.findNetTag('zone')
                if not pickedObj.isEmpty():
                    if pickedObj.getTag('zone') == 'hand':
                        try:
                            base.playCard(pickedObj)
                        except IllegalMoveError as error:
                            print error
                    elif pickedObj.getTag('zone') == 'face-down':
                        try:
                            base.revealFacedown(pickedObj)
                        except IllegalMoveError as error:
                            print error

    def onMouse1 (self):
        self.getObjectClickedOn()

class App (ShowBase):
    handPos = 0.0
    enemyHandPos = 0.0
    playerFacePos = (0, 0, 1)
    enemyFacePos = (0, 0, -1)

    playerHandNodes = []
    enemyHandNodes = []
    fdPos = 0.0
    playerFacedownNodes = []
    playerFaceupNodes = []

    serverIp = "localhost"
    port = 18861

    connection = rpyc.connect(serverIp, port)
    server = connection.root

    def __init__ (self):
        ShowBase.__init__(self)
        self.scene = self.loader.loadModel("empty.obj")
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()

        self.playerIconPath = self.server.getLocalPlayer().getIconPath()
        self.enemyIconPath = self.server.getEnemyPlayer().getIconPath()

        self.endPhaseButton = DirectButton(
                image="./concentric-crescents.png",
                pos=(0, 0, -0.5),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=endPhase
                )
        self.endPhaseLabel = OnscreenText(
                text=self.server.getPhase(),
                pos=(0, -0.7, 0),
                scale=(0.1, 0.1, 0.1)
                )

        print self.server.getLocalPlayer().getHandSize()
        self.makeHand()
        self.makeEnemyHand()
        self.makePlayerFace()
        self.makeEnemyFace()

    def makeHand (self):
        for i in self.playerHandNodes:
            i.detachNode()
            self.handPos = 0.0
        self.playerHandNodes = []
        for i in range(0, self.server.getLocalPlayer().getHandSize()):
            self.addHandCard(self.server.getLocalPlayer().getHand(i))

    def makeEnemyHand (self):
        for i in self.enemyHandNodes:
            i.detachNode()
            self.enemyHandPos = 0.0
        self.enemyHandNodes = []
        for i in range(0, self.server.getEnemyPlayer().getHandSize()):
            self.addEnemyHandCard()

    def makeBoard (self):
        for i in self.playerFacedownNodes:
            i.detachNode()
        self.playerFacedownNodes = []
        for i in self.playerFaceupNodes:
            i.detachNode()
        self.playerFaceupNodes = []
        self.fdPos = 0.0
        for i in self.server.getLocalPlayer().getFaceups():
            self.addFaceupCard(i)
        for i in self.server.getLocalPlayer().getFacedowns():
            self.addFdCard(i)

    def addHandCard (self, card):
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

    def addEnemyHandCard (self):
        cm = CardMaker('enemy hand card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.server.getEnemyPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyHandPos, 0, 3.1)
        cardModel.setTag('card', 'enemy hand card')
        cardModel.setTag('zone', 'enemy hand')
        self.enemyHandPos += 1.1
        self.enemyHandNodes.append(cardModel)

    def addFdCard (self, card):
        cm = CardMaker('face-down card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.server.getLocalPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.fdPos, 0, 1.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-down')
        self.fdPos += 1.1
        self.playerFacedownNodes.append(cardModel)

    def addFaceupCard (self, card):
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

    def makePlayerFace (self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.server.getLocalPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        self.playerFaceNode = cardModel

    def makeEnemyFace (self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.server.getEnemyPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setTag('zone', 'face')
        self.enemyFaceNode = cardModel

    def testEvent (self, event):
        print event

    def getCard (self, obj):
        if obj.getTag('zone') == 'hand':
            return obj.getTag('card')

    def playCard (self, handCard):
        self.server.getLocalPlayer().play(self.playerHandNodes.index(handCard))
        self.makeHand()
        self.makeBoard()

    def revealFacedown (self, card):
        index = self.playerFacedownNodes.index(card)
        self.server.getLocalPlayer().revealFacedown(index)
        self.makeHand()
        self.makeBoard()

def endPhase ():
    base.server.endPhase()
    base.makeHand()
    base.makeBoard()
    base.endPhaseLabel.text = base.server.getPhase()

def endTurn ():
    base.server.endTurn()
    base.makeHand()
    base.makeBoard()

app = App()
handler = MouseHandler()

from direct.task import Task

def logCameraTask (name):
    print base.camera.getPos()
    return Task.cont

#app.taskMgr.add(logCameraTask, "LogCameraTask")

app.camera.setPos(4, -20, 1.2)

app.run()
