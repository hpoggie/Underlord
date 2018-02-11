from .enums import *


def destroy(card):
    card.game.destroy(card)


class EndOfGame(BaseException):
    def __init__(self, winner):
        self.winner = winner


def event(func):
    def fooBeforeAfter(self, *args, **kwargs):
        for pl in self.players:
            pl.beforeEvent(func.__name__, *args, **kwargs)
            for c in pl.faceups[:]:
                c.beforeEvent(func.__name__, *args, **kwargs)

        func(self, *args, **kwargs)

        for pl in self.players:
            pl.afterEvent(func.__name__, *args, **kwargs)
            for c in pl.faceups[:]:
                c.afterEvent(func.__name__, *args, **kwargs)

    return fooBeforeAfter


class Game:
    def __init__(self, p1Type, p2Type):
        """
        p1Type and p2Type are the classes of player 1 and player 2.
        e.g. Templar and Thief
        """
        self.turn = None  # It's no one's turn until both players have mulliganed
        self.phase = Phase.reveal

        self.players = (p1Type(), p2Type())
        for player in self.players:
            player.game = self
            for card in player.deck:
                card.game = self

    def start(self):
        for player in self.players:
            player.shuffle()
            player.drawOpeningHand()

    def finishMulligans(self):
        self.turn = Turn.p1

    @property
    def activePlayer(self):
        return None if self.turn is None else self.players[self.turn]

    @event
    def fight(self, c1, c2):
        c1.onFight(c2)
        c2.onFight(c1)

        if c1.zone == c1.owner.facedowns:
            c1.visibleWhileFacedown = True
        if c2.zone == c2.owner.facedowns:
            c2.visibleWhileFacedown = True

        if c1.spell or c2.spell:
            return

        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    @event
    def destroy(self, card):
        card.zone = card.owner.graveyard

    @event
    def endPhase(self):
        if self.phase == Phase.reveal:
            for c in self.activePlayer.facedowns[:]:
                c.zone = c.owner.graveyard
            self.activePlayer.drawCard()

        self.phase += 1

        if self.phase == Phase.play:
            for f in self.activePlayer.faceups:
                f.hasAttacked = False
        elif self.phase > Phase.play:
            self.endTurn()

    @event
    def endTurn(self):
        player = self.activePlayer
        player.manaCap += 1
        if player.manaCap > 15:
            player.opponent.win()
        player.opponent.mana = player.opponent.manaCap
        self.turn = Turn.p2 if self.turn == Turn.p1 else Turn.p1
        self.phase = Phase.reveal

    def end(self, winner):
        raise EndOfGame(winner)
