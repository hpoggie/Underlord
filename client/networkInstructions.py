import copy

from direct.showbase.DirectObject import DirectObject

from core.card import Card
from core.game import EndOfGame
from core.player import Zone


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

    def moveCard(self, index, zone):
        # Compare ids because lists have == overloaded
        playerZoneIds = [id(z) for z in [
            base.player.facedowns,
            base.player.faceups,
            base.player.hand,
            base.player.deck,
            base.player.graveyard]]

        # TODO: hack.
        if id(zone) in playerZoneIds:
            c = base.player.deck[index]
            c.owner = base.player
        else:
            c = base.enemy.deck[index]
            c.owner = base.enemy
        c.game = base.player.game
        c._zone = zone
        zone.append(c)

        return c

    def updatePlayerHand(self, *cardIds):
        base.player.hand = Zone()
        for x in cardIds:
            self.moveCard(x, base.player.hand)
        base.redraw()

    def updatePossiblyInvisibleZone(self, cardIds, zone):
        for x in cardIds:
            if x == -1:
                c = Card(name="mysterious card",
                         owner=base.enemy,
                         game=base.game)
                c.zone = zone
            else:
                card = self.moveCard(x, zone)
                card.visible = True

    def updateEnemyHand(self, *cardIds):
        base.enemy.hand = Zone()
        self.updatePossiblyInvisibleZone(cardIds, base.enemy.hand)
        base.redraw()

    def updatePlayerFacedowns(self, *cardIds):
        base.player.facedowns = Zone()
        for x in cardIds:
            self.moveCard(x, base.player.facedowns)
        base.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        base.enemy.facedowns = Zone()
        self.updatePossiblyInvisibleZone(cardIds, base.enemy.facedowns)
        base.redraw()

    def updatePlayerFaceups(self, *cardIds):
        base.player.faceups = Zone()
        for x in cardIds:
            self.moveCard(x, base.player.faceups)
        base.redraw()

    def updateHasAttacked(self, *values):
        for i, c in enumerate(base.player.faceups):
            c.hasAttacked = values[i]

    def updateEnemyFaceups(self, *cardIds):
        base.enemy.faceups = Zone()
        for x in cardIds:
            self.moveCard(x, base.enemy.faceups)
        base.redraw()

    def updatePlayerGraveyard(self, *cardIds):
        base.player.graveyard = Zone()
        for x in cardIds:
            self.moveCard(x, base.player.graveyard)
        base.redraw()

    def updateEnemyGraveyard(self, *cardIds):
        base.enemy.graveyard = Zone()
        for x in cardIds:
            self.moveCard(x, base.enemy.graveyard)
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

    def updatePlayerCounter(self, index, value):
        base.player.faceups[index].counter = value

    def updateEnemyCounter(self, index, value):
        base.enemy.faceups[index].counter = value

    def requestTarget(self):
        pass

    def requestReplace(self):
        base.guiScene.startReplacing()

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
