from NetworkManager import NetworkManager


class ServerNetworkManager (NetworkManager):
    base = None

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
