from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from core.enums import Phase
from panda3d.core import TransparencyAttrib
import factions.templars


class Fonts(DirectObject):
    def __init__(self):
        self.font = loader.loadFont("Ubuntu-Regular.ttf")
        self.font.setPixelsPerUnit(60)


class Scene(DirectObject):
    def __init__(self):
        self.font = base.fonts.font

        # Put everything under one node to make it easy to destroy
        self.root = base.aspect2d.attachNewNode(name="GuiScene")

    def label(self, **kwargs):
        defaultArgs = {}
        # Attach the label to the root.
        # Note that this does not affect pos/scale for OnscreenText
        defaultArgs['parent'] = self.root
        defaultArgs['font'] = self.font  # Use the default font
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}  # Merge the 2 dicts; prefer kwargs
        return OnscreenText(**kwargs)

    def button(self, **kwargs):
        defaultArgs = {}
        # Attach the label to the root.
        # Note that this does not affect pos/scale for OnscreenText
        defaultArgs['parent'] = self.root
        defaultArgs['text_font'] = self.font  # Use the default font
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}  # Merge the 2 dicts; prefer kwargs
        return DirectButton(**kwargs)

    def image(self, **kwargs):
        defaultArgs = {}
        defaultArgs['parent'] = self.root
        defaultArgs['scale'] = 0.1
        kwargs = {**defaultArgs, **kwargs}
        image = OnscreenImage(**kwargs)
        image.setTransparency(TransparencyAttrib.MAlpha)  # Enable alpha
        return image

    def unmake(self):
        self.root.detachNode()


class ConnectionUI(Scene):
    def __init__(self):
        super().__init__()
        self.connectingLabel = self.label(text="connecting to server")

    def showConnectionError(self, callback):
        self.connectingLabel.hide()
        self.connectionFailedLabel = self.label(text="Error. Could not connect to server")
        self.reconnectButton = self.button(
            pos=(0, 0, -0.25),
            image="./reconnect.png",
            relief=None,
            command=callback)


class MainMenu(Scene):
    def __init__(self):
        super().__init__()

        self.label(
            text="UNDERLORD",
            scale=0.3,
            pos=(0, 0.3, 0))

        base.numPlayersLabel = self.label(
            text="Getting server info...",
            pos=(0, 0.2, 0),
            mayChange=True)

        def connect():
            base.connectionManager.startGame()

        def quit():
            base.userExit()

        buttons = (
            ("Play", connect),
            ("Quit", quit))
        buttonPos = iter([
            (0, 0, len(buttons) * 0.15 - i * 0.15 - 0.3)
            for i in range(len(buttons))])
        for b in buttons:
            self.button(
                text=b[0],
                command=b[1],
                pos=next(buttonPos),
                frameSize=(-1.5, 1.5, -0.5, 1))

    def showWaitMessage(self):
        self.label(
            text="Waiting for another player.",
            pos=(0, -0.5, 0))


class FactionSelect(Scene):
    def __init__(self):
        super().__init__()

        self.label(
            text="faction select",
            pos=(0, -0.7, 0),
            mayChange=True)

        for i, faction in enumerate(base.availableFactions):
            self.button(
                image=faction.iconPath + '/' + faction.cardBack,
                parent=self.root,
                pos=(i * 0.2, 0, 0),
                relief=None,
                command=base.pickFaction,
                extraArgs=[i])

    def showBigMessage(self, message):
        """
        Put huge text on the screen that obscures stuff
        """
        self.label(
            text=message,
            scale=(0.5, 0.5, 0.5))

    def showWaitMessage(self):
        self.label(
            text="Waiting for opponent.",
            pos=(0, -0.5, 0))


class GameHud(Scene):
    def __init__(self):
        super().__init__()

        self.turnLabel = self.label(
            text="",
            pos=(0, -0.9, 0),
            mayChange=True)

        self.playerManaCapLabel = self.label(
            text=str(base.player.manaCap),
            pos=(-0.4, -0.44, 0),
            mayChange=True)
        self.enemyManaCapLabel = self.label(
            text=str(base.enemy.manaCap),
            pos=(-0.5, 0.77),
            mayChange=True)
        self.cardNameLabel = self.label(
            text="",
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = self.label(
            text="",
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = self.label(
            text="",
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = self.label(
            text="",
            pos=(0.7, -0.7, 0),
            mayChange=True)
        self.endPhaseButton = self.button(
            text="End Phase",
            pos=(0.7, 0, -0.85),
            command=self.onEndPhaseButton)
        self.mulliganButton = self.button(
            text="Mulligan",
            pos=(0.7, 0, -0.85),
            command=self.onMulliganButton)

        if isinstance(base.player, factions.templars.Templar):
            self.templarEndPhaseButton = self.button(
                text="Faction Ability",
                scale=1,
                pos=(0, 0, -1),
                parent=self.endPhaseButton,
                command=self.onTemplarEndPhaseButton)

    def onMulliganButton(self):
        base.mulligan()

    def onEndPhaseButton(self):
        base.endPhase()
        if base.activeDecision is not None:
            base.acceptTarget(None)
            base.mouseHandler.targeting = False
            base.activeDecision = None

    def onTemplarEndPhaseButton(self):
        base.endPhase()

    def showBigMessage(self, message):
        """
        Put huge text on the screen that obscures stuff
        """
        self.winLabel = self.label(
            text=message,
            scale=(0.5, 0.5, 0.5))

    def hideBigMessage(self):
        if hasattr(self, 'winLabel') and self.winLabel is not None:
            self.winLabel.detachNode()

    def showTargeting(self):
        if not hasattr(self, 'targetingLabel'):
            self.targetingLabel = self.label(
                text="Select target",
                pos=(0, -0.7, 0))
            self.targetingGradient = self.image(
                image="gradient.png",
                pos=(0, -0.7, 0),
                scale=(10, 1, 3))
        else:
            self.targetingLabel.show()
            self.targetingGradient.show()

    def hideTargeting(self):
        self.targetingLabel.hide()
        self.targetingGradient.hide()

    def redrawTooltips(self):
        if hasattr(self, 'cardNameLabel'):
            self.cardNameLabel.setText("")

        if hasattr(self, 'cardStatsLabel'):
            self.cardStatsLabel.setText("")

        if hasattr(self, 'tooltipLabel'):
            if hasattr(self, 'phase') and self.active:
                self.tooltipLabel.setText(
                    "Reveal face-down cards" if self.phase == Phase.reveal
                    else "Play face-down cards and attack")
            else:
                self.tooltipLabel.setText("")

    def updateCardTooltip(self, card):
        self.cardNameLabel.setText(card.name)
        label = str(card.cost) + " " + str(card.rank)
        self.cardStatsLabel.setText(label)
        self.tooltipLabel.setText(
            ("Instant. " if card.playsFaceUp else "") + card.desc)

    def redraw(self):
        if base.hasMulliganed:
            self.mulliganButton.detachNode()

        if base.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()

        if base.phase == Phase.play and base.active and hasattr(self, 'templarEndPhaseButton'):
            self.templarEndPhaseButton.show()
        else:
            self.templarEndPhaseButton.hide()

        if base.phase == Phase.reveal and base.active:
            self.playerManaCapLabel.setText(
                str(base.player.mana) + " / " + str(base.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(base.player.manaCap))
        self.enemyManaCapLabel.setText(str(base.enemy.manaCap))
        if not base.hasMulliganed:
            self.endPhaseLabel.setText("Mulligan")
        else:
            self.endPhaseLabel.setText(str(Phase.keys[base.phase]))
        self.turnLabel.setText("Your Turn" if base.active else "Enemy Turn")
