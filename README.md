**All issues and contributions should be done on
[Gitlab](https://gitlab.com/costrouc/dftfit). Github is used only as a
mirror for visibility**



# DFTFIT

DFTFIT is a python code that used Ab Initio data from DFT calculations
such as VASP and QE to create molecular dynamic potentials. Our
package differs from other similar codes in that we leverage LAMMPS.

<table>
<tr>
  <td>Latest Release</td>
  <td><img src="https://img.shields.io/pypi/v/dftfit.svg" alt="latest release"/></td>
</tr>
<tr>
  <td>Package Status</td>
  <td><img src="https://img.shields.io/pypi/status/dftfit.svg" alt="status" /></td>
</tr>
<tr>
  <td>License</td>
  <td><img src="https://img.shields.io/pypi/l/dftfit.svg" alt="license" /></td>
</tr>
<tr>
  <td>Build Status</td>
  <td> <a href="https://gitlab.com/costrouc/dftfit/pipelines"> <img
src="https://gitlab.com/costrouc/dftfit/badges/master/pipeline.svg"
alt="gitlab pipeline status" /> </a> </td>
</tr>
<tr>
  <td>Documentation</td>
  <td> <a href="https://dftfit.readthedocs.io/en/latest/"> <img src="https://readthedocs.org/projects/dftfit/badge/?version=latest" alt="readthedocs documentation" /> </a> </td>
</tr>
</table>

## Presentations:

 - [HTCMC 2016](https://speakerdeck.com/costrouc/dftfit-potential-generation-for-molecular-dynamics-calculations#)
 - [MRS 2017](https://speakerdeck.com/costrouc/dftfit-potential-generation-for-molecular-dynamics-calculations#)

## Algorithm

We use generalized least squares method for finding the optimal
parameters for a proposed potential. DFTFIT integrates with existing
MD software as a potential calculator. Currently only
[LAMMPS](http://lammps.sandia.gov/doc/Manual.html) is supported. This
means the user has the freedom to use any of the potentials available
in LAMMPS.

Our algorithm follows a
[highly cited publication](http://dx.doi.org/10.1063/1.1513312) that
proposes a method for determining a new potential for Silicon using the force matching of DFT calcultions.

![Optimization Equation](https://gitlab.com/costrouc/dftfit/raw/master/docs/images/equations.png)

### Parameters

 - n_c: number of system configurations
 - N number of atoms in each configuration
 - α, β: tensor with 3D dimensions [x, y, z]
 - cl: classical results from molecular dynamics potential
 - ai: ab initio results from dft simulation
 - w_f, w_s, w_e: weights to assign respectively for force, stress,
   energy
 - F, S, E: force, stress, and energy respectively.


Dependencies
------------

 - MD Calculator: [LAMMPS](http://lammps.sandia.gov/)
   - [pymatgen_lammps (run as command)](https://gitlab.com/costrouc/pymatgen-lammps)
   - [lammps-cython (python interface)](https://gitlab.com/costrouc/lammps-cython)
 - [pagmo2](https://github.com/esa/pagmo2)
 - [pymatgen](https://github.com/materialsproject/pymatgen/)
 - Ab Initio data from either [VASP](https://www.vasp.at/) or [Quantum
   Espresso](http://www.quantum-espresso.org/)

# Installation

```bash
pip install dftfit
```

# Documentation

The official documentation is hosted on readthedocs.org: https://dftfit.readthedocs.io/en/latest/

# Running

DFTFIT is a library that provides methods for optimization. There is a
GUI in the works. See the test folder for examples. Currently there
are examples for mgo and ceria.

# Examples

One example for DFTFIT is included for MgO.

# Contributing

All contributions, bug reports, bug fixes, documentation improvements,
enhancements and ideas are welcome. These should be submitted at the
[Gitlab repository](https://gitlab.com/costrouc/lammps-cython). Github
is only used for visibility.

# License

[MIT](https://gitlab.com/costrouc/dftfit/blob/master/LICENSE.md)
