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
        if len(base.player.facedowns) == 1:
            base.endPhaseWithCard(base.player.facedowns[0])
        else:
            super().onEndPhaseButton()
