# from pathlib import Path

# import click
# from pymatgen.io.cif import CifParser
# from pymatgen.io.vasp import Poscar

# from . import cli
# from ..potential import Potential


# def get_structure(filename):
#     from pymatgen.io.cif import CifParser
#     from pymatgen.io.vasp import Poscar

#     if filename.lower().endswith('.cif'):
#         return CifParser(filename).get_structure()[0]
#     elif filename.lower().endswith('poscar'):
#         return Poscar.from_file(filename).structure
#     else:
#         raise ValueError('Cannot determine file type from filename [.cif, poscar]')


# @cli.command()
# @click.option('-s', '--structure', type=click.Path(exists=True), required=True)
# @click.option('-p', '--potential', type=click.Path(exists=True), required=True)
# @click.option('-d', '--directory', type=click.Path(exists=True), default=".")
# @click.option('--software', type=click.Choice(['lammps']), default="lammps")
# @click.option('-c', '--calculation', type=click.Choice(['relax', 'static']), default="relax")
# @click.pass_context
# def test(ctx, structure, potential, directory, software, calculation):
#     directory = str(Path(directory).absolute())
#     print(
#         f'Structure: {structure}\n'
#         f'Potential: {potential}\n'
#         f'Directory: {directory}\n'
#         f'Software: {software}\n'
#         f'Calculation: {calculation}'
#     )

#     structure = get_structure(structure)
#     potential = Potential.from_file(potential)
#     if software == 'lammps':
#         from ..io.lammps import modify_input_for_potential
#         from lammps.sets import StaticSet, RelaxSet
#         from lammps.inputs import LammpsData
#         mapper = {
#             'static': StaticSet,
#             'relax': RelaxSet
#         }
#         input_set = mapper[calculation](LammpsData.from_structure(structure))
#         modify_input_for_potential(input_set, potential)
#         input_set.write_input(directory)
