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


def read_vasp_outcar(filename):
    """Reads the OUTCAR file from a VASP run.

    Will only output the last scf step. Meaning that if a molecular
    dynamics run was performed only the last step is used.
    """
    with open(filename) as f:
        outcar = f.read()

        atom_types_regex = r"POTCAR:\s+([A-Za-z_]+)\s+([A-Z][a-z]?)\s+(\d{2}[A-Z][a-z]+\d{4})"
        atom_types = re.findall(atom_types_regex, outcar)

        atom_numbers_regex = r"ions per type =\s+((?:\d+\s+)+)"
        atom_numbers = re.findall(int_regex, re.search(atom_numbers_regex, outcar).group(0))

        atoms = []
        for atom_type, atom_number in zip(atom_types, atom_numbers):
            atoms.append([atom_type[1], int(atom_number)])

        position_force_regex = (
            r"POSITION\s+TOTAL-FORCE \(eV/Angst\)\s+"
            r"-+\s+"
            r"((?:(?:{0}\s+){{6}})+)"
        ).format(double_regex)

        volume_basis_regex = (
            r"VOLUME and BASIS-vectors are now :\s+"
            r"-+\s+"
            r"energy-cutoff  :\s+{0}\s+"
            r"volume of cell :\s+{0}\s+"
            r"direct lattice vectors\s+reciprocal lattice vectors\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
            r"({0})\s+({0})\s+({0})\s+{0}\s+{0}\s+{0}\s+"
        ).format(double_regex)

        steps = []
        for basis, positions_forces in zip(re.findall(volume_basis_regex, outcar),
                                           re.findall(position_force_regex, outcar)):
            basis = ([[float(basis[0]), float(basis[1]), float(basis[2])],
                      [float(basis[3]), float(basis[4]), float(basis[5])],
                      [float(basis[6]), float(basis[7]), float(basis[8])]])

            positions = []
            forces = []
            for row in re.findall((r"({0})\s+" * 6).format(double_regex), positions_forces):
                positions.append([float(row[0]), float(row[1]), float(row[2])])
                forces.append([float(row[3]), float(row[4]), float(row[5])])

            symbols = []
            for atom in atoms:
                symbols += [atom[0]] * atom[1]

            steps.append({
                'system': Atoms(symbols=symbols, positions=positions, cell=basis, pbc=True),
                'dft': {
                    'forces': forces
                }
            })

        return steps[-1]


def read_vasp_xml(filename):
    """Reads the vasprun.xml file from a VASP run

    Will only output the last scf step. Meaning that if a molecular
    dynamics run was performed only the last step is used.

    """
    root = ET.parse(filename).getroot()

    symbols = []
    for atom in root.findall('atominfo/array[1]/set/rc/c[1]'):
        symbols.append(atom.text.replace(" ", ""))

    steps = []
    for calculation in root.findall('calculation'):
        # vasprun gives the basis, positions, and forces for each calculation
        # in an xml format. A list of text floats must be converted to floats

        basis_xml = calculation.find('structure/crystal/varray[@name="basis"]')
        basis = [[float(_) for _ in v.text.split()] for v in basis_xml]

        positions_xml = calculation.find('structure/varray[@name="positions"]')
        positions = [[float(_) for _ in v.text.split()] for v in positions_xml]

        forces_xml = calculation.find('varray[@name="forces"]')
        forces = np.array([[float(_) for _ in v.text.split()] for v in forces_xml])

        stresses_xml = calculation.find('varray[@name="stress"]')
        stresses = np.array([[float(_) for _ in v.text.split()] for v in stresses_xml])

        total_energy = float(calculation.find('energy/i[@name="e_fr_energy"]').text)

        steps.append({
            'system': Atoms(symbols=symbols, scaled_positions=positions, cell=basis, pbc=True),
            'dft': {
                'forces': forces,
                'stresses': stresses * KBar,
                'total-energy': total_energy
            }
        })

    return steps[-1]


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


def write_lammps_data_file(structure, atom_types, filename, format="charge"):
    """A file to write lammps atom coordinates file.

    For details on the format of a lammps data file
    http://lammps.sandia.gov/doc/read_data.html

    """
    formats = ['charge', 'atomic']

    if format not in formats:
        error_str = (
            "can only write in supported formats {}"
        ).format(formats)
        raise Exception(error_str)

    with open(filename, "w") as f:
        lx, ly, lz, xy, xz, yz = cell_to_lammps_box(structure.cell)

        f.write((
            "ASE generated file for {}\n\n"
            "{} atoms\n"
            "{} atom types\n"
            "0.0 {:.6f} xlo xhi\n"
            "0.0 {:.6f} ylo yhi\n"
            "0.0 {:.6f} zlo zhi\n"
            "{:.6f} {:.6f} {:.6f} xy xz yz\n"
        ).format(
            structure.get_chemical_formula(),
            len(structure),
            len(atom_types),
            lx, ly, lz, xy, xz, yz))

        f.write("\nMasses\n\n")
        for key, (i, mass, charge) in atom_types.items():
            f.write("{0} {1}\n".format(i, mass))

        f.write("\nAtoms\n\n")
        for i, atom in enumerate(structure, start=1):
            atom_type, mass, charge = atom_types[atom.symbol]
            if format == "charge":
                f.write("{0} {1} {2} {3:.4f} {4:.4f} {5:.4f}\n".format(
                    i, atom_type, charge, *atom.position))
            elif format == "atomic":
                f.write("{0} {1} {2:.4f} {3:.4f} {4:.4f}\n".format(
                    i, atom_type, *atom.position))


def cell_to_lammps_box(cell):
    """Converts unit cell vectors to lammps box parameters

    """
    a, b, c, alpha, beta, gamma = cell_to_cellpar(cell)
    alpha = radians(alpha)
    beta = radians(beta)
    gamma = radians(gamma)

    lx = a
    xy = b * cos(gamma)
    xz = c * cos(beta)
    ly = sqrt(b**2 - xy**2)
    yz = (b * c*cos(alpha) - xy * xz) / ly
    lz = sqrt(c**2 - xz**2 - yz**2)

    return [lx, ly, lz, xy, xz, yz]


def read_lammps_forces_dump(filename):
    """
    Reads the dump file produced by Lammps.
    It begins dumping the forces on row 9.
    """
    try:
        forces = np.loadtxt(filename, skiprows=9)
    except StopIteration:
        raise ValueError("Unable to read forces from {}".format(filename))

    if len(forces) == 0:
        raise ValueError("Unable to read forces from {}".format(filename))

    return forces


def read_lammps_logfile(filename):
    """Reads the lammps compute output from stdout. Collects stress
    tensor and total energy
    """
    with open(filename, "r") as f:
        logfile = f.read()
        match = re.search(
            "Memory usage per processor\s+=\s+{0}\s+Mbytes\s+(.*)\s+Loop time of".format(
                double_regex), logfile, re.DOTALL)
        if match:
            thermo = read_lammps_thermo(match.group(1))
        else:
            raise Exception("Unable to read thermo data from logfile")

    return {'thermo': thermo}


def read_lammps_thermo(thermo_str):
    thermo_tags = ['TotEng', 'Pxx', 'Pyy', 'Pzz', 'Pxy', 'Pxz', 'Pyz']
    index_thermo_tags = []

    data = thermo_str.split('\n')
    header = data[0].split()
    rows = data[1:]
    thermo = defaultdict(list)

    if set(thermo_tags).issubset(set(header)):
        for tag in thermo_tags:
            index_thermo_tags.append(header.index(tag))
    else:
        error_str = "Thermo style must include {0}"
        raise Exception(error_str.format(thermo_tags))

    for row in rows:
        values = row.split()
        for i, tag in zip(index_thermo_tags, thermo_tags):
            thermo[tag].append(float(values[i]))

    return thermo

# Accepted filenames and their functions
filetypes = {
    'OUTCAR': read_vasp_outcar,
    'vasprun.xml': read_vasp_xml,
    'QE': read_qe_outfile
}
