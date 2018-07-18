.. dftfit documentation master file, created by
   sphinx-quickstart on Fri Mar 30 18:44:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to dftfit's documentation!
==================================

.. image:: images/mgo-training-sets-goal.png

DFTFIT is a python code that used Ab Initio data from DFT calculations
such as VASP, Quantum Espresso, and Siesta to develop molecular
dynamic potentials. Our package differs from other similar codes in
that we leverage LAMMPS as a calculator enabling a wide variety of
`potentials
<https://dftfit.readthedocs.io/en/latest/potentials.html>`_. The
potentials include custom python functions and a wide variety or
three-body interactions including the Tersoff, Stillinger-Weber,
Gao-Weber, Vashishta, and COMB Potentials. All of which can be
combined to have for example a Buckingham + Coulomb + ZBL
potential. We also have an extensive set of multi-objective and
single-objective `optimizers
<https://dftfit.readthedocs.io/en/latest/configuration.html#optimization>`_.

In general three things are required from the user.
  - `Ab-Initio Training
    Data <https://dftfit.readthedocs.io/en/latest/training.html>`_
    includes VASP, Siesta, and Quantum Espresso Calculations.
  - `configuration <https://dftfit.readthedocs.io/en/latest/configuration.html>`_
    specifies optimization algorithm and number of steps, sqlite
    database to store results, and MD calculator to use.
  - `Potential <https://dftfit.readthedocs.io/en/latest/potentials.html>`_
    among a rich set of two and three body potentials. Including a
    custom python function.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   tutorial
   potentials
   training
   configuration
   commands
   visualization
   performance


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
