import os
import argparse

import yaml
import json


def is_file_type(filename):
    if not os.path.isfile(os.path.expanduser(filename)):
        raise argparse.ArgumentTypeError(f'path {filename} is not a file')
    return filename


def is_not_file_type(filename):
    if os.path.isfile(os.path.expanduser(filename)):
        raise argparse.ArgumentTypeError(f'path {filename} is an existing file')
    return filename


def load_filename(filename):
    if filename.endswith('.yaml') or filename.endswith('.yml'):
        return yaml.load(open(filename))
    elif filename.endswith('.json'):
        return json.load(open(filename))
    else:
        raise argparse.ArgumentError('only json and yaml files supported')
