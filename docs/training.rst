Training Sets
=============

DFTFIT uses Ab-Inito calculation to guide the optimization of
potentials along with measured properties. The goal is to make it
easier for users to include vasp calculations in their potential
fitting. Thus DFTFIT has support for reading VASP ``vasprun.xml``,
Quantum Espresso ``*.out``, and Siesta ``*.xml`` output files. The
parsers will read as many sets that contain the structure, energy,
stress, and forces. These output files may be the result of a
relaxation, SCF, of BOMD, etc. calculation. If DFTFIT does not have
support for the output format that you supply please submit an `issue
<https://github.com/costrouc/dftfit/issues>`_. Additionally measured
properties include: lattice_constants, elastic_constants,
bulk_modulus, and shear_modulus.

Measured Properties
-------------------

Recently DFTFIT has added support for experimental properties and
other measured quantities. These include: lattice_constants,
elastic_constants, bulk_modulus, and shear_modulus. In order to use
one you must include a ground_state for an example see this input
`training file <https://github.com/costrouc/dftfit/blob/master/test_files/training/training-mattoolkit-mgo-properties.yaml>`_.

 - lattice constants (lengths)
 - elastic constants (voigt)
 - bulk modulus
 - shear modulus


Ab-Initio Training Sets
-----------------------

Example of training sets include:

 - equilibrium structure
 - displaced structures :math:`0.01 \unicode{x212B} - 0.04 \unicode{x212B}`
 - deformed structures :math:`\pm\%2` normal, :math:`\pm\%8` shear
 - random perturbed structures :math:`0.04 \unicode{x212B}`

.. image:: images/mgo-training-sets-goal.png

Be aware the DFT calculations that change the unit cell result in less
accurate energy, stress, and forces. Thus an additional SCF
calculation `will be necessary <https://cms.mpi.univie.ac.at/vasp/vasp/Accurate_bulk_relaxations_with_internal_parameters_one.html>`_.

In general a ``selector`` is used to get the input files.

 - ``selector.filename`` select a specific output filename of ``type``
 - ``selector.fileglob`` select a specific set of output files that match `glob <https://docs.python.org/3.7/library/glob.html#module-glob>`_ of ``type``.
 - ``selector.num_samples`` for each matching file choose num_samples with maximum separation

An example Siesta training set is included below.

.. code-block:: yaml

   version: v1
   kind: Training
   spec:
     - type: Siesta
       selector:
         filename: test_files/siesta/d1_li_20ev.xml
         num_samples: 3
     - type: Siesta
       selector:
         filename: test_files/siesta/d1_o_30ev.xml
         num_samples: 4
     - type: Siesta
       selector:
         filename: test_files/siesta/d1_ta_20ev.xml
         num_samples: 5

VASP
----

.. code-block:: yaml

  spec:
   - type: VASP
     selector:
       filename: test_files/vasp/vasprun.xml.mgo


Quantum Espresso
----------------

.. code-block:: yaml

   spec:
    - type: QE
      selector:
        filename: test_files/espresso/...

Siesta
------

.. code-block:: yaml

   spec:
    - type: Siesta
      selector:
        filename: test_files/siesta/d1_o_30ev.xml
        num_samples: 4
