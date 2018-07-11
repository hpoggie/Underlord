import factions.thieves
from client.hud import GameHud
from panda3d.core import TextNode
from direct.gui.DirectGui import OnscreenText
# https://www.panda3d.org/manual/index.php/DirectEntry
from direct.gui.DirectGui import DirectEntry


class ThiefHud(GameHud):
    def __init__(self):
        super().__init__()
        self.entryLabel = self.label(
            text='',
            mayChange=True)

        self.entry = DirectEntry(
            initialText='Type card name...',
            scale=0.05,
            focus=1,
            command=self.useThiefAbility,
            focusInCommand=lambda: self.entry.enterText(''))

    def useThiefAbility(self, cardname):
        cardId = next(c for c in base.enemy.deck if c.name == cardname).cardId
        base.networkManager.useThiefAbility(0, cardId, 0)

    def onThiefAbilityButton(self):
        pass

    def redraw(self):
        super().redraw()

        if not hasattr(self, 'thiefAbilityButton'):
            self.thiefAbilityButton = self.button(
                text="Faction Ability",
                scale=1,
                pos=(0, 0, -1),
                parent=self.endPhaseButton,
                command=self.onThiefAbilityButton)
