Configuration
=============

The configuration schema is where you specify all optimization
settings and general DFTFIT settings such as which ``sqlite`` database
to write to. See bellow for an example configuration file.

.. code-block:: yaml

   version: v1
   kind: Configuration
   metadata:
     name: simple test
     labels:
       test: simple
       hello: world
   spec:
     logging: INFO
     database:
       filename: "test.db"
       interval: 10
     algorithm:
       name: 'pygmo.de'
       steps: 10
       population: 5
       include_initial_guess: False
     problem:
       calculator: 'lammps'
       command: 'lammps_serial'
       weights:
         force:  0.8
         stress: 0.1
         energy: 0.1

Metadata
--------

DFTFIT allows a user to assign a name to an optimization run
``metadata.name`` along with arbitrary key value strings to the
run. This metadata will be included in the SQLite database.

 - ``metadata.name`` string name to assign to run
 - ``metadata.labels`` key, value strings to assign to run

Optimization
------------

DFTFIT gives the user explicit control over the optimization
procedure. In general the number of potential evaluations is equal to
``spec.population * (spec.steps + 1)``. This is because DFTFIT does
one initial evaluations of guessed parameters. Note that optimization
is broken into two parts. The problem is how DFTFIT evaluates the
objective function. The algorithm is control over the optimization
algorithm used on the objective function.

Problem
~~~~~~~

DFTFIT uses the problem to specify how it evaluates the objective
function.

 - ``spec.problem.weights`` weights to use in addition to the features
   to calculate. Available options include: force, stress, energy,
   lattice_constants, elastic_constants, bulk_modulus,
   shear_modulus. Note that even for multiobjective optimization
   functions a single objective value can be computed.

Algorithms
~~~~~~~~~~

DFTFIT is unique in that it allows for both single and multi objective
optimization. By using `pagmo2
<https://esa.github.io/pagmo2/docs/algorithm_list.html>`_ for
optimization DFTFIT is able to offer 20+ single objective and several
multi-objective algorithms. A list of some of the notable algorithms
include.

 - `SADE <https://esa.github.io/pagmo2/docs/python/algorithms/py_algorithms.html#pygmo.sade>`_
 - `LBFGS <https://esa.github.io/pagmo2/docs/python/algorithms/py_algorithms.html#pygmo.nlopt>`_
 - `Bee Colony <https://esa.github.io/pagmo2/docs/python/algorithms/py_algorithms.html#pygmo.bee_colony>`_
 - `MOEAD <https://esa.github.io/pagmo2/docs/python/algorithms/py_algorithms.html#pygmo.moead>`_

Values

 - ``spec.algorithm.name`` pagmo2 optimization algorithm to use
 - ``spec.algorithm.steps`` number of steps to take in optimization
 - ``spec.algorithm.population`` number of guesses per optimization step
 - ``spec.algorithm.include_initial_guess`` whether to include the initial values from the potential schema


SQLite Database
---------------

Most scientific software writes output to a custom binary output file
or ``json`` files. DFTFIT writes all optimization information to an
SQLite database. This provides MANY benefits.

 - several concurrent runs can write to the same file
 - since sqlite is a database you can evaluate the progress of the optimization in realtime
 - sqlite is fault tollerant meaning that the change of corruption is very low

For easily viewing the results DFTFIT provides serveral methods in
``dftfit.db_actions``. Also you may use any available SQLite viewer
such as the free `sqlitebrowser <http://sqlitebrowser.org/>`_.

 - ``spec.database.filename`` controls the sqlite filename that all information is written to
 - ``spec.database.interval`` controls how dftfit batches writes of evaluation information. Each write takes around 1-20 ms depending on system.

MD Calculator
-------------

DFTFIT originally only had one MD calculator ``lammps``. However it
worked by writting input files and then telling lammps to run
them. This was not ideal so a new calculator was written that uses
`lammps-cython <https://github.com/costrouc/lammps-cython>`_. This
calculator integrated `LAMMPS` within the python process.

It is at least 5X-10X faster and is the recommended calculator.

 - ``spec.problem.calculator`` set that DFTFIT calculator to use. Recommended ``lammps_cython``. Available: "lammps", "lammps_cython"
 - ``spec.problem.command`` only used by "lammps" calculator to
   specify the executable path.
 - ``spec.problem.num_workers`` allows for parallelism of DFTFIT
   optimization. Does not scale well past 6 workers (1500 lammps
   calculations/second).



Miscellaneous
-------------

 - ``spec.logging`` controls the verbosity of DFTFIT (DEBUG, INFO, WARNING, CRITICAL)
