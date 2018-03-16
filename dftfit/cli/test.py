from pymatgen.io.cif import CifParser
from pymatgen.io.vasp import Poscar

from .utils import is_file_type
from ..potential import Potential
from ..predict import Predict
from ..predict.utils import print_elastic_information


def add_subcommand_test(subparsers):
    parser = subparsers.add_parser('test', help='train potential model')
    parser.set_defaults(func=handle_subcommand_test)
    parser.add_argument('-p', '--potential', help='potential filename in in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-s', '--structure', help='base structure', type=is_file_type, required=True)
    parser.add_argument('--property', action='append', choices=['lattice', 'elastic'], help='choose properties to test default is all')
    parser.add_argument('--software', default='lammps', help='md calculator to use')
    parser.add_argument('--command', help='md calculator command has sensible defaults')
    parser.add_argument('--num-workers', default=1, type=int, help='number md calculators to use')


def get_structure(filename):
    if filename.lower().endswith('.cif'):
        return CifParser(filename).get_structures()[0]
    elif filename.lower().endswith('poscar'):
        return Poscar.from_file(filename).structure
    else:
        raise ValueError('Cannot determine file type from filename [.cif, poscar]')


def handle_subcommand_test(args):
    properties = set(args.property) if args.property else {'elastic', 'lattice'}
    default_commands = {
        'lammps': 'lammps'
    }
    command = args.command if args.command else default_commands.get(args.software)
    predict = Predict(calculator=args.software, command=command, num_workers=args.num_workers)
    potential = Potential.from_file(args.potential)
    structure = get_structure(args.structure)

    import warnings
    warnings.filterwarnings("ignore") # yes I have sinned

    if 'lattice' in properties:
        old_lattice, new_lattice = predict.lattice_constant(structure, potential)
        print('Lattice Constants:')
        print('        a: {:6.3f}    b: {:6.3f}     c: {:6.3f}'.format(*new_lattice.abc))
        print('    alpha: {:6.3f} beta: {:6.3f} gamma: {:6.3f}'.format(*new_lattice.angles))
    if 'elastic' in properties:
        elastic = predict.elastic_constant(structure, potential)
        print('Elastic:')
        print_elastic_information(elastic)
