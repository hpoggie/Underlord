import textwrap

import panda3d.core
from panda3d.core import CardMaker, BitMask32
from direct.showbase.DirectObject import DirectObject

from .fanHand import fanHand
from . import animations

def hideCard(card):
    for ch in card.children:
        if ch.name != 'frame':
            ch.hide()


def showCard(card):
    for ch in card.children:
        if ch.name != 'frame':
            ch.show()


def cleanup(parent):
    for i in parent.children:
        c = i.getPythonTag('card')
        if c is None or c.cardId == -1:
            i.removeNode()


def updateCardNode(card):
    card.costNode.setText(str(card.cost))
    card.rankNode.setText(str(card.rank))
    if hasattr(card, 'counter'):
        card.counterNode.setText(str(card.counter))


class ZoneMaker(DirectObject):
    def __init__(self):
        # Set up the root node
        self.scene = base.render.attachNewNode('empty')

        base.playerIconPath = base.player.iconPath
        base.enemyIconPath = base.enemy.iconPath
        base.playerCardBack = base.player.cardBack
        base.enemyCardBack = base.enemy.cardBack

        for name in ['playerHand', 'mulliganHand', 'enemyHand',
                     'playerBoard', 'enemyBoard', 'orphan']:
            setattr(self, name, self.scene.attachNewNode(name))

        self.playerHand.reparentTo(self.scene)
        self.playerHand.setPosHpr(2.5, 0, -2, 0, 45.0, 0)
        self.mulliganHand.reparentTo(base.camera)
        self.playerBoard.setPos(0, 0, -2)
        self.enemyBoard.setPos(0, 0, 2.1)
        self.playerGraveyard = self.scene.attachNewNode('player graveyard')
        self.playerGraveyard.setPos(0, 0, -6.5)
        self.enemyGraveyard = self.scene.attachNewNode('enemy graveyard')
        self.enemyGraveyard.setPos(0, 0, 6.5)

        self.makePlayerFace()
        self.makeEnemyFace()

        # For showing a big version of a card on mouse over
        self.focusedCard = base.camera.attachNewNode('focused card')
        self.focusedCard.setPos(-0.5, 6, -0.3)

        for c in base.player.referenceDeck + base.enemy.referenceDeck:
            c.pandaNode = None

    def addHandCard(self, card, tr, parent=None):
        if parent is None:
            parent = self.playerHand

        cardModel = self.loadCard(card)
        pivot = self.scene.attachNewNode('pivot')
        offset = cardModel.getScale() / 2
        pivot.setPosHpr(*tr)
        cardModel.reparentTo(pivot)
        cardModel.setPos(-offset)
        cardModel.setHpr(0, 0, 0)
        cardModel.setPythonTag('zone', base.player.hand)
        pivot.reparentTo(parent)

    def makeMulliganHand(self):
        """
        Draw the player's hand for mulligan
        """
        cleanup(self.mulliganHand)

        posX = 0
        for c in base.player.hand:
            self.addHandCard(c, (posX, 0, 0, 0, 0, 0), self.mulliganHand)
            if c in base.toMulligan:
                hideCard(c.pandaNode)
            else:
                showCard(c.pandaNode)

            posX += 1.1

        self.mulliganHand.setPosHpr(
            -1.1 * (len(base.player.hand) - 1) / 2, 12, 0, 0, 0, 0)

    def makePlayerHand(self):
        """
        Redraw the player's hand.
        """
        self.mulliganHand.removeNode()
        # Destroy entire hand. This is slow and may need to be changed
        # cleanup(self.playerHand)
        for pivot in self.playerHand.children:
            for c in pivot.children:
                c.wrtReparentTo(self.scene)
            pivot.removeNode()

        fan = fanHand(len(base.player.hand))
        for i, tr in enumerate(fan):
            self.addHandCard(base.player.hand[i], tr)

    def makeEnemyHand(self):
        cleanup(self.enemyHand)

        def addEnemyHandCard(card, tr):
            if card.visible:
                cardModel = self.loadCard(card)
            else:
                cardModel = self.loadEnemyBlank(card)
            pivot = self.scene.attachNewNode('pivot')
            offset = cardModel.getScale() / 2
            pivot.setPosHpr(*tr)
            cardModel.reparentTo(pivot)
            cardModel.setPos(-offset)
            cardModel.setPythonTag('zone', base.enemy.hand)
            pivot.reparentTo(self.enemyHand)

        fan = fanHand(len(base.enemy.hand))
        for i, tr in enumerate(fan):
            addEnemyHandCard(base.enemy.hand[i], tr)

        self.enemyHand.setPosHpr(2.5, -1.0, 7.1, 0, 45.0, 0)

    def makeBoard(self):
        """
        Show the player's faceups and facedowns
        """
        cleanup(self.playerBoard)

        posX = 0.0

        def addFaceupCard(card):
            cardModel = self.loadCard(card)
            cardModel.reparentTo(self.playerBoard)
            cardModel.setPosHpr(posX, 0, 0, 0, 0, 0)
            cardModel.setPythonTag('zone', base.player.faceups)

        def addFdCard(card):
            cardModel = self.loadCard(card)
            hideCard(cardModel)
            cardModel.reparentTo(self.playerBoard)
            cardModel.setPosHpr(posX, 0, 0, 0, 0, 0)
            cardModel.setPythonTag('zone', base.player.facedowns)

        for c in base.player.faceups:
            addFaceupCard(c)
            posX += 1.1
        for c in base.player.facedowns:
            addFdCard(c)
            posX += 1.1

    def makeEnemyBoard(self):
        cleanup(self.enemyBoard)
        for n in self.enemyBoard.children:
            n.reparentTo(self.orphan)

        posX = 0.0

        def addEnemyFdCard(card):
            if card.visible:
                cardModel = self.loadCard(card)
                hideCard(cardModel)
            else:
                cardModel = self.loadEnemyBlank(card)
            cardModel.reparentTo(self.enemyBoard)
            cardModel.setPos(posX, 0, 0)
            cardModel.setPythonTag('zone', base.enemy.facedowns)

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
            cleanup(self.playerGraveyard)
            c = self.loadCard(base.player.graveyard[-1])
            showCard(c)
            animations.animateMove(c, self.playerGraveyard, 0.3)
            c.setPythonTag('zone', base.player.graveyard)

            for c1 in base.player.graveyard[:-1]:
                if c1.pandaNode is not None:
                    c1.pandaNode.removeNode()
                c1.pandaNode = None

    def makeEnemyGraveyard(self):
        if len(base.enemy.graveyard) > 0:
            cleanup(self.enemyGraveyard)
            c = self.loadCard(base.enemy.graveyard[-1])
            showCard(c)
            animations.animateMove(c, self.enemyGraveyard, 0.3)
            c.setPythonTag('zone', base.enemy.graveyard)

            for c1 in base.enemy.graveyard[:-1]:
                if c1.pandaNode is not None:
                    c1.pandaNode.removeNode()
                c1.pandaNode = None

    def focusCard(self, card):
        """
        Draws a big version of the card so the player can read the text
        easily.
        """
        # If the node path is pointing to the right card, don't rebuild
        if (card != self.focusedCard and
                card.getPythonTag('_zone') is not
                self.focusedCard.getTag('_zone')):
            self.focusedCard.unstash()
            if len(self.focusedCard.children) > 0:
                self.focusedCard.children[0].removeNode()

            oldCard = self.focusedCard.getPythonTag('oldCard')
            if oldCard:
                oldCard.show()
            # Make a duplicate of the node. Actually a different node path
            # pointing to the same node
            copy = card.copyTo(card.getParent())
            if card.getPythonTag('zone') is base.player.hand:
                pivot = card.parent.attachNewNode('a')
                pivot.setPos(card, 0.5, 0, 0.55)
                copy.reparentTo(pivot)
                copy.setPos(-1.25, -0.2, 0)
                pivot.setHpr(self.focusedCard, 0, 0, 0)
                copy.setScale(2.5)
                pivot.wrtReparentTo(self.focusedCard)
                self.focusedCard.setPythonTag('oldCard', card)
                card.hide()
            elif card.getPythonTag('zone') is base.enemy.hand:
                pivot = card.parent.attachNewNode('a')
                pivot.setPos(card, 0.5, 0, -0.55)
                copy.reparentTo(pivot)
                copy.setPos(-1.25, -0.2, 0)
                pivot.setHpr(self.focusedCard, 0, 0, 0)
                copy.setScale(2.5)
                pivot.wrtReparentTo(self.focusedCard)
                self.focusedCard.setPythonTag('oldCard', card)
                card.hide()
            elif card.getPythonTag('zone') is base.enemy.graveyard:
                # Don't get cut off by top of screen
                copy.wrtReparentTo(self.focusedCard)
                copy.setPos(copy, 1, 0, -2)
                copy.setHpr(0, 0, 0)
                copy.setScale(2.5)
            else:
                copy.wrtReparentTo(self.focusedCard)
                copy.setPos(copy, 1, 0, 1)
                copy.setHpr(0, 0, 0)
                copy.setScale(2.5)
            # Don't try to play this
            self.focusedCard.setCollideMask(BitMask32(0x0))
            # Keep track of the zone to know if it's changed
            # _zone rather than zone so MouseHandler will grab the card under it
            self.focusedCard.setPythonTag('_zone', card.getPythonTag('zone'))

    def unfocusCard(self):
        # Stash the enlarged card image so it won't collide or be visible.
        # This is different from using hide() because it also prevents
        # collision.
        self.focusedCard.stash()
        c = self.focusedCard.getPythonTag('oldCard')
        if c:
            c.show()

    def loadCard(self, card):
        if card.pandaNode is not None:
            showCard(card.pandaNode)
            updateCardNode(card)
            return card.pandaNode

        cardBase = self.scene.attachNewNode(card.name)

        cm = CardMaker(card.name)

        cardFrame = cardBase.attachNewNode(cm.generate())
        tex = loader.loadTexture('ul_frame_alt.png')
        cardFrame.setTexture(tex)
        cardFrame.setScale(1, 1, 509 / 364)
        cardFrame.setTransparency(True)
        cardFrame.setName('frame')

        cardImage = cardBase.attachNewNode(cm.generate())
        try:
            tex = loader.loadTexture(card.imagePath)
        except IOError:
            tex = loader.loadTexture('base_icons/missing.png')
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
        card.costNode = cost

        rank = panda3d.core.TextNode('rank')
        rank.setText(str(card.rank))
        textNodePath = cardBase.attachNewNode(rank)
        textNodePath.setScale(0.1)
        textNodePath.setPos(0.08, -0.05, 1.125)
        card.rankNode = rank

        desc = panda3d.core.TextNode('desc')
        desc.setText(textwrap.fill(card.desc, width=25))
        textNodePath = cardBase.attachNewNode(desc)
        textNodePath.setScale(0.07)
        textNodePath.setPos(0.09, -0.05, 0.4)

        counter = panda3d.core.TextNode('counter')
        textNodePath = cardBase.attachNewNode(counter)
        textNodePath.setScale(0.4)
        textNodePath.setPos(0.7, -0.05, 0.1)
        card.counterNode = counter

        if hasattr(card, 'counter'):
            counter.setText(str(card.counter))

        cardBase.setPythonTag('card', card)
        card.pandaNode = cardBase

        return cardBase

    def loadBlank(self, path, card):
        cardBase = self.scene.attachNewNode('mysterious card')

        cm = CardMaker('mysterious card')

        cardFrame = cardBase.attachNewNode(cm.generate())
        tex = loader.loadTexture('ul_frame_alt.png')
        cardFrame.setTexture(tex)
        cardFrame.setScale(1, 1, 509 / 364)
        cardFrame.setTransparency(True)
        cardFrame.setName('frame')
        cardBase.setPythonTag('card', card)
        return cardBase

    def loadPlayerBlank(self, card):
        path = base.playerIconPath + "/" + base.playerCardBack
        return self.loadBlank(path, card)

    def loadEnemyBlank(self, card):
        path = base.enemyIconPath + "/" + base.enemyCardBack
        return self.loadBlank(path, card)

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
        if base.hasMulliganed:
            self.makePlayerHand()
        else:
            self.makeMulliganHand()
        self.makeBoard()
        self.makeEnemyHand()
        self.makeEnemyBoard()
        self.makePlayerGraveyard()
        self.makeEnemyGraveyard()

        for n in self.orphan.children:
            n.removeNode()

    def unmake(self):
        self.playerHand.removeNode()  # In case it's parented to the camera
        self.mulliganHand.removeNode()
        self.scene.removeNode()
