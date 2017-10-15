"""
This is the client script. It takes game data and draws it on the screen.
It also takes user input and turns it into game actions.
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from panda3d.core import CardMaker
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import CollisionNode, GeomNode, CollisionRay, TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText

from network import ClientNetworkManager, ServerNetworkManager
from core.enums import Phase, Zone

from panda3d.core import loadPrcFileData
from direct.task import Task
from factions import templars

import sys

loadPrcFileData(
    "",
    """
    win-size 500 500
    window-title Overlord
    fullscreen 0
    """)


class IllegalMoveError (Exception):
    pass


class MouseHandler (DirectObject):
    def __init__(self):
        self.accept('mouse1', self.onMouse1, [])

        self.showCollisions = False

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
        self.targeting = False

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

        if self.targeting:
            if pickedObj is not None:
                base.acceptTarget(pickedObj)
                self.targeting = False
            return

        if pickedObj and not pickedObj.isEmpty():
            if pickedObj.getTag('zone') == 'hand':
                try:
                    base.playCard(pickedObj)
                except IllegalMoveError as error:
                    print(error)
            elif pickedObj.getTag('zone') == 'face-down':
                if not self.activeCard:
                    try:
                        base.revealFacedown(pickedObj)
                    except IllegalMoveError as error:
                        print(error)
            elif pickedObj.getTag('zone') == 'enemy face-down':
                if self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face-up':
                if not self.activeCard:
                    self.activeCard = pickedObj
                else:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face' and self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
        else:
            self.activeCard = None

    def onMouse1(self):
        self.doClick()


class App (ShowBase):
    def __init__(self, argv):
        ShowBase.__init__(self)

        self.port = 9099

        self.scene = self.loadModel("empty")
        self.scene.reparentTo(self.render)

        base.cTrav = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.mouseHandler = MouseHandler()

        self.endPhaseLabel = OnscreenText(
            text="faction select",
            pos=(0, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.descLabel = OnscreenText(
            text="",
            pos=(-0.9, -0.8, 0),
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.taskMgr.add(self.mouseOverTask, "MouseOverTask")

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

        self.serverIp = argv[1] if len(argv) > 1 else "174.138.119.84"
        self.networkManager = ClientNetworkManager(self, self.serverIp)
        self.serverAddr = (self.serverIp, self.port)
        self.taskMgr.add(self.networkUpdateTask, "NetworkUpdateTask")
        self.networkManager.connect(self.serverAddr)
        self.networkManager.send("0", self.serverAddr)

        self._active = False
        self._started = False

    def loadModel(self, name):
        try:
            ret = self.loader.loadModel(name + ".bam")
        except IOError:
            ret = self.loader.loadModel(name + ".egg")

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

    def pickFaction(self, index):
        self.networkManager.sendInts(
            self.serverAddr,
            ServerNetworkManager.Opcodes.selectFaction,
            index)

        self.faction = self.availableFactions[index]

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
        self.cardStatsLabel = OnscreenText(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.endPhaseButton = DirectButton(
            image="./end_phase.png",
            pos=(0, 0, -0.5),
            scale=(0.1, 0.1, 0.1),
            relief=None,
            command=self.endPhase)

        self.handPos = 0.0
        self.enemyHandPos = 0.0
        self.playerFacePos = (0, 0, 1)
        self.enemyFacePos = (0, 0, -1)
        self.playerHandNodes = []
        self.enemyHandNodes = []
        self.fdPos = 0.0
        self.enemyFdPos = 0.0
        self.playerFacedownNodes = []
        self.enemyFacedownNodes = []
        self.playerFaceupNodes = []
        self.enemyFaceupNodes = []

        self.makeHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

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
                targetsEnemy = False
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

    def makeHand(self):
        for i in self.playerHandNodes:
            i.detachNode()
        self.handPosX = 0.0
        self.handPosY = 0.0
        self.handRot = -45.0
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
        cm = CardMaker(card.name)
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.handPosX, 0, self.handPosY)
        cardModel.setHpr(0, 0, self.handRot)
        cardModel.setTag('card', card.name)
        cardModel.setTag('zone', 'hand')
        self.handPosX += 0.75
        self.handPosY += 0.1
        self.handRot += 90. / len(self.player.hand) - 1
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
        cardModel.setTag('card', card.name)
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
        cardModel.setTag('zone', 'enemy face-down')
        self.enemyFdPos += 1.1
        self.enemyFacedownNodes.append(cardModel)

    def addFaceupCard(self, card):
        cm = CardMaker(card.name)
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.fdPos, 0, 1.1)
        cardModel.setTag('card', card.name)
        cardModel.setTag('zone', 'face-up')
        self.fdPos += 1.1
        self.playerFaceupNodes.append(cardModel)

    def addEnemyFaceupCard(self, card):
        cm = CardMaker(card.name)
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(self.enemyFdPos, 0, 2.1)
        cardModel.setTag('card', card.name)
        cardModel.setTag('zone', 'face-up')
        self.enemyFdPos += 1.1
        self.enemyFaceupNodes.append(cardModel)

    def makePlayerFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.playerIconPath + "/" + self.playerCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        self.playerFaceNode = cardModel

    def makeEnemyFace(self):
        cm = CardMaker("face")
        cardModel = self.render.attachNewNode(cm.generate())
        path = self.enemyIconPath + "/" + self.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setTag('zone', 'face')
        self.enemyFaceNode = cardModel

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
                ServerNetworkManager.Opcodes.play,
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
        self.endPhaseLabel.setText(str(Phase.keys[self.phase]))
        self.turnLabel.setText("Your Turn" if self.active else "Enemy Turn")
        if self.phase == Phase.reveal:
            self.playerManaCapLabel.setText(
                str(self.player.manaCap) + " (" + str(self.player.mana) + ")")
        else:
            self.playerManaCapLabel.setText(str(self.player.manaCap))
        self.enemyManaCapLabel.setText(str(self.enemy.manaCap))

    def mouseOverTask(self, name):
        if self.mouseWatcherNode.hasMouse():
            if hasattr(self, 'cardStatsLabel'):
                self.cardStatsLabel.setText("")

            if hasattr(self, 'descLabel'):
                self.descLabel.setText("")

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = self.playerIconPath + "/" + self.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            pickedObj = self.mouseHandler.getObjectClickedOn()
            if pickedObj:
                if pickedObj.getTag('zone') == 'hand':
                    card = self.player.hand[
                        self.playerHandNodes.index(pickedObj)]
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.descLabel.setText(
                        ("Instant. " if card.playsFaceUp else "") + card.desc)
                elif pickedObj.getTag('zone') == 'face-down':
                    card = self.player.facedowns[
                        self.playerFacedownNodes.index(pickedObj)]
                    self._activeObj = pickedObj
                    path = self.playerIconPath + "/" + card.image
                    pickedObj.setTexture(loader.loadTexture(path))
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.descLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'enemy face-down':
                    card = self.enemy.facedowns[
                        self.enemyFacedownNodes.index(pickedObj)]
                    if card is not None:
                        self._activeObj = pickedObj
                        path = self.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        label = str(card.cost) + " " + str(card.rank)
                        self.cardStatsLabel.setText(label)
                        self.descLabel.setText(card.desc)
                elif pickedObj.getTag('zone') == 'face-up':
                    if pickedObj in self.playerFaceupNodes:
                        card = self.player.faceups[
                            self.playerFaceupNodes.index(pickedObj)]
                    else:
                        card = self.enemy.faceups[
                            self.enemyFaceupNodes.index(pickedObj)]
                    label = str(card.cost) + " " + str(card.rank)
                    self.cardStatsLabel.setText(label)
                    self.descLabel.setText(card.desc)

        return Task.cont

    lastTime = 0.0

    def networkUpdateTask(self, task):
        self.networkManager.recv()
        return Task.cont


app = App(sys.argv)
app.camera.setPos(4, -20, 1.2)
app.run()
