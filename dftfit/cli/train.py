from ..dftfit import dftfit, dftfit_batch
from .utils import load_filename, is_file_type


def add_subcommand_train(subparsers):
    parser = subparsers.add_parser('train', help='train potential model')
    parser.set_defaults(func=handle_subcommand_train)
    parser.add_argument('-t', '--training', help='training set filename in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-p', '--potential', help='potential filename in in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-c', '--config', help='configuration filename in yaml/json format', type=is_file_type, required=True)
    parser.add_argument('-b', '--batch', help='batch set filename in yaml/json format', type=is_file_type)
    parser.add_argument('-s', '--set', help='set specific features of config files', nargs='+', action='append')
    parser.add_argument('-d', '--database', help='sqlite database filename')
    parser.add_argument('--steps', help='number of steps to preform for fitting', type=int)
    parser.add_argument('--population', help='population size to begin with', type=int)
    parser.add_argument('-l', '--loglevel', help='logging level', )


def handle_subcommand_train(args):
    training_schema = load_filename(args.training)
    potential_schema = load_filename(args.potential)
    configuration_schema = load_filename(args.config)

    if args.database:
        configuration_schema['spec']['database']['filename'] = args.database
    if args.loglevel:
        configuration_schema['spec']['logging'] = args.loglevel
    if args.steps:
        configuration_schema['spec']['algorithm']['steps'] = args.steps
    if args.population:
        configuration_schema['spec']['algorithm']['population'] = args.population
    if args.set:
        # this could be implemented with "utils.set_naive_attr_value"
        raise NotImplementedError('Hope to one day support setting specific arguments')
    if args.batch:
        batch_schema = load_filename(args.batch)
        dftfit_batch(training_schema=training_schema,
                     potential_schema=potential_schema,
                     configuration_schema=configuration_schema,
                     batch_schema=batch_schema)
    else:
        dftfit(training_schema=training_schema,
               potential_schema=potential_schema,
               configuration_schema=configuration_schema)
