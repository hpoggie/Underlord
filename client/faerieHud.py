from core.game import Phase

from . import hud


class FaerieHud(hud.GameHud):
    def onEndPhaseButton(self):
        if base.game.phase != Phase.reveal:
            base.endPhase()
            return

        def callback(card):
            base.endPhase(card)
            base.finishTargeting()

        if len(base.player.facedowns) == 0:
            super().onEndPhaseButton()
        elif len(base.player.facedowns) == 1:
            base.endPhaseWithCard(base.player.facedowns[0])
        else:
            base.mouseHandler.startTargeting("Choose card to keep", callback)
