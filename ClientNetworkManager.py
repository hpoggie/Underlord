from NetworkManager import NetworkManager


class ClientNetworkManager (NetworkManager):
    """
    The ClientNetworkManager takes incoming network opcodes and turns them into calls to the client.
    """
    base = None

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
