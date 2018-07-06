import math

import lammps
import numpy as np

from .base import DFTFITCalculator, MDReader


class LammpsCythonDFTFITCalculator(DFTFITCalculator):
    """This is not a general purpose lammps calculator. Only for dftfit
    evaluations. For now there are not plans to generalize it.
    """
    def __init__(self, structures, num_workers=1):
        if num_workers != 1:
            raise NotImplemented('For now limited to one worker')
        self.structures = structures
        self.lammps_systems = []

    def _initialize_lammps(self, structure):
        lmp = lammps.Lammps(units='metal', style='full', args=[
            '-log', 'none', '-screen', 'none'
        ])
        lmp.command('atom_modify map yes')
        elements = [s for s in set(structure.species)]
        atom_types = np.array([elements.index(atom.specie)+1 for atom in structure], dtype=np.intc)
        lmp.box.from_lattice_const(
            len(elements),
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

    def _apply_potential(self, lmp, elements, potential):
        """Apply specific potential

        Wish that this was more generic. But I have found that simpler
        implementation is better for now.
        """
        # buckingham + charge
        spec = potential.schema['spec']
        if 'charge' in spec and 'kspace' in spec and 'pair' in spec and \
           spec['pair']['type'] == 'buckingham':
            self._apply_buckingham_charge(lmp, elements, potential)

    def _apply_buckingham_charge(self, lmp, elements, potential):
        element_map = {e.symbol: i for i, e in enumerate(elements, start=1)}
        spec = potential.schema['spec']
        lmp.command('kspace_style %s %f' % (
            spec['kspace']['type'], spec['kspace']['tollerance']))
        lmp.command('pair_style buck/coul/long %f' % spec['pair']['cutoff'])
        for parameter in spec['pair']['parameters']:
            ij = sorted([element_map[parameter['elements'][0]],
                         element_map[parameter['elements'][1]]])
            lmp.command('pair_coeff %d %d %s' % (
                ij[0], ij[1],
                ' '.join([str(float(coeff)) for coeff in parameter['coefficients']])))
        for element, charge in spec['charge'].items():
            lmp.command('set type %d charge %f' % (element_map[element], float(charge)))

    async def submit(self, potential, properties=None):
        properties = properties or {'stress', 'energy', 'forces'}
        results = []
        for (lmp, elements), structure in zip(self.lammps_systems, self.structures):
            self._apply_potential(lmp, elements, potential)
            lmp.run(0)
            S = lmp.thermo.computes['thermo_press'].vector
            results.append(MDReader(
                forces=lmp.system.forces.copy(),
                energy=lmp.thermo.computes['thermo_pe'].scalar + lmp.thermo.computes['my_ke'].scalar,
                stress=np.array([
                    [S[0], S[3], S[5]],
                    [S[3], S[1], S[4]],
                    [S[5], S[4], S[2]]
                ]),
                structure=structure))
        return results

    def shutdown(self):
        pass
