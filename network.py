import types
import re

from network_manager import NetworkManager
from core.enums import numericEnum


class OpcodeError(Exception):
    pass


def serialize(args):
    return ''.join([{int: 'i', float: 'f', bool: 'b'}[type(x)] +
                    (repr(int(x)) if isinstance(x, bool) else repr(x))
                    for x in args])


def deserialize(packet):
    return [{'i': int, 'f': float, 'b': bool}[s[0]](int(s[1:]))
            for s in re.findall('[a-z][^a-z]*', packet)]


class ULNetworkManager(NetworkManager):
    def tryCall(self, key, args):
        if not hasattr(self.base, key):
            raise OpcodeError("Opcode not found: " + key)

        getattr(self.base, key)(*args)

    def tryFindKey(self, opcode):
        try:
            return self.Opcodes.keys[opcode]
        except IndexError:
            raise OpcodeError("Invalid index: " + str(opcode))


class ServerNetworkManager (ULNetworkManager):
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
        'replace',
        'useThiefAbility')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return

        try:
            operands = deserialize(packet)
        except KeyError:
            print("Got malformed packet: " + packet)
            return

        (opcode, operands) = (operands[0], operands[1:])

        key = self.tryFindKey(opcode)

        if self.verbose:
            print("got opcode: ", key)

        self.tryCall(key, [addr] + operands)

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


class ClientNetworkManager (ULNetworkManager):
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
        'updateHasAttacked',
        'updateEnemyFaceups',
        'updatePlayerGraveyard',
        'updateEnemyGraveyard',
        'updatePlayerManaCap',
        'updatePlayerMana',
        'updateEnemyManaCap',
        'updatePhase',
        'updatePlayerCounter',
        'updateEnemyCounter',
        'requestReplace',
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

        key = self.tryFindKey(opcode)

        if self.verbose:
            print("got opcode ", key + " with args " + str(operands))

        self.tryCall(key, operands)
