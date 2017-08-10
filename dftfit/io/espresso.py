# TODO: update to new interface

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from math import cos, radians, sqrt

import numpy as np
from ase import Atoms
from ase.geometry import cell_to_cellpar

# Heavily used constants
double_regex = r'[-+]?\d+\.\d+(?:[eE][-+]?\d+)?'
int_regex = '[+-]?\d+'

bohr = 0.529 #Ang/bohr
Ry = 13.60569 #eV/Rydberg
KBar = 0.1 #GPa/KBar




def read_qe_outfile(filename):
    """Reads the output file for a Quantum Espresso run to extract the
    forces on each atom, unit cell, and atom positions.

    Will only output the last scf step. Meaning that if a molecular
    dynamics run was performed only the last step is used.
    """
    with open(filename, "r") as f:
        out_str = f.read()

        alat_regex = r"lattice parameter \(alat\)\s+=\s+({0})".format(double_regex)

        lattice_regex = (
            r"crystal axes: \(cart\. coord\. in units of alat\)\s+"
            r"a\(1\) = \(\s+({0})\s+({0})\s+({0})\s+\)\s+"
            r"a\(2\) = \(\s+({0})\s+({0})\s+({0})\s+\)\s+"
            r"a\(3\) = \(\s+({0})\s+({0})\s+({0})\s+\)\s+"
        ).format(double_regex)

        alat = float(re.search(alat_regex, out_str).group(1))

        basis = np.array([float(_) for _ in re.search(
            lattice_regex, out_str).groups()]) * alat * bohr
        basis.shape = (3, 3)

        force_regex = (
            'atom\s+{1}\s+type\s+{1}\s+force\s+=\s+({0})\s+({0})\s+({0})\s+'
        ).format(double_regex, int_regex)

        force_block_regex = (
            r'Forces acting on atoms \(Ry/au\):\s+'
            r'((?:atom\s+{1}\s+type\s+{1}\s+force\s+=\s+{0}\s+{0}\s+{0}\s+)+)'
        ).format(double_regex, int_regex)

        position_regex = (
            '([A-Z][a-z]?)\s+({0})\s+({0})\s+({0})\s+'
        ).format(double_regex, int_regex)

        position_block_regex = (
            r'ATOMIC_POSITIONS \(angstrom\)\s+'
            r'((?:[A-Z][a-z]?\s+{0}\s+{0}\s+{0}\s+)+)'
        ).format(double_regex)

        stresses_regex = (
            r"total\s+stress\s+\(Ry/bohr\*\*3\)\s+\(kbar\)\s+P=\s+{0}\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
        ).format(double_regex)

        total_energy_regex = "!\s+total energy\s+=\s+({0})\s+Ry".format(double_regex)

        steps = []
        for forces_block, positions_block, stresses, total_energy in zip(
                re.findall(force_block_regex, out_str),
                re.findall(position_block_regex, out_str),
                re.findall(stresses_regex, out_str),
                re.findall(total_energy_regex, out_str)):

            positions = []
            symbols = []
            forces = []

            for position, force in zip(
                    re.findall(position_regex, positions_block),
                    re.findall(force_regex, forces_block)):

                symbols.append(position[0])
                positions.append([float(_) for _ in position[1:4]])
                forces.append([float(_) for _ in force])

            forces = np.array(forces)

            stresses = np.array([float(_) for _ in stresses])
            stresses.shape = (3, 3)

            total_energy = float(total_energy)

            steps.append({
                'system': Atoms(symbols=symbols, positions=positions, cell=basis, pbc=True),
                'dft': {
                    'forces': forces * Ry / bohr,
                    'stresses': stresses * Ry / (bohr**3),
                    'total-energy': total_energy * Ry
                }
            })

        if re.search("Molecular Dynamics Calculation", out_str):
            return steps
        else:
            return steps[-1]
