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
        pls = {p.addr: p for p in base.players}
        if operands[0] == Opcodes.connect:
            base.addPlayer(addr)
        elif operands[0] == Opcodes.revealFacedown:
            pls[addr].revealFacedown(operands[1])
        elif operands[0] == Opcodes.playFaceup:
            pls[addr].playFaceup(operands[1])
        elif operands[0] == Opcodes.attack:
            pls[addr].attack(operands[1], operands[2], operands[3])
        elif operands[0] == Opcodes.playCard:
            pls[addr].play(operands[1])
        elif operands[0] == Opcodes.acceptTarget:
            pls[addr].acceptTarget(operands[1])
        elif operands[0] == Opcodes.endPhase:
            if not pls[addr].isActivePlayer():
                print "It is not your turn."
            else:
                base.endPhase(addr)
