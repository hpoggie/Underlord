from panda3d.core import CollisionNode, GeomNode, CollisionRay
from direct.showbase.DirectObject import DirectObject

from core.core import Phase
from core.player import IllegalMoveError


class MouseHandler (DirectObject):
    def __init__(self):
        self.accept('mouse1', self.onMouse1, [])  # Left click
        self.accept('mouse3', self.onMouse3, [])  # Right click

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
        self._targeting = False

    @property
    def targeting(self):
        return self._targeting

    @targeting.setter
    def targeting(self, value):
        self._targeting = value
        if self._targeting:
            base.guiScene.showTargeting()
        else:
            base.guiScene.hideTargeting()

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
            return

        if pickedObj and not pickedObj.isEmpty():
            if pickedObj.getTag('zone') == 'hand':
                if not base.hasMulliganed:
                    c = base.player.hand[base.playerHandNodes.index(pickedObj)]
                    if c in base.toMulligan:
                        base.toMulligan.remove(c)
                    else:
                        base.toMulligan.append(c)
                    base.zoneMaker.makePlayerHand()
                else:
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
                else:
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'enemy face-down':
                if self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face-up':
                if base.phase == Phase.play and not self.activeCard:
                    self.activeCard = pickedObj
                elif self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
            elif pickedObj.getTag('zone') == 'face' and self.activeCard:
                    base.attack(self.activeCard, pickedObj)
                    self.activeCard = None
        else:
            self.activeCard = None

    def onMouse1(self):
        try:
            self.doClick()
        except IllegalMoveError as e:
            print(e)

    def onMouse3(self):
        if self.targeting:
            base.acceptTarget(None)

    def mouseOverTask(self):
        if base.mouseWatcherNode.hasMouse():
            if hasattr(base.guiScene, 'redrawTooltips'):
                base.guiScene.redrawTooltips()

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = base.playerIconPath + "/" + base.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            pickedObj = self.getObjectClickedOn()
            if pickedObj:
                if pickedObj.getTag('zone') == 'hand':
                    card = base.player.hand[
                        base.playerHandNodes.index(pickedObj)]
                    base.guiScene.updateCardTooltip(card)
                elif pickedObj.getTag('zone') == 'face-down':
                    card = base.player.facedowns[
                        base.playerFacedownNodes.index(pickedObj)]
                    self._activeObj = pickedObj
                    path = base.playerIconPath + "/" + card.image
                    pickedObj.setTexture(loader.loadTexture(path))
                    base.guiScene.updateCardTooltip(card)
                elif pickedObj.getTag('zone') == 'enemy face-down':
                    card = base.enemy.facedowns[
                        base.enemyFacedownNodes.index(pickedObj)]
                    if card is not None:
                        self._activeObj = pickedObj
                        path = base.playerIconPath + "/" + card.image
                        pickedObj.setTexture(loader.loadTexture(path))
                        base.guiScene.updateCardTooltip(card)
                elif pickedObj.getTag('zone') == 'face-up':
                    if pickedObj in base.playerFaceupNodes:
                        card = base.player.faceups[
                            base.playerFaceupNodes.index(pickedObj)]
                    else:
                        card = base.enemy.faceups[
                            base.enemyFaceupNodes.index(pickedObj)]
                    base.guiScene.updateCardTooltip(card)
