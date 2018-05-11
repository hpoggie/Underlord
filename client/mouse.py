from panda3d.core import CollisionNode, GeomNode, CollisionRay
from direct.showbase.DirectObject import DirectObject

from core.core import Phase
from core.player import IllegalMoveError


# Adapted from the asteroids panda3d example
# This function, given a line (vector plus origin point) and a desired y value,
# will give us the point on the line where the desired y value is what we want.
# This is how we know where to position an object in 3D space based on a 2D mouse
# position. It also assumes that we are dragging in the XZ plane.
#
# This is derived from the mathematical of a plane, solved for a given point
def PointAtY(y, point, vec):
    return point + vec * ((y - point.getY()) / vec.getY())


class MouseHandler (DirectObject):
    def __init__(self):
        self.accept('mouse1', self.onMouse1Down, [])  # Left click
        self.accept('mouse1-up', self.onMouse1Up, [])
        self.accept('mouse3', self.onMouse3Down, [])  # Right click

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

        self._dragging = None

        # Counts down between clicks to detect double click
        self.doubleClickTimer = -1.0
        self.doubleClickInterval = 1.0

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
                pickedObj = pickedObj.findNetPythonTag('zone')
                return pickedObj

    def doClick(self):
        pickedObj = self.getObjectClickedOn()

        if self.dragging:
            return

        if self.targeting and pickedObj is not None:
            base.acceptTarget(pickedObj)
        elif pickedObj and not pickedObj.isEmpty():
            zone = pickedObj.getPythonTag('zone')
            if zone is base.player.hand and not base.hasMulliganed:
                c = pickedObj.getPythonTag('card')
                if c in base.toMulligan:
                    base.toMulligan.remove(c)
                else:
                    base.toMulligan.append(c)
                base.zoneMaker.makePlayerHand()
            elif zone is base.player.hand:
                self.dragging = pickedObj
            elif zone is base.player.facedowns:
                if self.activeCard:
                    self.activeCard = None
                else:
                    base.revealFacedown(pickedObj)
            elif zone is base.player.faceups and base.phase == Phase.play:
                self.activeCard = pickedObj
            elif zone is base.enemy.facedowns and self.activeCard:
                base.attack(self.activeCard, pickedObj)
                self.activeCard = None
            elif zone == base.enemy.faceups and self.activeCard:
                base.attack(self.activeCard, pickedObj)
                self.activeCard = None
            elif zone is base.enemy.face and self.activeCard:
                base.attack(self.activeCard, pickedObj)
                self.activeCard = None
        else:
            self.activeCard = None

    @property
    def dragging(self):
        return self._dragging

    @dragging.setter
    def dragging(self, obj):
        self._dragging = obj
        if obj is None:
            base.zoneMaker.makePlayerHand()  # Put the card back
        else:
            obj.reparentTo(base.zoneMaker.scene)

    def stopDragging(self):
        """
        Stop dragging the card and play it if it's in the drop zone
        """
        # Borders of the drop zone
        # If you drop the card outside the drop zone,
        # the action is cancelled
        pos = self._dragging.getPos()
        inX = pos.x > 0 and pos.x < 8
        inZ = pos.z > 0 and pos.z < 6
        if inX and inZ:
            try:
                base.playCard(self._dragging)
            except IllegalMoveError as e:
                print(e)
        self.dragging = None

    def onMouse1Down(self):
        if self._dragging is not None:
            self.stopDragging()
            self.doubleClickTimer = -1
        elif self.doubleClickTimer <= 0:
            self.doubleClickTimer = 0.2
            try:
                self.doClick()
            except IllegalMoveError as e:
                print(e)

    def onMouse1Up(self):
        if self._dragging and self.doubleClickTimer <= 0:
            self.stopDragging()

    def onMouse3Down(self):
        if self.targeting:
            base.acceptTarget(None)

        if self.dragging:
            self.dragging = None

    def mouseOverTask(self):
        if base.mouseWatcherNode.hasMouse():
            if self.doubleClickTimer > 0:
                # Count down based on how long it took to draw the last frame
                self.doubleClickTimer -= globalClock.getDt()

            if hasattr(base.guiScene, 'redrawTooltips'):
                base.guiScene.redrawTooltips()

            if hasattr(self, '_activeObj') and self._activeObj is not None:
                path = base.playerIconPath + "/" + base.playerCardBack
                self._activeObj.setTexture(loader.loadTexture(path))
                self._activeObj = None

            if self.dragging is not None:
                mpos = base.mouseWatcherNode.getMouse()
                # Drag the card
                # See the Panda3d chess example
                self.pickerRay.setFromLens(
                    base.camNode, mpos.getX(), mpos.getY())
                # Get a vector relative to the camera position
                nearPoint = render.getRelativePoint(
                    camera, self.pickerRay.getOrigin())
                nearVec = render.getRelativeVector(
                    camera, self.pickerRay.getDirection())
                # Drag in the XZ plane
                self.dragging.setPos(PointAtY(.5, nearPoint, nearVec))
            else:
                pickedObj = self.getObjectClickedOn()
                if pickedObj:
                    card = pickedObj.getPythonTag('card')
                    if card is not None:
                        if card.zone is base.player.facedowns or card.zone is base.enemy.facedowns:
                            self._activeObj = pickedObj
                            # TODO: use enemy icon path when that's a thing
                            path = base.playerIconPath + "/" + card.image
                            pickedObj.setTexture(loader.loadTexture(path))

                        base.guiScene.updateCardTooltip(card)
