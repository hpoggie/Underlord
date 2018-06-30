from core.game import Phase
from client.hud import GameHud
from client.zoneMaker import hideCard, showCard


class MarinerHud(GameHud):
    def onFishButton(self):
        base.endPhase(fish=True)

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

            if len(targets) == 3:
                base.fishReplace(targets)
                base.finishTargeting()

        base.targetCallback = callback
        base.targetDesc = "Choose 3 cards to put back."
        base.mouseHandler.targeting = True

    def redraw(self):
        super().redraw()

        if not hasattr(self, 'fishButton'):
            self.fishButton = self.button(
                text="Faction Ability",
                scale=1,
                pos=(0, 0, -1),
                parent=self.endPhaseButton,
                command=self.onFishButton)

        if (base.phase == Phase.reveal and
                base.active and
                base.bothPlayersMulliganed and
                not base.hasFirstPlayerPenalty):
            self.fishButton.show()
        else:
            self.fishButton.hide()
