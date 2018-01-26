def numericEnum(*items):
    d_items = dict(list(zip(items, list(range(len(items))))))
    d_items['keys'] = items
    return type('NumericEnum', (), d_items)


Turn = numericEnum('p1', 'p2')
Phase = numericEnum('reveal', 'play')
