from network_manager import NetworkManager


class ServerNetworkManager (NetworkManager):
    def __init__(self, base):
        super(ServerNetworkManager, self).__init__()
        self.base = base

    class Opcodes:
        connect = 0
        revealFacedown = 1
        playFaceup = 2
        attack = 3
        playCard = 4
        acceptTarget = 5
        endPhase = 6

    def onGotPacket(self, packet, addr):
        base = self.base
        Opcodes = self.__class__.Opcodes
        operands = [int(x) for x in packet.split(":")]
        if self.verbose:
            print "got opcode, ", operands[0]
        if operands[0] == Opcodes.connect:
            base.addPlayer(addr)
        elif operands[0] == Opcodes.revealFacedown:
            base.revealFacedown(addr, operands[1])
        elif operands[0] == Opcodes.playFaceup:
            base.playFaceup(addr, operands[1])
        elif operands[0] == Opcodes.attack:
            base.attack(addr, operands[1], operands[2], operands[3])
        elif operands[0] == Opcodes.playCard:
            base.play(addr, operands[1])
        elif operands[0] == Opcodes.acceptTarget:
            base.acceptTarget(addr, operands[1], operands[2], operands[3])
        elif operands[0] == Opcodes.endPhase:
            base.endPhase(addr)


class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into calls to the client.
    """
    def __init__(self, base, ip):
        super(ClientNetworkManager, self).__init__()
        self.base = base
        self.ip = ip

    class Opcodes:
        updatePlayerHand = 0
        updateEnemyHand = 1
        updatePlayerFacedowns = 2
        updateEnemyFacedowns = 3
        updatePlayerFaceups = 4
        updateEnemyFaceups = 5
        updatePlayerManaCap = 6
        updateEnemyManaCap = 7
        updatePhase = 8
        requestTarget = 9
        win = 10
        lose = 11
        setActive = 12

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
