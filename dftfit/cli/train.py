from ..dftfit import dftfit
from .utils import load_filename, is_file_type


def add_subcommand_train(subparsers):
    parser = subparsers.add_parser('train', help='train potential model')
    parser.set_defaults(func=handle_subcommand_train)
    parser.add_argument('-t', '--training', help='training set filename in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-p', '--potential', help='potential filename in in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-c', '--config', help='configuration filename in yaml/json format', type=is_file_type)
    parser.add_argument('-s', '--set', help='set specific features of config files', nargs='+', action='append')
    parser.add_argument('-d', '--database', help='sqlite database filename')
    parser.add_argument('--steps', help='number of steps to preform for fitting', type=int)
    parser.add_argument('--population', help='population size to begin with', type=int)
    parser.add_argument('-l', '--loglevel', help='logging level', )


def handle_subcommand_train(args):
    training_schema = load_filename(args.training)
    potential_schema = load_filename(args.potential)
    configuration_schema = {}
    if args.config:
        configuration_schema = load_filename(args.config)
    if args.database:
        configuration_schema['spec']['database'] = args.database
    if args.loglevel:
        configuration_schema['spec']['logging'] = args.loglevel
    if args.steps:
        configuration_schema['spec']['steps'] = args.steps
    if args.population:
        configuration_schema['spec']['population'] = args.population
    if args.set:
        raise NotImplementedError('Hope to one day support setting specific arguments')

    dftfit(training_schema=training_schema,
           potential_schema=potential_schema,
           configuration_schema=configuration_schema)
