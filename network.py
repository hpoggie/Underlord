from network_manager import NetworkManager
from core.enums import numericEnum


class ServerNetworkManager (NetworkManager):
    def __init__(self, base):
        super().__init__()
        self.base = base

    Opcodes = numericEnum(
        'addPlayer',
        'selectFaction',
        'revealFacedown',
        'playFaceup',
        'attack',
        'play',
        'acceptTarget',
        'endPhase')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode, ", self.Opcodes.keys[opcode])
        getattr(self.base, self.Opcodes.keys[opcode])(addr, *operands)


class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into
    calls to the client.
    """
    def __init__(self, base, ip):
        super().__init__()
        self.base = base
        self.ip = ip

    Opcodes = numericEnum(
        'updateEnemyFaction',
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
        'requestTarget',
        'winGame',
        'loseGame',
        'setActive')

    def onGotPacket(self, packet, addr):
        if packet == '':
            return
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print("got opcode, ", self.Opcodes.keys[opcode])
        getattr(self.base, self.Opcodes.keys[opcode])(*operands)
