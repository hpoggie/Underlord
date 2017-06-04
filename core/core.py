from enums import *
from player import Player


class EndOfGame:
    def __init__(self, winner):
        self.winner = winner


class Game:
    def __init__(self, p1Faction, p2Faction):
        self.turn = Turn.p1
        self.phase = Phase.reveal

        self.players = (Player(p1Faction), Player(p2Faction))
        for player in self.players:
            player.game = self
            for card in player.deck:
                card.game = self

    def start(self):
        for player in self.players:
            player.shuffle()
            player.drawOpeningHand()

    @property
    def activePlayer(self):
        return self.players[self.turn]

    def fight(self, c1, c2):
        if c1.spell or c2.spell:
            return
        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    def destroy(self, card):
        card.moveZone(Zone.graveyard)

    def endPhase(self):
        if self.phase == Phase.reveal:
            self.activePlayer.facedowns = []
            self.activePlayer.drawCard()

        self.phase += 1

        if self.phase == Phase.play:
            for f in self.activePlayer.faceups:
                f.hasAttacked = False
        elif self.phase > Phase.play:
            self.endTurn()

    def endTurn(self):
        player = self.activePlayer
        player.manaCap += 1
        if player.manaCap > 15:
            player.getEnemy().win()
        player.getEnemy().mana = player.getEnemy().manaCap
        self.turn = Turn.p2 if self.turn == Turn.p1 else Turn.p1
        self.phase = Phase.reveal

    def end(self, winner):
        raise EndOfGame(winner)
