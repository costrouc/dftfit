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


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.benchmark(group='predict', min_rounds=1)
def test_lammps_cython_md_calculator_point_defects(benchmark, structure, potential, training):
    potential = potential('test_files/potential/MgO-charge-buck.yaml')
    structure = structure('test_files/structure/MgO.cif')
    training = training('test_files/training/training-mattoolkit-mgo-properties.yaml', cache_filename="test_files/mattoolkit/cache/cache.db")
    point_defects_schema = training.schema['spec'][7]['data']

    predict = Predict('lammps_cython')
    @benchmark
    def test():
        predict.point_defects(structure, potential, point_defects_schema, supercell=(2, 2, 2))


@pytest.mark.lammps_cython
@pytest.mark.calculator
@pytest.mark.benchmark(group='predict', min_rounds=1)
def test_lammps_cython_md_calculator_displacement_energies(benchmark, structure, potential, training):
    potential = potential('test_files/potential/MgO-charge-buck.yaml')
    structure = structure('test_files/structure/MgO.cif')
    training = training('test_files/training/training-mattoolkit-mgo-properties.yaml', cache_filename="test_files/mattoolkit/cache/cache.db")
    displacement_energy_schema = training.schema['spec'][8]['data']

    predict = Predict('lammps_cython')
    @benchmark
    def test():
        predict.displacement_energies(structure, potential, displacement_energy_schema, supercell=(2, 2, 2))
