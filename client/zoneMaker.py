from panda3d.core import CardMaker
from direct.showbase.DirectObject import DirectObject

from .fanHand import fanHand


class ZoneMaker(DirectObject):
    def __init__(self):
        # Set up the root node
        self.scene = base.render.attachNewNode('empty')

        base.playerIconPath = base.faction.iconPath
        base.enemyIconPath = base.enemyFaction.iconPath
        base.playerCardBack = base.faction.cardBack
        base.enemyCardBack = base.enemyFaction.cardBack

        base.playerHandNodes = []
        base.enemyHandNodes = []
        base.playerFacedownNodes = []
        base.enemyFacedownNodes = []
        base.playerFaceupNodes = []
        base.enemyFaceupNodes = []

        self.makePlayerHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

    def makePlayerHand(self):
        """
        Redraw the player's hand.
        """
        # Destroy entire hand. This is slow and may need to be changed
        for i in base.playerHandNodes:
            i.detachNode()

        base.playerHandNodes = []

        if not hasattr(self, 'playerHand'):
            self.playerHand = self.scene.attachNewNode('playerHand')

        def addHandCard(card, tr):
            cardModel = self.loadCard(card)
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setTag('zone', 'hand')
            base.playerHandNodes.append(cardModel)
            pivot.reparentTo(self.playerHand)

        fan = fanHand(len(base.player.hand))
        for i, tr in enumerate(fan):
            addHandCard(base.player.hand[i], tr)

        self.playerHand.setPosHpr(2.5, -1.0, 0, 0, 45.0, 0)

    def makeEnemyHand(self):
        for i in base.enemyHandNodes:
            i.detachNode()

        base.enemyHandNodes = []

        if not hasattr(self, 'enemyHand'):
            self.enemyHand = self.scene.attachNewNode('enemyHand')

        def addEnemyHandCard(tr):
            cardModel = self.loadEnemyBlank()
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setTag('zone', 'enemy hand')
            base.enemyHandNodes.append(cardModel)
            pivot.reparentTo(self.enemyHand)

        fan = fanHand(len(base.enemy.hand))
        for i, tr in enumerate(fan):
            addEnemyHandCard(tr)

        self.enemyHand.setPosHpr(2.5, -1.0, 7.1, 0, 45.0, 0)

    def makeBoard(self):
        """
        Show the player's faceups and facedowns
        """
        for i in base.playerFacedownNodes:
            i.detachNode()
        base.playerFacedownNodes = []
        for i in base.playerFaceupNodes:
            i.detachNode()
        base.playerFaceupNodes = []

        posX = 0.0
        posZ = 0.55

        def addFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-up')
            base.playerFaceupNodes.append(cardModel)

        def addFdCard(card):
            cardModel = self.loadPlayerBlank()
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-down')
            base.playerFacedownNodes.append(cardModel)

        for i in base.player.faceups:
            addFaceupCard(i)
            posX += 1.1
        for i in base.player.facedowns:
            addFdCard(i)
            posX += 1.1

    def makeEnemyBoard(self):
        for i in base.enemyFacedownNodes:
            i.detachNode()
        base.enemyFacedownNodes = []
        for i in base.enemyFaceupNodes:
            i.detachNode()
        base.enemyFaceupNodes = []

        posX = 0.0
        posZ = 2.1

        def addEnemyFdCard():
            cardModel = self.loadEnemyBlank()
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'enemy face-down')
            base.enemyFacedownNodes.append(cardModel)

        def addEnemyFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setTag('zone', 'face-up')
            base.enemyFaceupNodes.append(cardModel)

        for i in base.enemy.faceups:
            addEnemyFaceupCard(i)
            posX += 1.1
        for i in range(0, len(base.enemy.facedowns)):
            addEnemyFdCard()
            posX += 1.1

    def loadCard(self, card):
        cm = CardMaker(card.name)
        cardModel = self.scene.attachNewNode(cm.generate())
        if card.owner == base.player:
            path = base.playerIconPath + "/" + card.image
        else:
            path = base.enemyIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        return cardModel

    def loadBlank(self, path):
        cm = CardMaker('mysterious card')
        cardModel = self.scene.attachNewNode(cm.generate())
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        return cardModel

    def loadPlayerBlank(self):
        path = base.playerIconPath + "/" + base.playerCardBack
        return self.loadBlank(path)

    def loadEnemyBlank(self):
        path = base.enemyIconPath + "/" + base.enemyCardBack
        return self.loadBlank(path)

    def makePlayerFace(self):
        cm = CardMaker("face")
        cardModel = self.scene.attachNewNode(cm.generate())
        path = base.playerIconPath + "/" + base.playerCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, -1.5)
        cardModel.setTag('zone', 'face')
        base.playerFaceNode = cardModel

    def makeEnemyFace(self):
        cm = CardMaker("face")
        cardModel = self.scene.attachNewNode(cm.generate())
        path = base.enemyIconPath + "/" + base.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setTag('zone', 'face')
        base.enemyFaceNode = cardModel

    def redrawAll(self):
        self.makePlayerHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()

    def unmake(self):
        self.scene.detachNode()
