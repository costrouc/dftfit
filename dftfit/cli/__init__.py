import argparse

from .train import add_subcommand_train


def init_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_subcommand_train(subparsers)
    return parser
