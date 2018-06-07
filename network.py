import types

from network_manager import NetworkManager
from core.enums import numericEnum
from core.decision import Decision


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
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode: ", self.Opcodes.keys[opcode])

        getattr(self.base, self.Opcodes.keys[opcode])(addr, *operands)

    def onClientConnected(self, conn):
        # Make it so each client opcode is a function
        for i, key in enumerate(ClientNetworkManager.Opcodes.keys):
            class OpcodeFunc:
                def __init__(self, manager, opcode):
                    self.manager = manager
                    self.opcode = opcode

                def __call__(self, base, *args):
                    self.manager.sendInts(
                        base.addr,
                        self.opcode,
                        *args)

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
                    base.sendInts(
                        (base.ip, base.port),
                        self.opcode,
                        *args)

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
        'updatePlayerManaCap',
        'updatePlayerMana',
        'updateEnemyManaCap',
        'updatePhase',
        'winGame',
        'loseGame',
        'setActive',
        'kick')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode: ", self.Opcodes.keys[opcode])
        getattr(self.base, self.Opcodes.keys[opcode])(*operands)
