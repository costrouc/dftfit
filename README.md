**All issues and contributions should be done on
[Gitlab](https://gitlab.com/costrouc/dftfit). Github is used only as a
mirror for visibility**

# DFTFIT

DFTFIT is a python code that used Ab Initio data from DFT calculations
such as VASP, Quantum Espresso, and Siesta to develop molecular
dynamic potentials. Our package differs from other similar codes in
that we leverage LAMMPS as a calculator enabling a wide variety of
[potentials](https://dftfit.readthedocs.io/en/latest/potentials.html). The
potentials include custom python functions and a wide variety or
three-body interactions including the Tersoff, Stillinger-Weber,
Gao-Weber, Vashishta, and COMB Potentials. All of which can be
combined to have for example a Buckingham + Coulomb + ZBL
potential. We also have an extensive set of multi-objective and
single-objective
[optimizers](https://dftfit.readthedocs.io/en/latest/configuration.html#optimization)that can evaluate a potential for many properties including energy,
forces, stress, lattice constants, elastic constants, bulk modulus,
and shear modulus.

In general three things are required from the user.
  - [Ab-Initio Training
    Data](https://dftfit.readthedocs.io/en/latest/training.html)
    includes VASP, Siesta, and Quantum Espresso
    Calculations. Additionally the user may supply measured properties
    such as lattice constants, elastic constants, bulk modulus, and
    shear modulus.
  - [configuration](https://dftfit.readthedocs.io/en/latest/configuration.html):
    specifies optimization algorithm and number of steps, sqlite
    database to store results, and MD calculator to use.
  - [Potential](https://dftfit.readthedocs.io/en/latest/potentials.html)
    among a rich set of two and three body potentials. Including a
    custom python function.

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

## Potentials

Any combination of the following potentials is a valid potential in DFTFIT.

Two-Body Potentials

 - custom python function
 - ZBL
 - Buckingham
 - Beck
 - coulombic interaction
 - Lennard Jones

Three-Body Potentials

 - Tersoff
 - Stillinger Weber
 - Gao Weber
 - Vashishta
 - COMB/COMB3
 
## Measured Properties

 - energy
 - stress
 - forces
 - lattice constants (lengths)
 - elastic constants (voigt)
 - bulk modulus
 - shear modulus

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

For `pypi` installation. Note that installation of `lammps-cython` may
fail and is required. You will need to install ``LAMMPS`` as
documented
[here](https://costrouc.gitlab.io/lammps-cython/installation.html#pip). You may have to do `pip install numpy cython`.

```bash
pip install dftfit
```

For `conda` installation

```bash
conda install -c costrouc -c matsci -c conda-forge dftfit
```

For `docker` installation

```bash
docker pull costrouc/dftfit
```

# Documentation

The official documentation is hosted on readthedocs.org: https://dftfit.readthedocs.io/en/latest/

# Running

DFTFIT provides a [command line
interface](https://dftfit.readthedocs.io/en/latest/commands.html). Of
course the package can be used as a standard python package.

# Tutorial and Documentation

 - [MgO tutorial](https://dftfit.readthedocs.io/en/latest/tutorial.html)
 - [Documentation](https://dftfit.readthedocs.io/en/latest/index.html)

# Contributing

All contributions, bug reports, bug fixes, documentation improvements,
enhancements and ideas are welcome. These should be submitted at the
[Gitlab repository](https://gitlab.com/costrouc/lammps-cython). Github
is only used for visibility.

# License

[MIT](https://gitlab.com/costrouc/dftfit/blob/master/LICENSE.md)
