import click
import logging

from ..logging import LOG_LEVELS, init_logging


@click.group()
@click.option('--loglevel', type=click.Choice(LOG_LEVELS), default='WARNING')
@click.pass_context
def cli(ctx, loglevel):
    init_logging(loglevel)


from . import train
