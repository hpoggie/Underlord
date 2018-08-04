import copy

from direct.showbase.DirectObject import DirectObject

from core.card import Card
from core.game import EndOfGame
from core.zone import Zone


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

    def requestGoingFirstDecision(self):
        base.decideWhetherToGoFirst()

    def updateEnemyFaction(self, index):
        base.enemyFaction = base.availableFactions[index]

    def enemyGoingFirst(self):
        base.onGameStarted(goingFirst=False)

    def enemyGoingSecond(self):
        base.onGameStarted(goingFirst=True)

    def updateBothPlayersMulliganed(self):
        base.bothPlayersMulliganed = True

    def idsToCards(self, cardIds):
        idAndEnemy = zip(cardIds[::2], cardIds[1::2])
        cards = []
        for cardId, ownedByEnemy in idAndEnemy:
            if cardId == -1:
                cards.append(Card(name="mysterious card",
                             owner=base.enemy,
                             game=base.game,
                             cardId=-1))
            else:
                c = (base.enemy.referenceDeck[cardId] if ownedByEnemy
                     else base.player.referenceDeck[cardId])
                c.visible = True
                cards.append(c)

        return cards

    def moveCard(self, c, zone):
        # fake moveToZone
        if c._zone is not None and c in c._zone:
            c._zone.remove(c)
        c._zone = zone
        zone.append(c)

        return c

    def updatePlayerHand(self, *cardIds):
        base.player.hand[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.player.hand)

    def updateEnemyHand(self, *cardIds):
        base.enemy.hand[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.enemy.hand)

    def updatePlayerFacedowns(self, *cardIds):
        base.player.facedowns[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.player.facedowns)

    def updateEnemyFacedowns(self, *cardIds):
        base.enemy.facedowns[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.enemy.facedowns)

    def updatePlayerFaceups(self, *cardIds):
        base.player.faceups[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.player.faceups)

    def updateHasAttacked(self, *values):
        for i, c in enumerate(base.player.faceups):
            c.hasAttacked = values[i]

    def updateEnemyFaceups(self, *cardIds):
        base.enemy.faceups[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.enemy.faceups)

    def updatePlayerGraveyard(self, *cardIds):
        base.player.graveyard[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.player.graveyard)

    def updateEnemyGraveyard(self, *cardIds):
        base.enemy.graveyard[:] = []
        for x in self.idsToCards(cardIds):
            self.moveCard(x, base.enemy.graveyard)

    def updatePlayerManaCap(self, manaCap):
        base.player.manaCap = manaCap

    def updatePlayerMana(self, mana):
        base.player.mana = mana

    def updateEnemyManaCap(self, manaCap):
        base.enemy.manaCap = manaCap

    def updatePhase(self, phase):
        base.phase = phase

    def updatePlayerCounter(self, index, value):
        base.player.faceups[index].counter = value

    def updateEnemyCounter(self, index, value):
        base.enemy.faceups[index].counter = value

    def requestTarget(self):
        pass

    def requestReplace(self, nArgs):
        base.guiScene.startReplacing(nArgs)

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
        base.active = value

    def endRedraw(self):
        base.redraw()
