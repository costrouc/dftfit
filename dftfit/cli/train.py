import argparse
import os
import yaml
import json

from ..dftfit import dftfit


def _exists_and_load_filename(filename):
    if not os.path.isfile(filename):
        raise argparse.ArgumentError(f'path {filename} is not a file')

    if filename.endswith('.yaml') or filename.endswith('.yml'):
        return yaml.load(open(filename))
    elif filename.endswith('.json'):
        return json.load(open(filename))
    else:
        raise argparse.ArgumentError('only json and yaml files supported')


def add_subcommand_train(subparsers):
    parser = subparsers.add_parser('train', help='train potential model')
    parser.set_defaults(func=handle_subcommand_train)
    parser.add_argument('-t', '--training', help='training set filename in yaml/json format', required=True)
    parser.add_argument('-p', '--potential', help='potential filename in in yaml/json format', required=True)
    parser.add_argument('-c', '--config', help='configuration filename in yaml/json format')


def handle_subcommand_train(args):
    training_schema = _exists_and_load_filename(args.training)
    potential_schema = _exists_and_load_filename(args.potential)
    configuration_schema = {}
    if args.config:
        configuration_schema = _exists_and_load_filename(args.config)
    dftfit(training_schema=training_schema,
           potential_schema=potential_schema,
           configuration_schema=configuration_schema)
