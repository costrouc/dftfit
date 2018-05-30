import math

import lammps
import pymatgen as pmg

from .base import MDCalculator, MDReader


class LammpsCythonCalculator(MDCalculator):
    """This is not a general purpose lammps calculator. Only for dftfit
    evaluations. For now there are not plans to generalize it.
    """
    def __init__(self, structures, num_workers=1):
        if num_workers != 1:
            raise NotImplemented('For now limited to one worker')
        self.structures = structures
        self.lammps_systems = []

    def _initialize_lammps(self, structure):
        lmp = lammps.Lammps(units='metal', args=[
            '-log', 'none', '-screen', 'none'
        ])
        lmp.command('atom_modify map yes')
        elements = [s for s in set(structure.species)]
        atom_types = np.array([elements.index(atom.specie)+1 for atom in structure], dtype=np.intc)
        lmp.box.from_lattice_const(len(elements),
                                   np.array(structure.lattice.abc),
                                   np.array(structure.lattice.angles) * (math.pi/180))
        for element, atom_type in zip(elements, lmp.system.atom_types):
            atom_type.mass = element.atomic_mass
        lmp.system.create_atoms(atom_types, structure.cart_coords+1e-8)
        lmp.thermo.add('my_ke', 'ke', 'all')
        return lmp, elements

    async def create(self):
        for structure in self.structures:
            self.lammps_systems.append(self._initialize_lammps(structure))

    def _apply_potential(self, lmp, potential):
        pass

    def _apply_potential_charges(self

    async def submit(self, potential, properties=None):
        properties = properties or {'stress', 'energy', 'forces'}
        results = []
        for lmp, structure in zip(self.lammps_systems, self.structures):
            self._apply_potential(lmp, potential)
            lmp.run(0)
            S = lmp.thermo.computes['thermo_press'].vector
            results.append(MDReader(
                forces=lmp.system.forces.copy(),
                energy=lmp.thermo.computes['thermo_pe'].scalar + lmp.thermo.computes['my_ke'].scalar,
                stresses=np.array([
                    [S[0], S[3], S[5]],
                    [S[3], S[1], S[4]],
                    [S[5], S[4], S[2]]
                ]),
                structure=structure))
        return results

    async def shutdown(self):
        pass
