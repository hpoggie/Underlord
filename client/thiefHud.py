import factions.thieves
from client.hud import GameHud
from panda3d.core import TextNode
from direct.gui.DirectGui import OnscreenText
# https://www.panda3d.org/manual/index.php/DirectEntry
from direct.gui.DirectGui import DirectEntry

from client.zoneMaker import hideCard, showCard


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

        self.entry.hide()

        self.thiefAbilityButton = self.button(
            text="Faction Ability",
            scale=1,
            pos=(0, 0, -1),
            parent=self.endPhaseButton,
            command=self.onThiefAbilityButton)

    def useThiefAbility(self, cardname):
        try:
            cardId = next(c for c in base.enemy.deck if c.name == cardname).cardId
        except StopIteration:
            print("That is not the name of an enemy card.")
        else:
            base.networkManager.useThiefAbility(0, cardId, 0)
            base.mouseHandler.targeting = False
            self.entry.hide()

    def onThiefAbilityButton(self):
        def chooseTarget(target):
            self.toSteal = target
            self.entry.show()

        def chooseDiscard(target):
            self.toDiscard = target
            hideCard(target)
            base.mouseHandler.startTargeting(
                "Choose a target.",
                chooseTarget)

        base.mouseHandler.startTargeting(
            "Choose a card to discard.",
            chooseDiscard)

    def startReplacing(self):
        targets = []

        def callback(target):
            if target is None:
                return

            if target in targets:
                targets.remove(target)
                showCard(target)
            else:
                targets.append(target)
                hideCard(target)

            if len(targets) == 2:
                base.replace(targets)
                base.finishTargeting()

        base.mouseHandler.startTargeting(
            "Choose 2 cards to topdeck.",
            callback)
