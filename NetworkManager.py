import socket, struct

class NetworkManager:
    ip = "127.0.0.1"
    port = 9099
    bufsize = 1024

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #internet, udp
    sock.setblocking(0)

    unreceivedPackets = [] # all packets we sent that have not yet been received
    currentId = 0 #the largest currently unallocated id

    lastReceivedPackets = dict()
    savedPackets = [] #out of order packets saved for later

    verbose = False

    def startServer (self):
        self.sock.bind(("", self.port))

    def send (self, data, target):
        packet = str(data) + " " +str(self.currentId)
        self.sock.sendto(packet, target)
        self.unreceivedPackets.append((packet, target))
        self.currentId += 1

    def popSavedPackets (self):
        while len(self.savedPackets) > 0:
            foundPacket = False
            for p in self.savedPackets:
                data, num = p[0].split(" ")
                num = int(num)
                if num == self.lastReceivedPackets[p[1]] + 1:
                    if self.verbose: print "Using saved packet ", num
                    self.lastReceivedPackets[p[1]] = num
                    self.onGotPacket(data, p[1])
                    self.savedPackets.remove(p)
                    foundPacket = True
            if foundPacket == False: return

    def recv (self):
        try:
            data, addr = self.sock.recvfrom(self.bufsize)
        except socket.error:
            return

        try:
            lastReceivedPacket = self.lastReceivedPackets[addr]
        except KeyError:
            self.lastReceivedPackets[addr] = -1
            lastReceivedPacket = -1

        string, recId = data.split(" ")
        recId = int(recId)

        if recId == -1: #packet was a response
            if self.verbose: print "Got response for packet ", string
            for packet in self.unreceivedPackets:
                if packet[0].split(" ")[1] == string: self.unreceivedPackets.remove(packet)
        elif recId == lastReceivedPacket + 1: #actual data
            if self.verbose: print "Got packet ", recId
            self.lastReceivedPackets[addr] = recId
            self.sock.sendto(str(recId) + " -1", addr)#send back the id
            self.onGotPacket(string, addr)
            self.popSavedPackets()
        elif recId > lastReceivedPacket + 1: # out of order
            if self.verbose: print "Saving out of order packet ", recId
            self.savedPackets.append((data, addr))
        else:
            if self.verbose: print "Got duplicate packet ", recId
            self.sock.sendto(str(recId) + " -1", addr)#send back the id

    def update (self):
        self.recv()
        for p in self.unreceivedPackets:
            self.sock.sendto(p[0], p[1])

    def onGotPacket (self, packet, addr):
        print packet
