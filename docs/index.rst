.. dftfit documentation master file, created by
   sphinx-quickstart on Fri Mar 30 18:44:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to dftfit's documentation!
==================================

.. image:: images/mgo-training-sets-goal.png

DFTFIT is a python code that used Ab Initio data from DFT calculations
such as VASP and QE to create molecular dynamic potentials. Our
package differs from other similar codes in that we leverage LAMMPS as
a calculator. We also have an extensive set of multi-objective and
single-objective optimizers. See `pygmo algorithms
<https://esa.github.io/pagmo2/docs/algorithm_list.html>`_ for full
list of optimizers.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   tutorial
   potentials
   training
   configuration
   command
   visualization
   performance


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
