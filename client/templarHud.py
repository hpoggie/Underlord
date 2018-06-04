from core.game import Phase
from core.player import IllegalMoveError
import factions.templars
from client.hud import GameHud


class TemplarHud(GameHud):
    def onEndPhaseButton(self):
        try:
            base.endPhase(card=None)
        except IllegalMoveError as e:
            print(e)

    def onTemplarEndPhaseButton(self):
        def callback(target):
            try:
                base.endPhase(card=target)
            except IllegalMoveError as e:
                print(e)
            else:
                base.finishTargeting()

        base.targetCallback = callback
        # TODO: grab desc from faction?
        base.targetDesc = "Choose a card to discard."
        base.mouseHandler.targeting = True

    def redraw(self):
        super().redraw()

        if not hasattr(self, 'templarEndPhaseButton'):
            self.templarEndPhaseButton = self.button(
                text="Faction Ability",
                scale=1,
                pos=(0, 0, -1),
                parent=self.endPhaseButton,
                command=self.onTemplarEndPhaseButton)

        # Hide everything if we haven't mulliganed yet
        if not base.bothPlayersMulliganed:
            self.templarEndPhaseButton.hide()
            return

        if base.phase == Phase.play and base.active:
            self.templarEndPhaseButton.show()
        else:
            self.templarEndPhaseButton.hide()

