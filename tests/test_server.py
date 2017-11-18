import server


svc = server.OverlordService()


addr0 = ('localhost', 99999)
addr1 = ('localhost', 99998)


def testAddTooManyPlayers():
    svc.addPlayer(addr0)
    svc.addPlayer(addr1)
    try:
        svc.addPlayer('localhost')
        assert False
    except server.ServerError:
        pass


def testSelectFaction():
    svc.selectFaction(addr0, 0)
    svc.selectFaction(addr1, 0)
    assert None not in svc.factions
