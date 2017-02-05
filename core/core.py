from enums import *
from player import Player
from factions.templars import Templars
import action


def setupActions(player):
    from action import Action
    vars(player).update(dict((key, Action(player, value)) for key, value in action.actions.iteritems()))


class Game:
    def __init__(self):
        self.turn = Turn.p1
        self.phase = Phase.reveal

        self.players = (Player(Templars), Player(Templars))
        for player in self.players:
            player.game = self
            setupActions(player)
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

        self.phase += 1

        if self.phase == Phase.draw:
            self.activePlayer.drawCard()
        elif self.phase == Phase.attack:
            for f in self.activePlayer.faceups:
                f.hasAttacked = False
        elif self.phase == Phase.play:
            pass
        else:
            self.endTurn()

    def endTurn(self):
        player = self.activePlayer
        player.manaCap += 1
        if player.manaCap > 15:
            player.getEnemy().win()
        player.mana = player.manaCap
        print "player " + player + " mana cap is " + str(player.manaCap)
        self.turn = Turn.p2 if self.turn == Turn.p1 else Turn.p1
        self.phase = Phase.reveal
