from .util import newGame
from core.exceptions import IllegalMoveError
from core.game import Game, Turn, Phase
import factions.templars as templars


def testTemplarAbility():
    game = Game(templars.Templar, templars.Templar)
    p0 = game.players[0]
    p1 = game.players[1]
    game.start()
    # empty mulligans
    p0.mulligan()
    p1.mulligan()

    p0.endTurn(p0.hand[0])

    assert len(p0.hand) == 4  # First player penalty
    assert p0.manaCap == 3

    p1.endTurn(None)

    assert len(p1.hand) == 6
    assert p1.manaCap == 2

    # Try discarding something not in your hand
    p0.endTurn(p1.hand[0])
    assert len(p1.hand) == 6
    assert p0.manaCap == 4


def testEquus():
    game, p0, p1 = newGame(templars.equus())
    p0.deck[0].zone = p0.faceups
    p0.manaCap = 3
    assert p0.faceups[0].rank == 5
    p0.manaCap = 4
    assert p0.faceups[0].rank == 2


def testHolyHandGrenade():
    game, p0, p1 = newGame(
        [templars.corvus(), templars.corvus()],
        [templars.holyHandGrenade(), templars.holyHandGrenade()])
    p0.mana = 5
    p0.drawCard()
    p0.hand[0].fast = True
    p0.playFaceup(p0.hand[0])
    p0.endPhase()
    p0.play(p0.hand[0])
    p0.endTurn()
    p1.mana = 8
    p1.drawCard()
    p1.drawCard()

    p1.playFaceup(p1.hand[0], p0.facedowns[0])
    assert len(p0.facedowns) == 0

    p1.playFaceup(p1.hand[0], p0.faceups[0])
    assert len(p0.facedowns) == 0


def testWrathOfGod():
    game, p0, p1 = newGame(
        [templars.corvus(), templars.corvus()],
        [templars.wrathOfGod()])
    p0.drawCard()
    p0.drawCard()
    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.hand[1].fast = True
    p0.hand[1].cost = 0
    p0.playFaceup(p0.hand[0])
    p0.playFaceup(p0.hand[0])
    p0.endTurn()
    p1.drawCard()
    p1.hand[0].cost = 0
    p1.playFaceup(p1.hand[0])
    assert len(p0.faceups) == 0


def testMiracle():
    game, p0, p1 = newGame(
        [templars.corvus() for i in range(6)] + [templars.miracle()])
    p0.drawCard()
    assert len(p0.hand) == 1
    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(p0.hand[0])
    assert len(p0.hand) == 5


def testMiracleNotEnoughCards():
    game, p0, p1 = newGame(
        templars.corvus(),
        templars.corvus(),
        templars.miracle()
    )
    p0.drawCard()
    assert len(p0.hand) == 1
    p0.hand[0].fast = True
    p0.hand[0].cost = 0
    p0.playFaceup(p0.hand[0])
    assert len(p0.hand) == 2


def testGrail():
    game, p0, p1 = newGame()
    c = templars.leftGrail()
    c.owner = p0
    c.zone = p0.faceups
    c = templars.corvus()
    c.owner = p1
    c.zone = p1.faceups
    p1.faceups[0].hasAttacked = False
    game.turn = Turn.p2
    game.phase = Phase.play
    # Should fail if attack works
    try:
        p1.attack(p1.faceups[0], p0.face)
        assert False
    except IllegalMoveError:
        pass


def testCrystalElemental():
    game, p0, p1 = newGame(
        [templars.crystalElemental()],
        [templars.corvus()])

    # Cheat the elemental into play
    p0.drawCard()
    p0.hand[0].fast = True
    p0.mana = templars.crystalElemental().cost
    p0.playFaceup(p0.hand[0])
    p0.endTurn()

    p1.endPhase()  # Draws the card
    p1.play(p1.hand[0])  # Play the card face-down
    p1.endTurn()

    p0.endPhase()
    assert(len(p0.hand) == 0)

    # give them a card to draw
    c = templars.crystalElemental()
    c.owner = p0  # Need to have an owner or can't switch zones
    p0.deck.append(c)

    p0.attack(p0.faceups[0], p1.facedowns[0])
    assert(len(p0.hand) == 1)
