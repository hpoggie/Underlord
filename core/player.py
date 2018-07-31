"""
Player class.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import randint

from core.game import Phase
from core.zone import Zone
from core.exceptions import IllegalMoveError

startHandSize = 5
maxManaCap = 15


class Player:
    iconPath = "./my_faction_icons"
    cardBack = "my-faction-back.png"

    def __init__(self):
        self.hand = Zone(self)
        self.facedowns = Zone(self)
        self.faceups = Zone(self)
        # Need to have a dummy zone to attack
        self.face = Zone(self, ["A human face."])
        self.deck = Zone(self, deepcopy(self.deck))  # deck is initially a class var

        self.graveyard = Zone(self)
        self._manaCap = 1
        self.mana = 1

        self.hasMulliganed = False
        self.hasFirstPlayerPenalty = False

        self.referenceDeck = self.deck[:]
        for i, card in enumerate(self.deck):
            card.owner = self
            card._zone = self.deck
            card.cardId = i

        # Add extra data so we can find zones by index
        self.zones = [
            self.face,
            self.faceups,
            self.facedowns,
            self.hand,
            self.graveyard
        ]

        # Counter for "Take an extra turn after this one" effects
        self.extraTurns = 0

        # Callback for effects that require replacing cards
        self.replaceCallback = None

        # Stack for forced actions (see push() and pop())
        self.actionStack = []

    def __repr__(self):
        if hasattr(self, 'game'):
            return "Player %d" % self.game.players.index(self)
        else:
            return "Player at 0x%x" % id(self)

    @property
    def baseDeck(self):
        return self.__class__.deck

    @property
    def manaCap(self):
        return self._manaCap

    @manaCap.setter
    def manaCap(self, value):
        self._manaCap = value
        if self._manaCap > 15:
            self.opponent.win()

    def shuffle(self):
        self.deck.shuffle()

    def drawOpeningHand(self):
        for i in range(0, startHandSize):
            self.drawCard()

    def onStartOfTurn(self):
        self.endPhase()

    def drawCard(self):
        if len(self.deck) != 0:
            self.deck[-1].zone = self.hand

    def drawCards(self, n):
        for i in range(n):
            self.drawCard()

    def drawTo(self, n):
        while len(self.hand) < n  and len(self.deck) > 0:
            self.drawCard()

    def topdeck(self, cards):
        """
        Put the cards on top of the player's deck.
        The first one in the list will be drawn last.
        """
        for card in cards:
            card._zone.remove(card)
            card._zone = self.deck

        self.deck[:] = self.deck + cards

    def bottomdeck(self, cards):
        """
        Put the cards on the bottom of the player's deck.
        The first one in the list will be drawn last.
        """
        for card in cards:
            card._zone.remove(card)
            card._zone = self.deck

        self.deck[:len(cards)], self.deck[len(cards):] = cards, self.deck[:]

    def discardRandom(self):
        try:
            idx = randint(0, len(self.hand) - 1)
            self.hand[idx].zone = self.graveyard
        except ValueError:  # Do nothing if you have no cards
            pass

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

    def replace(self, *cards):
        if self.replaceCallback is None:
            raise IllegalMoveError("No effect to replace for.")
        else:
            self.replaceCallback(*cards)
            self.replaceCallback = None
            self.popAction()

    def pushAction(self, func):
        """
        Push an action onto the stack
        This is useful for requiring things to happen after targetCallback
        is called
        """
        self.actionStack.append(func)

    def popAction(self):
        """
        Pop actions off the stack until we get a decision or it's empty
        """
        try:
            func = self.actionStack.pop()
        except IndexError:
            pass
        else:
            if func.__code__.co_argcount > 0:
                self.replaceCallback = func
            else:
                func()
                self.popAction()

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

        if self.replaceCallback is not None:
            raise IllegalMoveError(
                "Must replace cards from effect first.")

    def play(self, card):
        self.failIfInactive()

        # Overload
        if isinstance(card, int):
            card = self.hand[card]

        if self.game.phase != Phase.play:
            raise IllegalMoveError("""
            Can only play facedowns during play phase.""")

        if card.zone != self.hand:
            raise IllegalMoveError(
                "Can't play %s because it's not in your hand." % repr(card))

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

        card.cast(*args, **kwargs)

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

        if not card.fast:
            raise IllegalMoveError("That card can't be played face-up.")

        if self.mana < card.cost:
            raise IllegalMoveError("Not enough mana.")

        card.cast(*args, **kwargs)

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
                target.controller.faceups, target.controller.facedowns]:
            raise IllegalMoveError(
                "Can only attack face-up / face-down targets or a player.")

        attacker.attack(target)

    def attackFacedown(self, attacker, targetIndex):
        self.attack(attacker, self.opponent.facedowns[targetIndex])

    def attackFaceup(self, attacker, targetIndex):
        self.attack(attacker, self.opponent.faceups[targetIndex])

    def attackFace(self, attacker):
        self.attack(attacker, self.opponent.face)

    def endPhase(self):
        self.failIfInactive()
        self.game.endPhase()

    def endTurn(self, *args, **kwargs):
        self.failIfInactive()
        while self.active:
            self.endPhase(*args, **kwargs)

    def takeExtraTurn(self):
        self.extraTurns += 1
