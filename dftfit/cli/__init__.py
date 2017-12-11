import click


@click.group()
@click.pass_context
def cli(ctx, loglevel):
    pass


from . import train
from . import test
