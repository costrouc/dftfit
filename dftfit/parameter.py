import sys


class FloatParameter:
    """ Float with tracking. initial value and bounds.

    """
    def __init__(self, initial, bounds=(-sys.float_info.max, sys.float_info.max), computed=None):
        self.initial = float(initial)
        self.current = float(initial)
        self.bounds = [float(_) for _ in bounds]
        self.computed = computed

    def __float__(self):
        if self.computed is None:
            return self.current
        return self.computed()

    def __str__(self):
        return str(self.current)
