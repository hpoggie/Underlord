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

from direct.task import Task

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

        self.activeCard = None
        self.targeting = False

    def getObjectClickedOn (self):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()
            self.pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())

            base.cTrav.traverse(render)
            if (base.handler.getNumEntries() > 0):
                base.handler.sortEntries()
                pickedObj = base.handler.getEntry(0).getIntoNodePath()
                pickedObj = pickedObj.findNetTag('zone')
                return pickedObj

    def doClick (self):
        pickedObj = self.getObjectClickedOn()

        if self.targeting:
            if pickedObj != None:
                base.acceptTarget(pickedObj)
                self.targeting = False
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
                        print "p. mc %d" %base.getLocalPlayer().getManaCap()
                    elif pickedObj == base.enemyFaceNode:
                        print "e. mc %d" %base.getEnemyPlayer().getManaCap()
        else:
            self.activeCard = None

    def onMouse1 (self):
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
    port = 18861

    connection = rpyc.connect(serverIp, port)
    server = connection.root
    playerKey = raw_input()
    server.registerPlayer(playerKey)

    def __init__ (self):
        ShowBase.__init__(self)
        self.scene = self.loader.loadModel("empty.obj")
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.playerIconPath = self.getLocalPlayer().getIconPath()
        self.enemyIconPath = self.getEnemyPlayer().getIconPath()

        self.endPhaseButton = DirectButton(
                image="./concentric-crescents.png",
                pos=(0, 0, -0.5),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=self.endPhase
                )
        self.endPhaseLabel = OnscreenText(
                text=self.server.getPhase(),
                pos=(0, -0.7, 0),
                scale=(0.1, 0.1, 0.1)
                )

        self.cardStatsLabel = OnscreenText(
                text="",
                pos=(-0.7, -0.7, 0),
                scale=(0.1, 0.1, 0.1)
                )
        self.taskMgr.add(self.mouseOverTask, "MouseOverTask")

        print self.getLocalPlayer().getHandSize()
        self.makeHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

        self.servingThread = rpyc.BgServingThread(self.connection)
        self.server.setRedrawCallback(self.redraw)
        self.server.addTargetCallback(self.playerKey, self.getTarget)

    def getTarget (self):
        self.mouseHandler.targeting = True

    def acceptTarget (self, target):
        if target.getTag('zone') == 'face-down':
            index = self.enemyFacedownNodes.index(target)
        else:
            index = -1

        self.server.getLocalPlayer(self.playerKey).acceptTarget(index)

    def getLocalPlayer (self):
        return self.server.getLocalPlayer(self.playerKey)

    def getEnemyPlayer (self):
        return self.server.getEnemyPlayer(self.playerKey)

    def makeHand (self):
        for i in self.playerHandNodes:
            i.detachNode()
            self.handPos = 0.0
        self.playerHandNodes = []
        for i in range(0, self.getLocalPlayer().getHandSize()):
            self.addHandCard(self.getLocalPlayer().getHand(i))

    def makeEnemyHand (self):
        for i in self.enemyHandNodes:
            i.detachNode()
            self.enemyHandPos = 0.0
        self.enemyHandNodes = []
        for i in range(0, self.getEnemyPlayer().getHandSize()):
            self.addEnemyHandCard()

    def makeBoard (self):
        for i in self.playerFacedownNodes:
            i.detachNode()
        self.playerFacedownNodes = []
        for i in self.playerFaceupNodes:
            i.detachNode()
        self.playerFaceupNodes = []
        self.fdPos = 0.0
        for i in self.getLocalPlayer().getFaceups():
            self.addFaceupCard(i)
        for i in self.getLocalPlayer().getFacedowns():
            self.addFdCard(i)

    def makeEnemyBoard (self):
        for i in self.enemyFacedownNodes:
            i.detachNode()
        self.enemyFacedownNodes = []
        for i in self.enemyFaceupNodes:
            i.detachNode()
        self.enemyFaceupNodes = []
        self.enemyFdPos = 0.0
        for i in self.getEnemyPlayer().getFaceups():
            self.addEnemyFaceupCard(i)
        for i in self.getEnemyPlayer().getFacedowns():
            self.addEnemyFdCard(i)

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
        path = self.enemyIconPath + "/" + self.getEnemyPlayer().getCardBack()
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
        path = self.playerIconPath + "/" + self.getLocalPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.fdPos, 0, 1.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-down')
        self.fdPos += 1.1
        self.playerFacedownNodes.append(cardModel)

    def addEnemyFdCard (self, card):
        cm = CardMaker('face-down card')
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.getEnemyPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyFdPos, 0, 2.1)
        cardModel.setTag('card', card.getName())
        cardModel.setTag('zone', 'face-down')
        self.enemyFdPos += 1.1
        self.enemyFacedownNodes.append(cardModel)

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

    def addEnemyFaceupCard (self, card):
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

    def makePlayerFace (self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.getLocalPlayer().getCardBack()
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        self.playerFaceNode = cardModel

    def makeEnemyFace (self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.getEnemyPlayer().getCardBack()
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
        if self.server.getPhase() == "Reveal":
            self.getLocalPlayer().playFaceup(self.playerHandNodes.index(handCard))
        else:
            self.getLocalPlayer().play(self.playerHandNodes.index(handCard))
        self.makeHand()
        self.makeBoard()

    def revealFacedown (self, card):
        if not card in self.playerFacedownNodes:
            raise IllegalMoveError("That card is not one of your facedowns.")
        index = self.playerFacedownNodes.index(card)
        self.getLocalPlayer().revealFacedown(index)
        self.makeHand()
        self.makeBoard()

    def attack (self, card, target):
        index = self.playerFaceupNodes.index(card)
        targetIndex = 0
        if target.getTag('zone') == 'face':
            if target == self.playerFaceNode:
                print "Can't attack yourself."
                return
        elif target.getTag('zone') == 'face-down':
            if target in self.playerFacedownNodes:
                print "Can't attack your own facedowns."
                return
            targetIndex = self.enemyFacedownNodes.index(target)
        else:
            if target in self.playerFaceupNodes:
                print "Can't attack your own faceups."
                return
            targetIndex = self.enemyFaceupNodes.index(target)

        self.server.attack(index, targetIndex, target.getTag('zone'), self.playerKey)

        self.makeHand()
        self.makeBoard()
        self.makeEnemyBoard()

    def endPhase (self):
        try:
            self.server.endPhase(base.playerKey)
        except Exception as e:
            print e

    def endTurn ():
        self.server.endTurn()
        self.makeHand()
        self.makeBoard()

    def redraw (self):
        self.makeHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()
        self.endPhaseLabel.text = base.server.getPhase()

    def mouseOverTask (self, name):
        if self.mouseWatcherNode.hasMouse():
            pickedObj = self.mouseHandler.getObjectClickedOn()
            if pickedObj and pickedObj.getTag('zone') == 'hand':
                card = self.getLocalPlayer().getHand(self.playerHandNodes.index(pickedObj))
                self.cardStatsLabel.text = "%d %d" % (card.getCost(), card.getRank())

        return Task.cont

app = App()

def logCameraTask (name):
    print base.camera.getPos()
    return Task.cont

#app.taskMgr.add(logCameraTask, "LogCameraTask")

app.camera.setPos(4, -20, 1.2)

app.run()
