from . import enums

Turn = enums.numericEnum('p1', 'p2')
Phase = enums.numericEnum('startOfTurn', 'reveal', 'play')


def destroy(card):
    card.game.destroy(card)


class EndOfGame(BaseException):
    def __init__(self, winner):
        self.winner = winner


def event(func):
    # Automatically generate function names for before and after events
    # e.g. endPhase -> beforeEndPhase
    upperName = func.__name__[0].upper() + func.__name__[1:]
    beforeEventName = 'before' + upperName
    afterEventName = 'after' + upperName

    def fooBeforeAfter(self, *args, **kwargs):
        self.doEventTriggers(beforeEventName, *args, **kwargs)
        func(self, *args, **kwargs)
        self.doEventTriggers(afterEventName, *args, **kwargs)

    return fooBeforeAfter


class Game:
    def __init__(self, p1Type, p2Type):
        """
        p1Type and p2Type are the classes of player 1 and player 2.
        e.g. Templar and Thief
        """
        # It's no one's turn until both players have mulliganed
        self.turn = None
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
        self.players[0].hasFirstPlayerPenalty = True
        self.players[1].hasFirstPlayerPenalty = False

    @property
    def activePlayer(self):
        return None if self.turn is None else self.players[self.turn]

    def doEventTriggers(self, name, *args, **kwargs):
        # Find the right function by name and call it
        # If it doesn't exist, don't worry about it
        def doTrigger(obj, name):
            if hasattr(obj, name):
                getattr(obj, name)(*args, **kwargs)

        for pl in self.players:
            doTrigger(pl, name)
            for c in pl.faceups[:]:
                doTrigger(c, name)

    def fight(self, c1, c2):
        self.doEventTriggers('beforeAnyFight', c1, c2)
        c1.beforeFight(c2)
        c2.beforeFight(c1)

        if c1.zone == c1.controller.facedowns:
            c1.visible = True
        if c2.zone == c2.controller.facedowns:
            c2.visible = True

        if c1.spell or c2.spell:
            if c1.illusion:
                self.destroy(c1)
            if c2.illusion:
                self.destroy(c2)
        else:
            if c1.rank < c2.rank:
                self.destroy(c1)
            if c1.rank > c2.rank:
                self.destroy(c2)
            elif c1.rank == c2.rank:
                self.destroy(c1)
                self.destroy(c2)

        self.doEventTriggers('afterAnyFight', c1, c2)
        c1.afterFight(c2)
        c2.afterFight(c1)

    @event
    def destroy(self, card):
        card.zone = card.owner.graveyard

    @event
    def dealDamage(self, player, amount):
        player.manaCap += amount

    @event
    def endPhase(self, keepFacedown=[]):
        if self.phase == Phase.reveal:
            for c in self.activePlayer.facedowns[:]:
                if c not in keepFacedown:
                    c.zone = c.owner.graveyard
            if self.activePlayer.hasFirstPlayerPenalty:
                self.activePlayer.hasFirstPlayerPenalty = False
            else:
                self.activePlayer.drawCard()

        self.phase += 1

        if self.phase == Phase.play:
            for f in self.activePlayer.faceups:
                f.hasAttacked = False
        elif self.phase > Phase.play:
            self.endTurn()

    @event
    def endTurn(self):
        # Make hand cards invisible so you can't easily see what's played
        for pl in self.players:
            for c in pl.hand:
                c.visible = False

        player = self.activePlayer
        player.manaCap += 1
        if player.manaCap > 15:
            player.opponent.win()
        player.opponent.mana = player.opponent.manaCap

        if player.extraTurns > 0:
            player.extraTurns -= 1
        else:
            self.turn = Turn.p2 if self.turn == Turn.p1 else Turn.p1

        self.phase = Phase.startOfTurn
        self.activePlayer.onStartOfTurn()

    def end(self, winner):
        raise EndOfGame(winner)
