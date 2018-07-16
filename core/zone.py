from core.game import destroy


class Zone(list):
    def __init__(self, controller, lst=[]):
        super().__init__(lst)
        self.dirty = True

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.dirty = True

    def __delitem__(self, key):
        super().__delitem__(key)
        self.dirty = True

    def append(self, card):
        super().append(card)
        self.dirty = True

    def remove(self, card):
        super().remove(card)
        self.dirty = True

    def destroyAll(self, fltr=lambda c: True):
        for card in [c for c in self if fltr(c)]:
            destroy(card)

    def destroyAllUnits(self):
        self.destroyAll(lambda c: c.isUnit)
