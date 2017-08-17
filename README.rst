TODO: much is incorrect needs update

DFTFIT
------

DFTFIT is a python code that used Ab Initio data from DFT calculations
such as VASP and QE to create molecular dynamic potentials. Our
package differs from other similar codes in that we leverage LAMMPS.

Presentations about dftfit:
 - [HTCMC 2016](https://speakerdeck.com/costrouc/dftfit-potential-generation-for-molecular-dynamics-calculations#)

Algorithm
---------

We use least squares for finding the optimal parameters for a proposed
potential. Since our DFTFIT uses LAMMPS, the user has the freedom to
use any of the potentials available in LAMMPS.

Our algorithm follows a
[highly cited publication](http://dx.doi.org/10.1063/1.1513312) that
proposes a method for determining a new potential for Silicon.

![Optimization Equation](docs/img/eqs.png)

Parameters
----------

 - [$n_c$] number of system configurations
 - [$N$] number of atoms in each configuration
 - [$\alpha, \beta$] tensor with 3D dimensions [x, y, z]
 - [$cl$] classical results from molecular dynamics potential
 - [$ai$] ab initio results from dft simulation
 - [$w_f, w_s, w_e$] weights to assign respectively for force, stress,
   energy
 - [$F, S, E$] force, stress, and energy respectively.


Dependencies
------------

 - [LAMMPS](http://lammps.sandia.gov/)
 - [NLOPT](http://ab-initio.mit.edu/wiki/index.php/NLopt) with python extension or scipy
 - [ASE](https://wiki.fysik.dtu.dk/ase/download.html)
 - DFT data from either [VASP](https://www.vasp.at/) or
   [Quantum Espresso](http://www.quantum-espresso.org/)

Currently DFTFIT depends on the atomic simulation environment but we will be moving to [pymatgen](http://pymatgen.org/) as soon as possible.


Install
-------

```bash
python3 setup.py develop --user
```

Installing dftfit in this way will allow any changes to the code to be
immediately applied to the package without the need for a re-install.

Note that DFTFIT will NOT install LAMMPS, VASP, or Quantum Espresso.
This software must be seperatly installed by the user.

Additionally nlopt is an optional dependency that requires the python
extension as well. We hope to remove the need for nlopt.

Running
-------

DFTFIT is a library that provides methods for optimization. There is a
GUI in the works. See the test folder for examples. Currently there
are examples for mgo and ceria.

Examples
--------

Two examples are included within the dftfit package. Currently it only
works with the nlopt package. NLOPT requires python 2.7. We hope to
remove this dependency soon.
