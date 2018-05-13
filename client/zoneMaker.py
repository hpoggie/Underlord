import textwrap

import panda3d.core
from panda3d.core import CardMaker
from direct.showbase.DirectObject import DirectObject

from .fanHand import fanHand


def hideCard(card):
    for ch in card.children:
        if ch.name != 'frame':
            ch.hide()


def showCard(card):
    for ch in card.children:
        if ch.name != 'frame':
            ch.show()


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
            cardModel.setPythonTag('zone', base.player.hand)
            base.playerHandNodes.append(cardModel)
            pivot.reparentTo(self.playerHand)

        fan = fanHand(len(base.player.hand))
        for i, tr in enumerate(fan):
            addHandCard(base.player.hand[i], tr)
            if base.player.hand[i] in base.toMulligan:
                tex = loader.loadTexture(base.playerIconPath + '/' + base.playerCardBack)
                hideCard(base.playerHandNodes[i])
            else:
                showCard(base.playerHandNodes[i])

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
            cardModel.setPythonTag('zone', base.enemy.hand)
            base.enemyHandNodes.append(cardModel)
            pivot.reparentTo(self.enemyHand)

        fan = fanHand(len(base.enemy.hand))
        for tr in fan:
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
            cardModel.setPythonTag('zone', base.player.faceups)
            base.playerFaceupNodes.append(cardModel)

        def addFdCard(card):
            cardModel = self.loadCard(card)
            hideCard(cardModel)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setPythonTag('zone', base.player.facedowns)
            # Give this a card ref so we can see it
            cardModel.setPythonTag('card', card)
            base.playerFacedownNodes.append(cardModel)

        for c in base.player.faceups:
            addFaceupCard(c)
            posX += 1.1
        for c in base.player.facedowns:
            addFdCard(c)
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

        def addEnemyFdCard(card):
            if card is None:
                cardModel = self.loadEnemyBlank()
            else:
                cardModel = self.loadCard(card)
                hideCard(cardModel)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setPythonTag('zone', base.enemy.facedowns)
            # Give this a card ref so we can see it
            cardModel.setPythonTag('card', card)
            base.enemyFacedownNodes.append(cardModel)

        def addEnemyFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.setPos(posX, 0, posZ)
            cardModel.setPythonTag('zone', base.enemy.faceups)
            base.enemyFaceupNodes.append(cardModel)

        for c in base.enemy.faceups:
            addEnemyFaceupCard(c)
            posX += 1.1
        for c in base.enemy.facedowns:
            addEnemyFdCard(c)
            posX += 1.1

    def loadCard(self, card):
        cardBase = self.scene.attachNewNode(card.name)

        cm = CardMaker(card.name)

        cardFrame = cardBase.attachNewNode(cm.generate())
        tex = loader.loadTexture('ul_frame_alt.png')
        cardFrame.setTexture(tex)
        cardFrame.setScale(1, 1, 509 / 364)
        cardFrame.setTransparency(True)
        cardFrame.setName('frame')

        cardImage = cardBase.attachNewNode(cm.generate())
        if card.owner == base.player:
            path = base.playerIconPath + "/" + card.image
        else:
            path = base.enemyIconPath + "/" + card.image
        tex = loader.loadTexture(path)
        cardImage.setTexture(tex)
        cardImage.setScale(0.8)
        cardImage.setPos(0.1, -0.05, 0.5)
        cardImage.setName('image')

        cost = panda3d.core.TextNode('cost')
        cost.setText(str(card.cost))
        textNodePath = cardBase.attachNewNode(cost)
        textNodePath.setScale(0.1)
        textNodePath.setPos(0.08, -0.05, 1.275)

        rank = panda3d.core.TextNode('rank')
        rank.setText(str(card.rank))
        textNodePath = cardBase.attachNewNode(rank)
        textNodePath.setScale(0.1)
        textNodePath.setPos(0.08, -0.05, 1.125)

        desc = panda3d.core.TextNode('desc')
        desc.setText(textwrap.fill(card.desc, width=40))
        textNodePath = cardBase.attachNewNode(desc)
        textNodePath.setScale(0.045)
        textNodePath.setPos(0.09, -0.05, 0.4)

        cardBase.setPythonTag('card', card)

        return cardBase

    def loadBlank(self, path):
        cardBase = self.scene.attachNewNode('mysterious card')

        cm = CardMaker('mysterious card')

        cardFrame = cardBase.attachNewNode(cm.generate())
        tex = loader.loadTexture('ul_frame_alt.png')
        cardFrame.setTexture(tex)
        cardFrame.setScale(1, 1, 509 / 364)
        cardFrame.setTransparency(True)
        cardFrame.setName('frame')
        return cardBase

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
        cardModel.setPythonTag('zone', base.player.face)
        base.playerFaceNode = cardModel

    def makeEnemyFace(self):
        cm = CardMaker("face")
        cardModel = self.scene.attachNewNode(cm.generate())
        path = base.enemyIconPath + "/" + base.enemyCardBack
        tex = loader.loadTexture(path)
        cardModel.setTexture(tex)
        cardModel.setPos(0, 0, 5)
        cardModel.setPythonTag('zone', base.enemy.face)
        base.enemyFaceNode = cardModel

    def redrawAll(self):
        self.makePlayerHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()

    def unmake(self):
        self.scene.detachNode()
