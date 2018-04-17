import numpy as np

class PairPotential:
    def u(self, r):
        raise NotImplemented()

    def f(self, r):
        raise NotImplemented()

    def a(self, r):
        raise NotImplemented()


class BuckinghamPotential(PairPotential):
    def __init__(self, params):
        self.a, self.rho, self.c = params

    def u(self, r):
        return self.a * np.exp(-r/self.rho) - self.c/r**6

    def f(self, r):
        return -self.a / rho * np.exp(-r/self.rho) + 6*self.c/r**7

    def a(self, r):
        return self.a / rho**2 * np.exp(-r/self.rho) + 42*self.c/r**8


class ZBLPotential(PairPotential):
    def __init__(self, params):
        self.z1, self.z2 = params

    def u(self, r):
        return
