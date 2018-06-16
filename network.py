import types
import re

from network_manager import NetworkManager
from core.enums import numericEnum


def serialize(args):
    return ''.join([{int: 'i', float: 'f', bool: 'b'}[type(x)] +
                    (repr(int(x)) if isinstance(x, bool) else repr(x))
                    for x in args])


def deserialize(packet):
    return [{'i': int, 'f': float, 'b': bool}[s[0]](s[1:])
            for s in re.findall('[a-z][^a-z]*', packet)]


class ServerNetworkManager (NetworkManager):
    def __init__(self, base):
        super().__init__()
        self.startServer()
        self.base = base

    Opcodes = numericEnum(
        'requestNumPlayers',
        'addPlayer',
        'decideWhetherToGoFirst',
        'selectFaction',
        'mulligan',
        'revealFacedown',
        'playFaceup',
        'attack',
        'play',
        'endPhase',
        'fishReplace')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return

        try:
            operands = deserialize(packet)
        except KeyError:
            print("Got malformed packet: " + packet)
            return

        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode: ", self.Opcodes.keys[opcode])

        try:
            getattr(self.base, self.Opcodes.keys[opcode])(addr, *operands)
        except AttributeError as e:
            print(e)

    def onClientConnected(self, conn):
        # Make it so each client opcode is a function
        for i, key in enumerate(ClientNetworkManager.Opcodes.keys):
            class OpcodeFunc:
                def __init__(self, manager, opcode):
                    self.manager = manager
                    self.opcode = opcode

                def __call__(self, base, *args):
                    self.manager.send(
                        base.addr,
                        serialize([self.opcode] + list(args)))

            # Bind the OpcodeFunc as a method to the class
            setattr(conn, key, types.MethodType(OpcodeFunc(self, i), conn))

        self.base.onClientConnected(conn)


class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into
    calls to the client.
    """
    def __init__(self, base, ip, port):
        super().__init__()
        self.base = base
        self.ip = ip
        self.port = port

        # Make it so each server opcode is a function
        for i, key in enumerate(ServerNetworkManager.Opcodes.keys):
            class OpcodeFunc:
                def __init__(self, opcode):
                    self.opcode = opcode

                def __call__(self, base, *args):
                    base.send(
                        (base.ip, base.port),
                        serialize([self.opcode] + list(args)))

            # Bind the OpcodeFunc as a method to the class
            setattr(self, key, types.MethodType(OpcodeFunc(i), self))

    Opcodes = numericEnum(
        'onEnteredGame',
        'requestGoingFirstDecision',
        'updateNumPlayers',
        'updateEnemyFaction',
        'enemyGoingFirst',
        'enemyGoingSecond',
        'updateBothPlayersMulliganed',
        'updatePlayerHand',
        'updateEnemyHand',
        'updatePlayerFacedowns',
        'updateEnemyFacedowns',
        'updatePlayerFaceups',
        'updateEnemyFaceups',
        'updatePlayerGraveyard',
        'updateEnemyGraveyard',
        'updatePlayerManaCap',
        'updatePlayerMana',
        'updateEnemyManaCap',
        'updatePhase',
        'updatePlayerCounter',
        'updateEnemyCounter',
        'winGame',
        'loseGame',
        'setActive',
        'kick')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return

        try:
            operands = deserialize(packet)
        except KeyError:
            print("Got malformed packet: " + packet)
            return

        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode: ", self.Opcodes.keys[opcode])

        try:
            getattr(self.base, self.Opcodes.keys[opcode])(*operands)
        except AttributeError as e:
            print(e)
