from direct.showbase.DirectObject import DirectObject


class NetworkInstructions(DirectObject):
    """
    Handles instructions from the server.
    """
    def updateNumPlayers(self, n):
        # numPlayersLabel is set by hud
        if hasattr(base, 'numPlayersLabel') and base.numPlayersLabel:
            base.numPlayersLabel.setText(str(n))

    def updateEnemyFaction(self, index):
        base.enemyFaction = base.availableFactions[index]

    def updatePlayerHand(self, *cardIds):
        base.player.hand = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            base.player.hand[i] = base.faction.deck[x]
            base.player.hand[i].owner = base.player
        base.redraw()

    def updateEnemyHand(self, size):
        base.enemy.hand = [None] * size

    def updatePlayerFacedowns(self, *cardIds):
        base.player.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            base.player.facedowns[i] = base.faction.deck[x]
            base.player.facedowns[i].owner = base.player
        base.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        base.enemy.facedowns = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            card = base.enemyFaction.deck[x]
            base.enemy.facedowns[i] = card if x != -1 else None
            if x != -1:
                base.enemy.facedowns[i].owner = base.enemy
        base.redraw()

    def updatePlayerFaceups(self, *cardIds):
        base.player.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            base.player.faceups[i] = base.faction.deck[x]
            base.player.faceups[i].owner = base.player
        base.redraw()

    def updateEnemyFaceups(self, *cardIds):
        base.enemy.faceups = [None] * len(cardIds)
        for i, x in enumerate(cardIds):
            base.enemy.faceups[i] = base.enemyFaction.deck[x]
            base.enemy.faceups[i].owner = base.enemy
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
        base.mouseHandler.targeting = True

    def winGame(self):
        base.hud.showBigMessage("Victory")
        base.quitToMainMenu()

    def loseGame(self):
        base.hud.showBigMessage("Defeat")

    def setActive(self, value):
        base.active = bool(value)
