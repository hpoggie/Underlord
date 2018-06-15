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

        base.playerIconPath = base.player.iconPath
        base.enemyIconPath = base.enemy.iconPath
        base.playerCardBack = base.player.cardBack
        base.enemyCardBack = base.enemy.cardBack

        for name in ['playerHand', 'enemyHand', 'playerBoard', 'enemyBoard']:
            setattr(self, name, self.scene.attachNewNode(name))

        self.playerBoard.setPos(0, 0, -2)
        self.enemyBoard.setPos(0, 0, 2.1)
        self.playerGraveyard = self.scene.attachNewNode('player graveyard')
        self.playerGraveyard.setPos(0, 0, -6.5)
        self.enemyGraveyard = self.scene.attachNewNode('enemy graveyard')
        self.enemyGraveyard.setPos(0, 0, 6.5)

        self.makePlayerHand()
        self.makeEnemyHand()
        self.makeBoard()
        self.makeEnemyBoard()
        self.makePlayerFace()
        self.makeEnemyFace()

        # For showing a big version of a card on mouse over
        self.focusedCard = base.camera.attachNewNode('focused card')
        self.focusedCard.setPos(-0.5, 6, -0.3)

    def makePlayerHand(self):
        """
        Redraw the player's hand.
        """
        # Destroy entire hand. This is slow and may need to be changed
        for i in self.playerHand.children:
            i.removeNode()

        def addHandCard(card, tr):
            cardModel = self.loadCard(card)
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setPythonTag('zone', base.player.hand)
            pivot.reparentTo(self.playerHand)

        fan = fanHand(len(base.player.hand))
        for i, tr in enumerate(fan):
            addHandCard(base.player.hand[i], tr)
            if base.player.hand[i] in base.toMulligan:
                tex = loader.loadTexture(base.playerIconPath + '/' + base.playerCardBack)
                hideCard(self.playerHand.children[i].children[0])
            else:
                showCard(self.playerHand.children[i].children[0])

        if base.hasMulliganed:
            self.playerHand.reparentTo(self.scene)
            self.playerHand.setPosHpr(2.5, 0, -2, 0, 45.0, 0)
        else:
            self.playerHand.reparentTo(base.camera)
            self.playerHand.setPos(-1.5, 10, 1.5)

    def makeEnemyHand(self):
        for i in self.enemyHand.children:
            i.removeNode()

        def addEnemyHandCard(tr):
            cardModel = self.loadEnemyBlank()
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setPythonTag('zone', base.enemy.hand)
            pivot.reparentTo(self.enemyHand)

        fan = fanHand(len(base.enemy.hand))
        for tr in fan:
            addEnemyHandCard(tr)

        self.enemyHand.setPosHpr(2.5, -1.0, 7.1, 0, 45.0, 0)

    def makeBoard(self):
        """
        Show the player's faceups and facedowns
        """
        for i in self.playerBoard.children:
            i.removeNode()

        posX = 0.0

        def addFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.reparentTo(self.playerBoard)
            cardModel.setPos(posX, 0, 0)
            cardModel.setPythonTag('zone', base.player.faceups)

        def addFdCard(card):
            cardModel = self.loadCard(card)
            hideCard(cardModel)
            cardModel.reparentTo(self.playerBoard)
            cardModel.setPos(posX, 0, 0)
            cardModel.setPythonTag('zone', base.player.facedowns)
            # Give this a card ref so we can see it
            cardModel.setPythonTag('card', card)

        for c in base.player.faceups:
            addFaceupCard(c)
            posX += 1.1
        for c in base.player.facedowns:
            addFdCard(c)
            posX += 1.1

    def makeEnemyBoard(self):
        for i in self.enemyBoard.children:
            i.removeNode()

        posX = 0.0

        def addEnemyFdCard(card):
            if card.visibleWhileFacedown:
                cardModel = self.loadCard(card)
                hideCard(cardModel)
            else:
                cardModel = self.loadEnemyBlank()
            cardModel.reparentTo(self.enemyBoard)
            cardModel.setPos(posX, 0, 0)
            cardModel.setPythonTag('zone', base.enemy.facedowns)
            # Give this a card ref so we can see it
            cardModel.setPythonTag('card', card)

        def addEnemyFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.reparentTo(self.enemyBoard)
            cardModel.setPos(posX, 0, 0)
            cardModel.setPythonTag('zone', base.enemy.faceups)

        for c in base.enemy.faceups:
            addEnemyFaceupCard(c)
            posX += 1.1
        for c in base.enemy.facedowns:
            addEnemyFdCard(c)
            posX += 1.1

    def makePlayerGraveyard(self):
        # Show only the top card for now
        if len(base.player.graveyard) > 0:
            for i in self.playerGraveyard.children:
                i.removeNode()
            c = self.loadCard(base.player.graveyard[-1])
            c.reparentTo(self.playerGraveyard)
            c.setPythonTag('zone', base.player.graveyard)

    def makeEnemyGraveyard(self):
        if len(base.enemy.graveyard) > 0:
            for i in self.enemyGraveyard.children:
                i.removeNode()
            c = self.loadCard(base.enemy.graveyard[-1])
            c.reparentTo(self.enemyGraveyard)
            c.setPythonTag('zone', base.enemy.graveyard)

    def focusCard(self, card):
        """
        Draws a big version of the card so the player can read the text
        easily.
        """
        # If the node path is pointing to the right card, don't rebuild
        if card != self.focusedCard:
            self.focusedCard.unstash()
            if len(self.focusedCard.children) > 0:
                self.focusedCard.children[0].removeNode()
            # Make a duplicate of the node. Actually a different node path
            # pointing to the same node
            card.copyTo(self.focusedCard)
            self.focusedCard.children[0].setPos(0, 0, 0)
            # Don't try to play this
            self.focusedCard.setPythonTag('card', None)

    def unfocusCard(self):
        # Stash the enlarged card image so it won't collide or be visible.
        # This is different from using hide() because it also prevents
        # collision.
        self.focusedCard.stash()

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
        tex = loader.loadTexture(card.imagePath)
        cardImage.setTexture(tex)
        cardImage.setScale(0.7)
        cardImage.setPos(0.15, -0.05, 0.5)
        cardImage.setName('image')

        name = panda3d.core.TextNode('name')
        name.setAlign(panda3d.core.TextNode.ARight)
        name.setText(card.name)
        textNodePath = cardBase.attachNewNode(name)
        textNodePath.setScale(0.08)
        textNodePath.setPos(0.92, -0.05, 1.275)

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
        desc.setText(textwrap.fill(card.desc, width=25))
        textNodePath = cardBase.attachNewNode(desc)
        textNodePath.setScale(0.07)
        textNodePath.setPos(0.09, -0.05, 0.4)

        if hasattr(card, 'counter'):
            counter = panda3d.core.TextNode('counter')
            counter.setText(str(card.counter))
            textNodePath = cardBase.attachNewNode(counter)
            textNodePath.setScale(0.4)
            textNodePath.setPos(0.7, -0.05, 0.1)

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
        cardModel.setPos(0, 0, -5)
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
        self.makePlayerGraveyard()
        self.makeEnemyGraveyard()

    def unmake(self):
        self.playerHand.removeNode()  # In case it's parented to the camera
        self.scene.removeNode()
