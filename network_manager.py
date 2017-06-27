import socket
import struct
import select


class Connection (object):
    def __init__(self, conn, addr):
        self.conn, self.addr = conn, addr
        self.buffer = ''


class NetworkManager (object):
    def __init__(self):
        self.ip = "127.0.0.1"
        self.port = 9099
        self.bufsize = 1024

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # internet, tcp
        self.connections = []
        self.isClient = False

        self.verbose = False

    def startServer(self):
        self.sock.bind(("", self.port))
        self.sock.listen(2)
        self.connections = [
                Connection(*self.sock.accept()),
                Connection(*self.sock.accept())]
        if self.verbose: print "got 2 players. starting"
        self.sock.setblocking(0)

    def connect(self, addr):
        self.sock.connect(addr)
        self.connections = [Connection(self.sock, addr)]
        self.isClient = True
        self.sock.setblocking(0)

    def send(self, data, target):
        packet = str(data) + '\0'

        if self.verbose:
            print "Sent packet " + packet + " to ", target

        if self.isClient:
            self.sock.sendall(packet)
        else:
            next(x for x in self.connections if x.addr == target).conn.sendall(packet)

    def sendInts(self, target, *args):
        self.send(":".join(str(x) for x in args), target)

    def recv(self):
        readers, writers, errors = select.select(
                [c.conn for c in self.connections], [], [], 0)

        for conn in readers:
            c = next(x for x in self.connections if x.conn == conn)
            newData = c.conn.recv(self.bufsize)
            c.buffer += newData
            data = c.buffer.split('\0')
            c.buffer = data[-1]
            data = data[:-1]

            for d in data:
                self.onGotPacket(d,
                        next(x for x in self.connections if x.conn == conn).addr)

    def onGotPacket(self, packet, addr):
        print packet
