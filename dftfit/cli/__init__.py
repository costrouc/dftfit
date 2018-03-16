import argparse
import sys

from . import train
from . import test
from . import db


def init_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    train.add_subcommand_train(subparsers)
    test.add_subcommand_test(subparsers)
    db.add_subcommand_db(subparsers)
    return parser


def cli():
    parser = init_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    args.func(args)
