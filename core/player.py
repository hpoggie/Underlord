"""
Player class.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import shuffle
from core.decision import Decision

from core.game import Phase

startHandSize = 5
maxManaCap = 15


class IllegalMoveError (Exception):
    pass


class Player:
    def __init__(self, faction):
        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.face = ["A human face."]  # Need to have a dummy zone to attack
        self.faction = faction
        self.deck = deepcopy(faction.deck)
        for card in self.deck:
            card.owner = self
            card._zone = self.deck
        self.graveyard = []
        self._manaCap = 1
        self.mana = 1

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        self.hasMulliganed = False
        self.hasFirstPlayerPenalty = False

    def __repr__(self):
        if hasattr(self, 'game'):
            return "Player %d" % self.game.players.index(self)
        else:
            return "Player at 0x%x" % id(self)

    @property
    def manaCap(self):
        return self._manaCap

    @manaCap.setter
    def manaCap(self, value):
        self._manaCap = value
        if self._manaCap > 15:
            self.opponent.win()

    def shuffle(self):
        shuffle(self.deck)

    def drawOpeningHand(self):
        for i in range(0, startHandSize):
            self.drawCard()

    def drawCard(self):
        if len(self.deck) != 0:
            self.deck[-1].zone = self.hand

    @property
    def active(self):
        return self.game.activePlayer == self

    @property
    def opponent(self):
        index = 1 if self.game.players[0] == self else 0
        return self.game.players[index]

    def getCard(self, zone, index):
        return zone[index]

    def win(self):
        self.game.end(winner=self)

    # Actions

    def mulligan(self, *cards):
        cards = set(cards)  # Remove duplicates

        if self.hasMulliganed:
            raise IllegalMoveError("Can't mulligan twice.")

        if self.game.turn is not None:
            raise IllegalMoveError(
                "Can only mulligan before the game has started.")

        for i in range(len(cards)):
            self.drawCard()
        for c in cards:
            c.zone = self.deck
        self.shuffle()

        self.hasMulliganed = True
        if self.opponent.hasMulliganed:
            self.game.finishMulligans()

    def failIfInactive(self, *args):
        if not self.active:
            raise IllegalMoveError("It is not your turn.")

    def play(self, card):
        self.failIfInactive()

        # Overload
        if isinstance(card, int):
            card = self.hand[card]

        if self.game.phase != Phase.play:
            raise IllegalMoveError("""
            Can only play facedowns during play phase.""")

        if card.zone != self.hand:
            raise IllegalMoveError("""
            Can't play a card that's not in your hand.""")

        card.zone = self.facedowns
        card.hasAttacked = False

    def revealFacedown(self, card, *args, **kwargs):
        self.failIfInactive()

        # Overload
        if isinstance(card, int):
            card = self.facedowns[card]

        if self.game.phase != Phase.reveal:
            raise IllegalMoveError("""
            Can only reveal facedowns during reveal phase.""")

        if self.mana < card.cost:
            raise IllegalMoveError("Not enough mana. (cost %d; mana %d)"
                                   % (card.cost, self.mana))

        if card.zone != self.facedowns:
            raise IllegalMoveError("Can't reveal a card that's not face-down.")

        try:
            card.cast()
        except Decision as d:
            d.execute(*args, **kwargs)

    def playFaceup(self, card, *args, **kwargs):
        self.failIfInactive()

        # Overload
        if isinstance(card, int):
            card = self.hand[card]

        if self.game.phase != Phase.reveal:
            raise IllegalMoveError("""
                    Can only play faceups during reveal phase.""")

        if card not in self.hand:
            raise IllegalMoveError("""
                    Can't play a card face-up that's not in hand.""")

        if not card.playsFaceUp:
            raise IllegalMoveError("That card does not play face-up.")

        if self.mana < card.cost:
            raise IllegalMoveError("Not enough mana.")

        try:
            card.cast()
        except Decision as d:
            d.execute(*args, **kwargs)

    def attack(self, attacker, target):
        self.failIfInactive()

        # Overload
        if isinstance(attacker, int):
            attacker = self.faceups[attacker]

        if attacker.hasAttacked:
            raise IllegalMoveError("Can only attack once per turn.")

        if self.game.phase != Phase.play:
            raise IllegalMoveError("Can only attack during attack phase.")

        if attacker.zone != self.faceups:
            raise IllegalMoveError("Can only attack with face-up cards.")

        taunts = [c for c in self.opponent.faceups if c.taunt]
        if len(taunts) > 0 and target not in taunts:
            raise IllegalMoveError("Must attack units with taunt first.")

        if target != self.opponent.face and target.zone not in [
                target.owner.faceups, target.owner.facedowns]:
            raise IllegalMoveError(
                "Can only attack face-up / face-down targets or a player.")

        attacker.hasAttacked = True

        if target == self.face:
            self.attackFace(attacker)
        else:
            self.game.fight(target, attacker)

    def attackFacedown(self, attacker, targetIndex):
        self.attack(attacker, self.opponent.facedowns[targetIndex])

    def attackFaceup(self, attacker, targetIndex):
        self.attack(attacker, self.opponent.faceups[targetIndex])

    def attackFace(self, attacker):
        self.failIfInactive()

        # Overload
        if isinstance(attacker, int):
            attacker = self.faceups[attacker]

        self.opponent.manaCap += attacker.rank

    def endPhase(self, *args, **kwargs):
        self.failIfInactive()
        try:
            self.game.endPhase()
        except Decision as d:
            d.execute(*args, **kwargs)

    def endTurn(self, *args, **kwargs):
        self.failIfInactive()
        while self.active:
            self.endPhase(*args, **kwargs)
