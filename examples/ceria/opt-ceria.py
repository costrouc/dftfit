"""Example script for running Dftfit

"""
import sys
from dftfit import Dftfit
dftfit = Dftfit()

#input_template = """
#"""

potential_template = """
## parameters in LAMMPS lj units for charge-transfer potential of ceria in lammps ##

# one-body interaction line:
# element1 * * V2N   m        q           simga CN polarizability lamda
O  * *         -0.25 15.999  -7.200106    1.430 2  0              5.803
Ce * *         0.50  140.116 14.400212    1.010 4  0              4.149
#O  * *         -0.25 15.999  0    1.430 2  0              5.803
#Ce * *         0.50  140.116 0    1.010 4  0              4.149
# notes: in lammps, O-1,Si-2, so O line should precede Si line
# V2N is zi/ni,e.g. valence over maximum outmost shell electron
# V2N is -2/8 for Oxygen, 4/8 for Silicon
# q column is not used: charge will be assigned either by readdata file or "set group group_name charge charge_amount" command

# two-body interaction line:
# element1 element2 * Aij      rij      Cij         nij         kij      Req         Dummy_variable(0)
Ce         Ce       * {3}      1.0000   0.0000E+00  0.0000E+00  0.0000   0.0000E+00  0
Ce         O        * {4}      {6}      0.0000E+00  0.0000E+00  0.0000   0.0000E+00  8
O          Ce       * {4}      {6}      0.0000E+00  0.0000E+00  0.0000   0.0000E+00  4
O          O        * {5}      {7}      0.0000E+00  0.0000E+00  {8}      0.0000E+00  0

# three-body interaction line:
# elelment1 element2 element3 cos(theta) gama   prefact Rcut    delta   a       b
Ce          Ce       Ce       0         0       0       4.0     0       0       0
O           O        O        0         0       0       4.0     0       0       0
Ce          Ce       O        0         0       0       4.0     0       0       0
Ce          O        O        -0.333    0.200   0.000   4.0     {0}     {1}     {2}
O           Ce       Ce       -0.766    0.300   0.000   4.0     -{0}    {1}     {2}
O           Ce       O        0         0       0       4.0     -{0}    {1}     {2}
O           O        Ce       0         0       0       4.0     0.00    0       0
Ce          O        Ce       0         0       0       4.0     {0}     {1}     {2}
"""

# See optimize.py for description of each parameter
dftfit.config.update({
    "lammps_command": '/Users/James/Software/LAMMPS/lmps-flx-Jan11/lmp_serial',
    "lammps_logfile": 'log.lammps',
    "lammps_template_files": { "ceria.pot": potential_template},
    "lammps_inputfile": "in.ceria",
    "lammps_datafile": "ceria.data",
    "lammps_forces_dumpfile": "ceria.forces",
    "lammps_unit_conversions": {  # Using metal units
        "force": 1.0,
        "stress": 160,         # GPa/Bar
        "energy": 1.0,
    },
    'weights': {
            'forces': 0.7,
            'stresses': 0.2,
            'total-energy': 0.1
    },
    "DEBUG": False,
})


float_MAX = sys.float_info.max
float_MIN = sys.float_info.min

# If parameter is bounded
# [initial_parameter_guess, (min_value, max_value)]
#
# If parameter is not bounded
# [initial_parameter_guess, None]

# Tricky way to set parameters and their respective bounds
# It makes it easier to set if they are side by side
# TODO evaluate if this affects readability
dftfit.parameters, dftfit.bounds = zip(*[
 	[0.0, (0.0,0)],
        [1.0, (1,1)],
        [1,(1.0,1)],
        #[0.5, (0.01,3)],
        #[1.0, (0.1,float_MAX)],
        #[1,(0.1,20)],
        [10, (0, float_MAX)],
        [1176, (0.1,float_MAX)],
        [22760,(0.1,float_MAX)],
        [0.3810,(0.1,float_MAX)],
        [0.1490,(0.01,float_MAX)],
        [27.890,(0.1, float_MAX)]
])

dftfit.atom_types = {
    'Ce': [2, 141, 1.4],
    'O': [1, 15.999, -1.4]
}

# # To read QE run
# filenames = ['../../data/mgo/qe_mgo_out']
# for filename in filenames:
#     dftfit.add_system_config(filename, filetype='QE')

# To import a vasp run
from dftfit.io import read_vasp_xml
folders = ['../../data/ceria/5',
          '../../data/ceria/6',
          '../../data/ceria/7',
          '../../data/ceria/8',
          '../../data/ceria/9',
          '../../data/ceria/10',
          '../../data/ceria/11',
          '../../data/ceria/12',
          '../../data/ceria/13',
          '../../data/ceria/14'
]
for folder in folders:
    config = read_vasp_xml(folder)
    from pprint import pprint
    pprint(config)
    dftfit.system_configs.append(config)

dftfit.optimize()
