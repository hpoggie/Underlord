from . import util
from . import dummyCards
import core.player
from core.player import Player, IllegalMoveError
from factions.templars import Templar
import factions.base


def deckContainsDuplicates(deck):
    for i, card in enumerate(deck):
        for card2 in deck[i + 1:]:
            if card == card2:
                return True
    return False


def testForDuplicates():
    player = Templar()
    assert not deckContainsDuplicates(player.deck)


def testForDuplicatesBetweenPlayers():
    player1 = Templar()
    player2 = Templar()

    for card1 in player1.deck:
        for card2 in player2.deck:
            assert card1 != card2


def testReveal():
    game, player, p1 = util.newGame(dummyCards.one())
    player.endPhase()  # draw the card
    newCard = player.hand[0]
    player.play(newCard)
    player.endPhase()
    p1.endTurn()
    player.revealFacedown(newCard)
    assert newCard.zone == player.faceups


def testPlay():
    game, player, _ = util.newGame(dummyCards.one())
    player.endPhase()
    newCard = player.hand[0]
    player.play(newCard)
    assert newCard.zone == player.facedowns


def testPlayFaceup():
    newCard = dummyCards.one()
    newCard.fast = True
    newCard.cost = 0
    game, player, _ = util.newGame(newCard)
    player.drawCard()
    instance = player.hand[0]
    player.playFaceup(instance)
    assert instance.zone == player.faceups


def testAttackFace():
    newCard = dummyCards.one()
    newCard.fast = True
    newCard.cost = 0
    game, player, _ = util.newGame(newCard)
    player.drawCard()
    player.playFaceup(player.hand[0])
    player.endPhase()
    player.attackFace(player.faceups[0])
    assert game.players[1].manaCap == 2


def testAttackFacedown():
    newCard = dummyCards.one()
    newCard.fast = True
    newCard.cost = 0
    game, p0, p1 = util.newGame(newCard)
    game.start()
    # 1st player plays a facedown
    p0.endPhase()
    p0.play(game.players[0].hand[0])
    p0.endTurn()
    # 2nd player attacks it
    p1.playFaceup(p1.hand[0])
    p1.endPhase()
    p1.attack(p1.faceups[0], p0.facedowns[0])
    assert len(p0.facedowns) == 0
    assert len(p1.faceups) == 0


def testAttackFaceup():
    newCard = dummyCards.one()
    newCard.fast = True
    newCard.cost = 0
    game, p0, p1 = util.newGame(newCard)
    game.start()
    # 1st player plays a faceup
    p0.playFaceup(p0.hand[0])
    p0.endTurn()
    # 2nd player attacks it
    p1.playFaceup(p1.hand[0])
    p1.endPhase()
    p1.attack(p1.faceups[0], p0.faceups[0])
    assert len(p0.facedowns) == 0
    assert len(p1.faceups) == 0


def testMulligan():
    from copy import deepcopy

    game, p0, p1 = util.newGame([dummyCards.one() for i in range(40)])
    game.start()
    game.turn = None
    hand0 = deepcopy(p0.hand)
    assert len(hand0) == core.player.startHandSize
    c = p0.hand[0]
    p0.mulligan(c)
    hand1 = deepcopy(p0.hand)
    assert len(hand1) == core.player.startHandSize
    assert hand0 != hand1

    assert c in p0.deck  # Has the card been returned to the deck

    # Can't mulligan twice
    try:
        p0.mulligan(p0.hand[0])
        assert False
    except IllegalMoveError:
        pass


def testActionsWithIndices():
    game, p0, p1 = util.newGame([dummyCards.one() for i in range(40)])
    game.start()

    print(p0.hand)
    p0.hand[0].fast = True  # Cheat
    p0.playFaceup(0)
    p0.endPhase()
    p0.play(0)
    p0.attackFace(0)
    p0.endPhase()

    p1.endPhase()
    p1.play(0)
    p1.endPhase()

    p0.revealFacedown(0)
    p0.endPhase()
    p0.attackFacedown(0, 0)


def testRepr():
    """
    Make sure repr() isn't broken
    """
    t = Templar()
    print(repr(t.deck))


def testRequiresTarget():
    assert factions.base.spellBlade().requiresTarget
    assert not factions.base.sweep().requiresTarget


def testZoneLists():
    game, p0, p1 = util.newGame()

    for z in p0.zones:
        assert z not in p1.zones
