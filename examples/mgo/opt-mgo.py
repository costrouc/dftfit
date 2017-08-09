"""Example script for running Dftfit

"""
from dftfit import Dftfit
import sys

input_template = """
# LAMMPS Input File for MgO

# Initialize Simulation
clear
units metal
dimension 3
boundary p p p
atom_style charge

# Read in atomic positions and unit cell
read_data mgo.data

set type 1 charge {9}
set type 2 charge -{9}

# Define Interatoic Potential
pair_style buck/coul/long 5.0
pair_coeff 1 1 {0} {1} {2}
pair_coeff 1 2 {3} {4} {5}
pair_coeff 2 2 {6} {7} {8}

kspace_style ewald 1.0e-5

# Required to read forces from MD run
# *not* very flexible at the moment
dump 1 all custom 1 mgo.forces fx fy fz
dump_modify 1 sort id

# Minimum required to read total-energy and pressure tensor
# order does *not* matter and additional items can be included
thermo_style custom etotal pxx pyy pzz pxy pxz pyz

run 0
"""

potential_template = """

"""

# See optimize.py for description of each parameter
dftfit_config = {
    "lammps_command": 'lammps',
    "lammps_logfile": 'log.lammps',
    "lammps_template_files": {"mgo.in": input_template,
                              "mgo.pot": potential_template},
    "lammps_inputfile": "mgo.in",
    "lammps_datafile": "mgo.data",
    "lammps_forces_dumpfile": "mgo.forces",
    "lammps_unit_conversions": {  # Using metal units
        "force": 1.0,
        "stress": 0.0001,         # GPa/Bar
        "energy": 1.0,
    },
    "weights": {
        'forces': 0.75,
        'stresses': 0.2,
        'total-energy': 0.05
    },
    "DEBUG": True,
}


dftfit = Dftfit(config=dftfit_config)

FMAX = sys.float_info.max
FMIN = sys.float_info.min

# If parameter is bounded
# [initial_parameter_guess, (min_value, max_value)]
#
# If parameter is not bounded
# [initial_parameter_guess, None]

# Tricky way to set parameters and their respective bounds
# It makes it easier to set if they are side by side
# TODO evaluate if this affects readability
dftfit.initial_parameters, dftfit.bounds = zip(*[
    [1309362.2766468062, (0.0, 100000000.0)],
    [0.104, (0.0000001, 1000000.0)],
    [0.0, (-100.0, 100.0)],
    [9892.357, (0.0, 100000000.0)],
    [0.20199, (0.000001, 1000000.0)],
    [0.0, (-100.0, 100.0)],
    [2145.7345, (0.0, 10000000.0)],
    [0.3, (0.000001, 100000.0)],
    [30.2222, (-100.0, 100.0)],
    [1.4, (1.0, 3.0)]
])

dftfit.atom_types = {
    'Mg': [1, 24.305, 1.4],
    'O': [2, 15.999, -1.4]
}

# import os
# directory = "../../data/mgo/3/"
# for filename in os.listdir(directory):
#     if filename.endswith(".xml"):
#         dftfit.add_system_config(directory + filename, filetype="vasprun.xml")

filename = "../../data/mgo/1/qe_mgo_out"
from dftfit.io import read_qe_outfile
dftfit.system_configs += read_qe_outfile(filename)

dftfit.optimize()
