"""
Server script.
Takes the client's actions and computes the results, then sends them back.
"""

import traceback
import random
import time
import inspect

from network_manager import ConnectionClosed
from core.game import Game, EndOfGame
from core.player import IllegalMoveError
from core.enums import numericEnum
from factions.templars import Templar
from factions.mariners import Mariner


class ServerError(BaseException):
    pass


Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


availableFactions = [Templar, Mariner]


def getCard(player, card):
    """
    Convert card to index
    """
    for i, tc in enumerate(player.baseDeck):
        if tc.name == card.name:
            return i


def acceptsTarget(func):
    def converted(self, *args):
        """
        Convert the indices from the netcode to a card ref
        """
        target = None
        addr = args[0]
        pl = self.players[addr]

        # Doesn't include self or target
        nArgs = func.__code__.co_argcount - 2

        try:
            # Assumes the target arg comes last.
            # Also assumes single target
            # TODO: support multiple targets
            targetIndices = args[nArgs:]
            targetZone, targetIndex, targetsEnemy = targetIndices

            if targetsEnemy:
                target = pl.opponent.zones[targetZone][targetIndex]
            else:
                target = pl.zones[targetZone][targetIndex]
        except ValueError:
            # Only got 1 arg.
            func(self, *args)
            return
        except IndexError:
            pass

        func(self, *args[:nArgs], target)

    return converted


class GameServer:
    def __init__(self, netman):
        self.networkManager = netman
        self.networkManager.base = self
        self.addrs = [c.addr for c in self.networkManager.connections]
        self.factions = [None, None]

        for conn in self.networkManager.connections:
            conn.onEnteredGame()

    # actions

    def selectFaction(self, addr, index):
        self.factions[self.addrs.index(addr)] = availableFactions[index]
        # If both players have selected their faction, start the game
        started = hasattr(self, 'game')
        if (None not in self.factions and
                not started and
                not hasattr(self, 'decidingPlayer')):
            # TODO: kludge
            for i in range(len(self.factions)):
                self.networkManager.connections[
                    (i + 1) % len(self.factions)].updateEnemyFaction(
                    availableFactions.index(self.factions[i]))

            self.waitOnGoingFirstDecision()

    def waitOnGoingFirstDecision(self):
        self.decidingPlayer = random.randint(0, 1)
        self.notDecidingPlayer = (self.decidingPlayer + 1) % 2
        conn = self.networkManager.connections[self.decidingPlayer]
        conn.requestGoingFirstDecision()

    def decideWhetherToGoFirst(self, addr, value):
        if self.addrs.index(addr) is not self.decidingPlayer:
            print("That player doesn't get to decide who goes first.")
            return

        if value:
            firstPlayer = self.decidingPlayer
        else:
            firstPlayer = self.notDecidingPlayer

        self.start(firstPlayer)
        del self.decidingPlayer
        del self.notDecidingPlayer

    def start(self, firstPlayer):
        secondPlayer = (firstPlayer + 1) % 2

        self.game = Game(self.factions[firstPlayer],
                         self.factions[secondPlayer])
        self.game.start()
        self.players = dict([
            (self.addrs[firstPlayer], self.game.players[0]),
            (self.addrs[secondPlayer], self.game.players[1])])
        # Make it easy to find connections by addr
        self.connections = dict([
            (addr, self.networkManager.connections[i])
            for i, addr in enumerate(self.addrs)])

        # Add extra data so we can find zones by index
        for pl in self.game.players:
            pl.zones = [
                pl.face,
                pl.faceups,
                pl.facedowns,
                pl.hand,
                pl.graveyard
            ]

        ndp = self.networkManager.connections[self.notDecidingPlayer]
        if firstPlayer == self.decidingPlayer:
            ndp.enemyGoingFirst()
        else:
            ndp.enemyGoingSecond()

        self.redraw()

    def mulligan(self, addr, *indices):
        pl = self.players[addr]
        pl.mulligan(*[pl.hand[index] for index in indices])

        if pl.opponent.hasMulliganed:
            for addr, c in self.connections.items():
                c.updateBothPlayersMulliganed()
            self.redraw()
        else:
            self.connections[addr].updatePlayerHand(
                *(getCard(pl, c) for c in pl.hand))

    @acceptsTarget
    def revealFacedown(self, addr, index, target=None):
        pl = self.players[addr]
        pl.revealFacedown(pl.facedowns[index], target)
        self.redraw()

    @acceptsTarget
    def playFaceup(self, addr, index, target=None):
        pl = self.players[addr]
        pl.playFaceup(pl.hand[index], target)
        self.redraw()

    def attack(self, addr, cardIndex, targetIndex, targetZone):
        pl = self.players[addr]
        attacker = pl.faceups[cardIndex]
        if targetZone == Zone.face:
            target = pl.opponent.face
        else:
            target = pl.opponent.zones[targetZone][targetIndex]

        pl.attack(attacker, target)
        self.redraw()

    def play(self, addr, index):
        pl = self.players[addr]
        pl.play(pl.hand[index])
        self.redraw()

    @acceptsTarget
    def endPhase(self, addr, target=None):
        self.players[addr].endPhase(target)
        self.redraw()

    # TODO: massive kludge
    def fishReplace(self, addr, *cards):
        pl = self.players[addr]
        pl.fishReplace([pl.hand[i] for i in cards])
        self.redraw()

    def redraw(self):
        for addr, pl in self.players.items():
            c = self.connections[addr]
            enemyPlayer = pl.opponent

            c.setActive(int(pl.active))
            c.updatePhase(self.game.phase)

            c.updatePlayerFaceups(*(getCard(pl, c) for c in pl.faceups))
            c.updateEnemyFaceups(
                *(getCard(enemyPlayer, c) for c in enemyPlayer.faceups)
            )

            c.updatePlayerHand(*(getCard(pl, c) for c in pl.hand))
            c.updatePlayerFacedowns(*(getCard(pl, c) for c in pl.facedowns))
            c.updatePlayerManaCap(pl.manaCap)
            c.updatePlayerMana(pl.mana)

            c.updateEnemyHand(len(enemyPlayer.hand))
            c.updateEnemyFacedowns(
                *(getCard(enemyPlayer, c) if c.visibleWhileFacedown else -1
                    for c in enemyPlayer.facedowns)
            )
            c.updateEnemyManaCap(enemyPlayer.manaCap)

    def endGame(self, winner):
        for addr, pl in self.players.items():
            if pl == winner:
                self.connections[addr].winGame()
            else:
                self.connections[addr].loseGame()

    def kickEveryone(self):
        for c in self.networkManager.connections:
            c.kick()

    def run(self):
        while 1:
            try:
                self.networkManager.recv()
            except IndexError as e:
                print(e)
            except IllegalMoveError as e:  # Client sent us an illegal move
                print(e)
            except EndOfGame as e:
                self.endGame(e.winner)
                exit(0)
            except ConnectionClosed as c:
                if c in self.networkManager.connections:
                    self.networkManager.connections.remove(c)
                # If you DC, your opponent wins
                if hasattr(self, 'players'):
                    try:
                        self.endGame(self.players[c.conn.addr].opponent)
                    except BrokenPipeError:  # Opponent also DC'd
                        pass
                else:
                    self.kickEveryone()
                exit(0)
            except Exception as e:  # We died due to some other error
                print(e)
                print(traceback.format_exc())
                self.kickEveryone()
                exit(1)

            time.sleep(0.01)
