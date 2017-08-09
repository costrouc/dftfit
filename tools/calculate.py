import numpy as np

prefix = ["mpirun", "-np", "3"]

mgo_lattice = """
# LAMMPS Input File for MgO

# Initialize Simulation
clear
units metal
dimension 3
boundary p p p
atom_style charge

# Read in atomic positions and unit cell
read_data mgo.data

# Define Interatoic Potential
pair_style buck/coul/long 10.0
pair_coeff 1 1 {0} {1} {2}
pair_coeff 1 2 {3} {4} {5}
pair_coeff 2 2 {6} {7} {8}

kspace_style ewald 1.0e-5

# Run minimization
fix 1 all box/relax iso 0.0 vmax 0.001

thermo 10
# thermo_style custom step lx ly lz vol

minimize 1.0e-10 1.0e-10 2000 100000
"""

mgo_bulk = """
# LAMMPS Input File for MgO
variable t equal 0.1

# Initialize Simulation
clear
units metal
dimension 3
boundary p p p
atom_style charge

# Read in atomic positions and unit cell
read_data mgo.data

# Define Interatoic Potential
pair_style buck/coul/long 10.0
pair_coeff 1 1 {0} {1} {2}
pair_coeff 1 2 {3} {4} {5}
pair_coeff 2 2 {6} {7} {8}

kspace_style ewald 1.0e-5

# Set the timestep for simulation 
timestep 0.001

# Set temperature of all atoms
velocity all create $t 12391

# Dump atom position data
# dump 1 all atom 100 mgo.dump

fix 1 all nvt temp $t $t 1.0
# fix 1 all npt temp $t $t 1.0 iso 0.0 0.0 1.0

thermo 10
run 1000
"""

# # Matsui (1989) (Partial Charges 1.4) WORKS
# parameters = [
#     1309362.2766468062, 0.104, 0.0,
#     9892.357957, 0.201999, 0.0,
#     2145.7345, 0.3, 30.2222
# ]

# Link to potentials
# http://link.aps.org/doi/10.1103/PhysRevB.72.115437
# #Lewis and Catlow (1985) (1.0 to avoid lammps problem) WORKS
# parameters = [
#     0.0, 1.0, 0.0,
#     821.61, 0.324199, 0.0,
#     22764.5407, 0.14899, 27.8803
# ]

# # Ball and Grimes (2.0 charge)
# parameters = [
#     0.0, 1.0, 0.0,
#     1279.69, 0.29969, 0.0,
#     9547.96, 0.21916, 32.0
# ]

# # Ball and Grimes (Partial Charges 1.7) WORKS
# parameters = [
#     0.0, 1.0, 0.0,
#     929.69, 0.29909, 0.0,
#     4870.0, 0.2670, 77.0
# ]

# # made-up potential (weight forces 1.0)
# parameters = [
#     1.25380353e+06, 1.53422695e-01, 1.31810338e-02,
#     1.86488686e+03, 2.67779727e-01, 7.16784697e+00,
#     1.42774015e+03, 2.90727891e-01, 8.30463840e+01
# ]

# made-up potential (weight forces 0.75 stresses 0.2 energy 0.05)
parameters = [
    1.30907730e+06, 3.06730024e-02, -9.99749294e+00,
    4.25453827e+03, 2.38471760e-01, 2.75030583e+01,
    2.37453010e+03, 2.90297534e-01, 2.65174178e+01
]

# # made-up potential (weight forces 0.65 stresses 0.3 energy 0.05)
# parameters = [
#     2.27849172e+06, 9.05195651e-02, -2.30452490e+00,
#     8.26622414e+03, 1.84436277e-01,  1.36671419e+00,
#     2.18950157e+03, 3.45466422e-01,  1.93281635e+01
# ]

atom_types = {
    'Mg': [1, 24.305, 1.426],
    'O': [2, 15.999, -1.426]
}


def lammps_output_table(lmp_output):
    import re
    import pandas
    from io import StringIO

    match = re.search(r"(Step.*?)(?=Loop time of)", lmp_output, re.DOTALL)
    if match:
        return pandas.read_csv(StringIO(lmp_output[match.start():match.end()]),
                               sep='\s+',
                               header=0,
                               index_col=0)
    return None


def write_lammps_data_file(structure, atom_types, filename):
    """
    A file to write lammps data files
    """
    with open(filename, "w") as f:
        f.write(("ASE generated file for {0}\n\n"
                 "{1} atoms\n"
                 ).format(structure.get_chemical_formula(), len(structure)))

        f.write("{0} atom types\n".format(len(atom_types)))

        f.write("0.0 {0} xlo xhi\n".format(structure.cell[0][0]))
        f.write("0.0 {0} ylo yhi\n".format(structure.cell[1][1]))
        f.write("0.0 {0} zlo zhi\n".format(structure.cell[2][2]))

        f.write("\nMasses\n\n")
        for key, (i, mass, charge) in atom_types.items():
            f.write("{0} {1}\n".format(i, mass))

        f.write("\nAtoms\n\n")
        for i, atom in enumerate(structure, start=1):
            atom_type, mass, charge = atom_types[atom.symbol]
            f.write("{0} {1} {2} {3:.4f} {4:.4f} {5:.4f}\n".format(
                i, atom_type, charge, *atom.position))


def run_lammps(inputfile):
    from subprocess import Popen, PIPE

    lmp_command = prefix + ["lmp_ubuntu", '-i', inputfile]
    proc = Popen(lmp_command, stdout=PIPE, stderr=PIPE)
    lmp_output = proc.communicate()

    proc.wait()

    lmp_out = lmp_output[0].decode()
    lmp_err = lmp_output[1].decode()

    return lammps_output_table(lmp_out)


if __name__ == "__main__":
    from ase.lattice.spacegroup import crystal

    a = 4.4
    mgo = crystal(['Mg', 'O'], basis=[[0., 0., 0.], [0.5, 0.5, 0.5]],
                  spacegroup=225, cellpar=[a, a, a, 90., 90., 90.])

    structure = mgo * (5, 5, 5)


    # Calculate Lattice Constant
    print("Lattice Constant Calculation:")
    write_lammps_data_file(structure, atom_types, "mgo.data")
    with open("mgo_lattice.in", "w") as f:
        f.write(mgo_lattice.format(*parameters))

    dt = run_lammps("mgo_lattice.in")

    # Update lattice constant to actual value
    a = np.power(dt['Volume'].iloc[-1], 1.0/3.0) / 5.0
    print("Lattice Constant [Ang]: {0}".format(a))

    # Calculate Bulk Modulus
    print("\nBulk Modulus Calculation")

    # use lattice constant from previous calculation
    mgo = crystal(['Mg', 'O'], basis=[[0., 0., 0.], [0.5, 0.5, 0.5]],
                  spacegroup=225, cellpar=[a, a, a, 90., 90., 90.])

    structure = mgo * (5, 5, 5)

    cell = structure.cell.copy()
    scales = np.linspace(-0.02, 0.02, 10)

    data = {"volume": [],
            "energy": []}

    for scale in scales:
        structure.set_cell((1 + scale) * cell, scale_atoms=True)
        write_lammps_data_file(structure, atom_types, "mgo.data")
        with open("mgo_bulk.in", "w") as f:
            f.write(mgo_bulk.format(*parameters))

        dt = run_lammps("mgo_bulk.in")

        volume = structure.get_volume()
        energy = dt['TotEng'].iloc[-10:].mean()

        data['volume'].append(volume)
        data['energy'].append(energy)

        print("Volume [Ang^3]: {0} Energy [eV]: {1}".format(volume, energy))

    import json
    json.dump(data, open("mgo-data.json", "w"))

    from base.bulk import get_lattice_constant
    structure.set_cell(cell, scale_atoms=True)

    results = get_lattice_constant(structure, data['volume'], data['energy'])

    print("\nBulk Modulus [GPa]: {0}".format(results['bulk modulus']))
