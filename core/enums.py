def numericEnum(*items):
    return type('NumericEnum', (), dict(zip(items, range(0, len(items)))))


Turn = numericEnum('p1', 'p2')
Phase = numericEnum('reveal', 'play')
Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


class IllegalMoveError (Exception):
    pass
