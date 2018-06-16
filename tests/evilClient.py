import time
import types
import network


class DummyClient:
    def __init__(self):
        for name in network.ClientNetworkManager.Opcodes.keys:
            setattr(self, name, types.MethodType(lambda self, *args: None, self))


nm = network.ClientNetworkManager(DummyClient(), 'localhost', 9099)
nm.verbose = True
nm.connect(('localhost', 9099))
while True:
    s = input().split(' ')
    if s[0] != '':
        getattr(nm, s[0])(*[eval(x) for x in s[1:]])

    nm.recv()
