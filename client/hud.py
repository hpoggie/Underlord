from direct.showbase.DirectObject import DirectObject
from panda3d.core import TextNode
from direct.gui.DirectGui import DirectButton
from direct.gui.OnscreenText import OnscreenText
from core.enums import Phase


class Fonts(DirectObject):
    def __init__(self):
        self.font = loader.loadFont("Ubuntu-Regular.ttf")
        self.font.setPixelsPerUnit(60)


class Scene(DirectObject):
    def __init__(self):
        self.font = base.fonts.font

    def unmake(self):
        pass


class MainMenu(Scene):
    def __init__(self):
        super().__init__()

        # Put everything under one node to make it easy to destroy
        self.menu = base.aspect2d.attachNewNode(name="Menu")

        OnscreenText(
            text="UNDERLORD",
            font=self.font,
            parent=self.menu,  # Doesn't affect pos/scale
            scale=0.3,
            pos=(0, 0.3, 0))

        base.numPlayersLabel = OnscreenText(
            text="Getting server info...",
            font=self.font,
            parent=self.menu,
            scale=0.1,
            pos=(0, 0.2, 0),
            mayChange=True)

        def connect():
            base.connectionManager.startGame()
            self.menu.detachNode()

        def quit():
            base.userExit()

        buttons = (
            ("Play", connect),
            ("Quit", quit))
        buttonPos = iter([
            (0, 0, len(buttons) * 0.15 - i * 0.15 - 0.3)
            for i in range(len(buttons))])
        for b in buttons:
            DirectButton(
                text=b[0],
                text_font=self.font,
                command=b[1],
                parent=self.menu,
                pos=next(buttonPos),
                scale=0.1,
                frameSize=(-1.5, 1.5, -0.5, 1))

    def unmake(self):
        self.menu.detachNode()


class FactionSelect(Scene):
    def __init__(self):
        super().__init__()

        self.factionSelectLabel = OnscreenText(
            text="faction select",
            font=self.font,
            pos=(0, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.factionButtons = []

        for i, faction in enumerate(base.availableFactions):
            self.factionButtons.append(DirectButton(
                image=faction.iconPath + '/' + faction.cardBack,
                pos=(i * 0.2, 0, 0),
                scale=(0.1, 0.1, 0.1),
                relief=None,
                command=base.pickFaction,
                extraArgs=[i]))

    def unmake(self):
        self.factionSelectLabel.detachNode()
        for btn in self.factionButtons:
            btn.destroy()


class GameHud(Scene):
    def __init__(self):
        super().__init__()

        self.turnLabel = OnscreenText(
            text="",
            font=self.font,
            pos=(0, -0.9, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)

        self.playerManaCapLabel = OnscreenText(
            text=str(base.player.manaCap),
            font=self.font,
            pos=(-0.4, -0.44, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.enemyManaCapLabel = OnscreenText(
            text=str(base.enemy.manaCap),
            font=self.font,
            pos=(-0.5, 0.77),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.cardNameLabel = OnscreenText(
            text="",
            font=self.font,
            pos=(-0.7, -0.6, 0),
            scale=0.07,
            mayChange=True)
        self.tooltipLabel = OnscreenText(
            text="",
            font=self.font,
            pos=(-0.9, -0.8, 0),
            scale=0.05,
            align=TextNode.ALeft,
            wordwrap=10,
            mayChange=True)
        self.cardStatsLabel = OnscreenText(
            text="",
            font=self.font,
            pos=(-0.7, -0.7, 0),
            scale=0.07,
            mayChange=True)
        self.endPhaseLabel = OnscreenText(
            text="",
            font=self.font,
            pos=(0.7, -0.7, 0),
            scale=(0.1, 0.1, 0.1),
            mayChange=True)
        self.endPhaseButton = DirectButton(
            image="./end_phase.png",
            pos=(0.7, 0, -0.85),
            scale=(0.1, 0.1, 0.1),
            relief=None,
            command=base.endPhase)

    def showBigMessage(self, message):
        """
        Put huge text on the screen that obscures stuff
        """
        self.winLabel = OnscreenText(
            text=message,
            font=self.font,
            scale=(0.5, 0.5, 0.5))

    def hideBigMessage(self):
        if hasattr(self, 'winLabel') and self.winLabel is not None:
            self.winLabel.detachNode()

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
        if base.active:
            self.endPhaseButton.show()
        else:
            self.endPhaseButton.hide()

        if base.phase == Phase.reveal and base.active:
            self.playerManaCapLabel.setText(
                str(base.player.mana) + " / " + str(base.player.manaCap))
        else:
            self.playerManaCapLabel.setText(str(base.player.manaCap))
        self.enemyManaCapLabel.setText(str(base.enemy.manaCap))
        self.endPhaseLabel.setText(str(Phase.keys[base.phase]))
        self.turnLabel.setText("Your Turn" if base.active else "Enemy Turn")

    def unmake(self):
        self.hideBigMessage()
        self.turnLabel.detachNode()
        self.playerManaCapLabel.detachNode()
        self.enemyManaCapLabel.detachNode()
        self.cardNameLabel.detachNode()
        self.tooltipLabel.detachNode()
        self.cardStatsLabel.detachNode()
        self.endPhaseLabel.detachNode()
        self.endPhaseButton.detachNode()
