Improving Performance
====================

DFTFIT's performance is predictable. A great amount of effort has been
put into ensuring that the code is benchmarked. See the `benchmark
tests <https://travis-ci.org/costrouc/dftfit>`_ to view the time
it takes for certain methods to complete.

The optimization is limited by the time each ``LAMMPS`` calculator
evaluation takes. For configurations of around 100-200 atoms this
takes around 1-10 ms. DFTFIT provides a method to parallelize these
calculations among processors ``lammps.problem.num_workers``.

So for example if you have 100 training images. You can expect without
parallelism you will achieve around 5 iterations per seconds. The code
scales almost ideally with more processors.
