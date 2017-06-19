def numericEnum(*items):
    d_items = dict(zip(items, range(0, len(items))))
    d_items['keys'] = items
    return type('NumericEnum', (), d_items)


Turn = numericEnum('p1', 'p2')
Phase = numericEnum('reveal', 'play')
Zone = numericEnum('face', 'faceup', 'facedown', 'hand', 'graveyard')


class IllegalMoveError (Exception):
    pass
