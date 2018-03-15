from direct.showbase.DirectObject import DirectObject
import copy


class NetworkInstructions(DirectObject):
    """
    Handles instructions from the server.
    """
    def onEnteredGame(self):
        base.onEnteredGame()

    def updateNumPlayers(self, n):
        # numPlayersLabel is set by hud
        if hasattr(base, 'numPlayersLabel') and base.numPlayersLabel:
            base.numPlayersLabel.setText(str(n) + " players in lobby.")

    def updateEnemyFaction(self, index):
        base.enemyFaction = base.availableFactions[index]

    def moveCard(self, index, zone):
        playerZones = [base.player.facedowns,
                       base.player.faceups,
                       base.player.hand,
                       base.player.deck]

        # TODO: hack. also enemy faction
        c = copy.copy(base.faction.deck[index])
        c.owner = base.player if zone in playerZones else base.enemy
        c.zone = zone

    def updatePlayerHand(self, *cardIds):
        base.player.hand = []
        for x in cardIds:
            self.moveCard(x, base.player.hand)
        base.redraw()

    def updateEnemyHand(self, size):
        base.enemy.hand = [None] * size

    def updatePlayerFacedowns(self, *cardIds):
        base.player.facedowns = []
        for x in cardIds:
            self.moveCard(x, base.player.facedowns)
        base.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        base.enemy.facedowns = []
        for x in cardIds:
            if x == -1:
                base.enemy.facedowns.append(None)
            else:
                self.moveCard(x, base.enemy.facedowns)
        base.redraw()

    def updatePlayerFaceups(self, *cardIds):
        base.player.faceups = []
        for x in cardIds:
            self.moveCard(x, base.player.faceups)
        base.redraw()

    def updateEnemyFaceups(self, *cardIds):
        base.enemy.faceups = []
        for i, x in enumerate(cardIds):
            self.moveCard(x, base.enemy.faceups)
        base.redraw()

    def updatePlayerManaCap(self, manaCap):
        base.player.manaCap = manaCap
        base.redraw()

    def updatePlayerMana(self, mana):
        base.player.mana = mana
        base.redraw()

    def updateEnemyManaCap(self, manaCap):
        base.enemy.manaCap = manaCap
        base.redraw()

    def updatePhase(self, phase):
        base.phase = phase

    def requestTarget(self):
        pass

    def winGame(self):
        base.guiScene.showBigMessage("Victory")
        base.quitToMainMenu()

    def loseGame(self):
        base.guiScene.showBigMessage("Defeat")
        base.quitToMainMenu()

    def kick(self):
        base.guiScene.showBigMessage("Kicked")
        base.quitToMainMenu()

    def setActive(self, value):
        base.active = bool(value)
