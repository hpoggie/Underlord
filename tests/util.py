from core.player import Player
from core.faction import Faction
from core.core import Game
from core.enums import Turn
import collections


def dummyFactionPlayer(deck):
    class DFP(Player):
        def __init__(self):
            super().__init__(Faction(name="Dummy Faction", deck=list(deck)))

    return DFP


def newGame(*args):
    """
    Helper function for writing cleaner tests.
    Tries to intelligently create a new game from the arguments you give it.
    If you give it 2 lists, it will give the players those lists as decks.
    If you give it one list, it will make that the deck for both players.
    If you give it some cards, it will make those the deck for both players.
    """
    # If we got 2 arguments and at least one of them is a list
    if len(args) == 2 and len(
            [x for x in args if isinstance(x, collections.Iterable)]) > 0:
        # For each of the arguments, if it's a list, make that the player's
        # deck, otherwise make a list containing only that card and make it
        # the player's deck
        players = [dummyFactionPlayer(arg)
                   if isinstance(arg, collections.Iterable)
                   else dummyFactionPlayer([arg]) for arg in args]
        game = Game(*players)
    elif len(args) == 0:
        pl = dummyFactionPlayer([])
        game = Game(pl, pl)
    elif isinstance(args[0], collections.Iterable):
        # if we only got one list, treat that the same as a bunch of cards
        pl = dummyFactionPlayer(args[0])
        game = Game(pl, pl)
    else:
        pl = dummyFactionPlayer(args)
        game = Game(pl, pl)

    # Disable mulligans by default
    game.turn = Turn.p1

    # Return the players for convenience
    return game, game.players[0], game.players[1]
