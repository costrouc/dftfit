import pytest

from dftfit.predict import Predict
from dftfit.potential import Potential


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.benchmark(group='predict', min_rounds=1)
def test_lammps_cython_md_calculator_static(benchmark, structure, potential):
    potential = potential('test_files/potential/MgO-charge-buck.yaml')
    structure = structure('test_files/structure/MgO.cif')

    predict = Predict('lammps_cython')
    @benchmark
    def test():
        predict.static(structure, potential)


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.benchmark(group='predict', min_rounds=1)
def test_lammps_cython_md_calculator_lattice_constant(benchmark, structure, potential):
    potential = potential('test_files/potential/MgO-charge-buck.yaml')
    structure = structure('test_files/structure/MgO.cif')

    predict = Predict('lammps_cython')
    @benchmark
    def test():
        predict.lattice_constant(structure, potential)


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.benchmark(group='predict', min_rounds=1)
def test_lammps_cython_md_calculator_elastic_constant(benchmark, structure, potential):
    potential = potential('test_files/potential/MgO-charge-buck.yaml')
    structure = structure('test_files/structure/MgO.cif')

    predict = Predict('lammps_cython')
    @benchmark
    def test():
        predict.elastic_constant(structure, potential)
