import inspect


class Decision(BaseException):
    """
    An effect that requires a decision from a player.

    Called just like a regular ability, but becomes the player's active ability
    instead of immediately executing. Then the player can execute it after
    getting targets.
    """
    def __init__(self, func, source, desc=""):
        self.source = source
        # TODO: support multiple targets
        self.numArgs = len(inspect.getargspec(func).args)
        self.func = func
        self.desc = desc

    def __call__(self):
        raise self

    def execute(self, *args, **kwargs):
        self.func(*args, **kwargs)
