import time
import types
import network


class DummyClient:
    def __init__(self):
        for name in network.ClientNetworkManager.Opcodes.keys:
            setattr(self, name, types.MethodType(lambda self, *args: None, self))


nm = network.ClientNetworkManager(DummyClient(), 'localhost', 9099)
nm.verbose = True
addr = ('localhost', 9099)
nm.connect(addr)
while True:
    s = input().split(' ')
    if s[0] == 'die':
        raise Exception
    elif s[0] != '':
        try:
            nm.send(addr, network.serialize((int(i) for i in s)))
        except ValueError:
            # If we don't have an int, try sending a real opcode
            getattr(nm, s[0])(*[eval(x) for x in s[1:]])

    nm.recv()
