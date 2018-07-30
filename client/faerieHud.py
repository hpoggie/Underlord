from core.game import Phase

from . import hud
from client.zoneMaker import hideCard, showCard


class FaerieHud(hud.GameHud):
    def startReplacing(self, nTargets):
        targets = []

        def callback(target):
            if target in targets:
                targets.remove(target)
                showCard(target)
            else:
                targets.append(target)
                hideCard(target)

            if len(targets) == nTargets:
                base.replace(targets)
                base.finishTargeting()

        base.mouseHandler.startTargeting("Select targets", callback)

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
