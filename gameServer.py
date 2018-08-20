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
from core.exceptions import IllegalMoveError
from core.enums import numericEnum
from factions.templars import Templar
from factions.mariners import Mariner
from factions.thieves import Thief
from factions.fae import Faerie


class ServerError(BaseException):
    pass


Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


availableFactions = [Templar, Mariner, Thief, Faerie]


def getCard(player, card):
    """
    Convert card to index
    """
    def isVisible(c):
        return (c.zone not in (c.controller.hand, c.controller.facedowns)
                or c.visible or c.controller is player)

    return ((card.cardId if isVisible(card) else -1), card.owner is not player)


def getZone(player, zone):
    return [i for c in zone for i in getCard(player, c)]


def ZIEToCard(pl, targetZone, targetIndex, targetsEnemy):
    if targetZone == -1:
        return None

    if targetsEnemy:
        target = pl.opponent.zones[targetZone][targetIndex]
    else:
        target = pl.zones[targetZone][targetIndex]

    return target


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

            target = ZIEToCard(pl, targetZone, targetIndex, targetsEnemy)
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
            self.connections[addr].updatePlayerHand(*getZone(pl, pl.hand))
            self.connections[addr].endRedraw()

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
        pl = self.players[addr]
        if pl.endPhase.__code__.co_argcount > 1:
            pl.endPhase(target)
        else:
            pl.endPhase()
        self.redraw()

    # TODO: massive kludge
    def replace(self, addr, *cards):
        pl = self.players[addr]

        lst = []
        for zone, index, enemy in zip(cards[::3], cards[1::3], cards[2::3]):
            if enemy:
                target = pl.opponent.zones[zone][index]
            else:
                print((zone, index, enemy))
                target = pl.zones[zone][index]
            lst.append(target)

        pl.replace(*lst)
        self.redraw()

    def useThiefAbility(self, addr, discardIndex, guessId, targetIndex):
        pl = self.players[addr]
        pl.thiefAbility(
            pl.hand[discardIndex],
            pl.opponent.__class__.deck[guessId].name,
            pl.opponent.facedowns[targetIndex])
        self.redraw()

    def redraw(self):
        for addr, pl in self.players.items():
            c = self.connections[addr]
            enemyPlayer = pl.opponent

            c.setActive(int(pl.active))
            c.updatePhase(self.game.phase)

            if pl.faceups.dirty:
                c.updatePlayerFaceups(*getZone(pl, pl.faceups))

            for i, card in enumerate(pl.faceups):
                if hasattr(card, 'counter'):
                    c.updatePlayerCounter(i, card.counter)

            c.updateHasAttacked(*(c.hasAttacked for c in pl.faceups))

            if enemyPlayer.faceups.dirty:
                c.updateEnemyFaceups(
                    *getZone(pl, enemyPlayer.faceups))

            for i, card in enumerate(pl.opponent.faceups):
                if hasattr(card, 'counter'):
                    c.updateEnemyCounter(i, card.counter)

            if pl.hand.dirty:
                c.updatePlayerHand(*getZone(pl, pl.hand))
            if pl.facedowns.dirty:
                c.updatePlayerFacedowns(*getZone(pl, pl.facedowns))

            c.updatePlayerManaCap(pl.manaCap)
            c.updatePlayerMana(pl.mana)

            if enemyPlayer.hand.dirty:
                c.updateEnemyHand(*getZone(pl, enemyPlayer.hand))
            if enemyPlayer.facedowns.dirty:
                c.updateEnemyFacedowns(
                    *getZone(pl, enemyPlayer.facedowns))

            c.updateEnemyManaCap(enemyPlayer.manaCap)

            if pl.graveyard.dirty:
                c.updatePlayerGraveyard(*getZone(pl, pl.graveyard))
            if enemyPlayer.graveyard.dirty:
                c.updateEnemyGraveyard(
                    *getZone(pl, pl.opponent.graveyard))

            c.endRedraw()

            if pl.replaceCallback is not None:
                c.requestReplace(pl.replaceCallback.__code__.co_argcount)

        for pl in self.game.players:
            for z in pl.zones:
                z.dirty = False


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
                    except (BrokenPipeError, ConnectionClosed):
                        # Opponent also DC'd
                        pass
                else:
                    try:
                        self.kickEveryone()
                    except (BrokenPipeError, ConnectionClosed):
                        pass
                exit(0)
            except Exception as e:  # We died due to some other error
                print(e)
                print(traceback.format_exc())
                self.kickEveryone()
                exit(1)

            time.sleep(0.01)
