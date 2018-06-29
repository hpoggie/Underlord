import copy

from direct.showbase.DirectObject import DirectObject

from core.card import Card
from core.game import EndOfGame


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
            c = copy.copy(base.faction.deck[index])
            c.owner = base.player
        else:
            c = copy.copy(base.enemyFaction.deck[index])
            c.owner = base.enemy
        c.game = base.player.game
        # TODO: really hacky. Can't just set card.zone
        # Because it will trigger onSpawn
        try:
            c.zone = zone
        except EndOfGame:
            pass

        return c

    def updatePlayerHand(self, *cardIds):
        base.player.hand = []
        for x in cardIds:
            self.moveCard(x, base.player.hand)
        base.redraw()

    def updateEnemyHand(self, size):
        base.enemy.hand = [Card(owner=base.player.opponent) for i in range(size)]

    def updatePlayerFacedowns(self, *cardIds):
        base.player.facedowns = []
        for x in cardIds:
            self.moveCard(x, base.player.facedowns)
        base.redraw()

    def updateEnemyFacedowns(self, *cardIds):
        base.enemy.facedowns = []
        for x in cardIds:
            if x == -1:
                c = Card(name="mysterious card",
                         owner=base.enemy,
                         game=base.game)
                c.zone = base.enemy.facedowns
            else:
                card = self.moveCard(x, base.enemy.facedowns)
                card.visibleWhileFacedown = True
        base.redraw()

    def updatePlayerFaceups(self, *cardIds):
        base.player.faceups = []
        for x in cardIds:
            self.moveCard(x, base.player.faceups)
        base.redraw()

    def updateHasAttacked(self, *values):
        for i, c in enumerate(base.player.faceups):
            c.hasAttacked = values[i]

    def updateEnemyFaceups(self, *cardIds):
        base.enemy.faceups = []
        for x in cardIds:
            self.moveCard(x, base.enemy.faceups)
        base.redraw()

    def updatePlayerGraveyard(self, *cardIds):
        base.player.graveyard = []
        for x in cardIds:
            self.moveCard(x, base.player.graveyard)
        base.redraw()

    def updateEnemyGraveyard(self, *cardIds):
        base.enemy.graveyard = []
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
