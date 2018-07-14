def deck(*args):
    deck = []

    for i, arg in enumerate(args):
        if hasattr(arg, '__call__'):
            if i + 1 < len(args) and isinstance(args[i + 1], int):
                deck += [arg() for i in range(args[i + 1])]
            else:
                deck.append(arg())

    return deck
