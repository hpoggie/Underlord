from network_manager import NetworkManager
from core.enums import numericEnum


class ServerNetworkManager (NetworkManager):
    def __init__(self, base):
        super(ServerNetworkManager, self).__init__()
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
        base = self.base
        Opcodes = self.__class__.Opcodes
        operands = [int(x) for x in packet.split(":")]
        (opcode, operands) = (operands[0], operands[1:])
        if self.verbose:
            print "got opcode, ", Opcodes.keys[opcode]
        getattr(base, Opcodes.keys[opcode])(addr, *operands)

class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into calls to the client.
    """
    def __init__(self, base, ip):
        super(ClientNetworkManager, self).__init__()
        self.base = base
        self.ip = ip

    Opcodes = numericEnum(
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
        'win',
        'lose',
        'setActive'
        )

    def onGotPacket(self, packet, addr):
        base = self.base
        Opcodes = self.Opcodes
        segments = [int(x) for x in packet.split(":")]
        if self.verbose:
            print "got opcode, ", segments[0]
        if segments[0] == Opcodes.updatePlayerHand:
            base.updatePlayerHand(segments[1:])
        elif segments[0] == Opcodes.updateEnemyHand:
            base.updateEnemyHand(segments[1])
        elif segments[0] == Opcodes.updatePlayerFacedowns:
            base.updatePlayerFacedowns(segments[1:])
        elif segments[0] == Opcodes.updateEnemyFacedowns:
            base.updateEnemyFacedowns(segments[1])
        elif segments[0] == Opcodes.updatePlayerFaceups:
            base.updatePlayerFaceups(segments[1:])
        elif segments[0] == Opcodes.updateEnemyFaceups:
            base.updateEnemyFaceups(segments[1:])
        elif segments[0] == Opcodes.updatePlayerManaCap:
            base.updatePlayerManaCap(segments[1])
        elif segments[0] == Opcodes.updatePlayerMana:
            base.updatePlayerMana(segments[1])
        elif segments[0] == Opcodes.updateEnemyManaCap:
            base.updateEnemyManaCap(segments[1])
        elif segments[0] == Opcodes.updatePhase:
            base.phase = segments[1]
        elif segments[0] == Opcodes.requestTarget:
            base.getTarget(segments[1], segments[2])
        elif segments[0] == Opcodes.win:
            base.winGame()
        elif segments[0] == Opcodes.lose:
            base.loseGame()
        elif segments[0] == Opcodes.setActive:
            base.active = bool(segments[1])
