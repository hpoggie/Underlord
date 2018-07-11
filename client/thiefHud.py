import factions.thieves
from client.hud import GameHud


class ThiefHud(GameHud):
    def onThiefAbilityButton(self):
        print('foobar')

    def redraw(self):
        super().redraw()

        if not hasattr(self, 'thiefAbilityButton'):
            self.thiefAbilityButton = self.button(
                text="Faction Ability",
                scale=1,
                pos=(0, 0, -1),
                parent=self.endPhaseButton,
                command=self.onThiefAbilityButton)
