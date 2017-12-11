import click

import yaml
import json

from . import cli
from ..dftfit import dftfit


def load_filename(filename):
    if filename.endswith('.yaml') or filename.endswith('.yml'):
        return yaml.load(open(filename))
    elif filename.endswith('.json'):
        return json.load(open(filename))
    else:
        raise ValueError('only json and yaml files supported')


@cli.command()
@click.option('-t', '--training', type=click.Path(exists=True), required=True)
@click.option('-p', '--potential', type=click.Path(exists=True), required=True)
@click.option('-c', '--config', type=click.Path(exists=True))
@click.pass_context
def train(ctx, training, potential, config):
    dftfit(training_schema=load_filename(training),
           potential_schema=load_filename(potential),
           configuration_schema=load_filename(config))
