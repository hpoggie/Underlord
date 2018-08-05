from direct.interval.IntervalGlobal import Sequence, Func


def animateMove(card, zone, duration):
    card.wrtReparentTo(card.get_top())
    Sequence(
        card.posInterval(duration / 2, zone.getPos(card.get_top())),
        Func(lambda: card.wrtReparentTo(zone))).start()
