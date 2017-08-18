import sys


class FloatParameter:
    """ Float with tracking. initial value and bounds.

    """
    def __init__(self, initial, bounds=None, fixed=False):
        bounds = bounds or (-sys.float_info.max, sys.float_info.max)
        self.current = float(initial)
        self._bounds = [float(_) for _ in bounds]
        self.computed = None
        self._fixed = fixed

    @property
    def fixed(self):
        return self._fixed or self.computed != None

    @property
    def bounds(self):
        return self._bounds

    def __float__(self):
        if self.computed:
            return self.computed()
        return self.current

    def __str__(self):
        return str(self.current)
