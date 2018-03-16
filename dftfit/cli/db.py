import os
import argparse

from .utils import is_file_type
from ..db import DatabaseManager
from ..db_actions import copy_database_to_database, select_potential_from_evaluation


def add_subcommand_db(subparsers):
    parser = subparsers.add_parser('db', help='database management')
    sub_subparsers = parser.add_subparsers()
    add_subcommand_db_merge(sub_subparsers)
    add_subcommand_db_potential(sub_subparsers)


def add_subcommand_db_merge(subparsers):
    parser = subparsers.add_parser('merge', help='merge multiple databases')
    parser.set_defaults(unique=False, func=handle_subcommand_db_merge)
    parser.add_argument('input_databases', nargs='+', type=is_file_type, help='input databases to merge')
    parser.add_argument('-o', '--output-database', help='output database', required=True)
    parser.add_argument('-u', '--unique', dest='unique', action='store_true', help='only insert unique runs')
    parser.add_argument('-f', '--force', dest='force', action='store_true', help='allow to write to existing database file')


def add_subcommand_db_potential(subparsers):
    parser = subparsers.add_parser('potential', help='write evaluation potential to file')
    parser.set_defaults(func=handle_subcommand_db_potential)
    parser.add_argument('database', type=is_file_type, help='database to get potential from')
    parser.add_argument('-e', '--evaluation', type=int, help='use evaluation id')
    parser.add_argument('-o', '--output-filename', help='output potential filename', required=True)


def handle_subcommand_db_merge(args):
    if os.path.isfile(args.output_database) and not args.force:
        print(f'path {args.output_database} is an existing file use -f to force writting to existing db')
        exit(1)

    dest_dbm = DatabaseManager(args.output_database)
    for input_database in args.input_databases:
        src_dbm = DatabaseManager(input_database)
        print('merging:', input_database)
        copy_database_to_database(src_dbm, dest_dbm, only_unique=args.unique)


def handle_subcommand_db_potential(args):
    dbm = DatabaseManager(args.database)
    if args.evaluation:
        potential = select_potential_from_evaluation(dbm, args.evaluation)
        potential.write_file(args.output_filename)
