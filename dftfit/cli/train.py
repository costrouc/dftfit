import click

from . import cli

from ..dftfit import Dftfit
from ..potential import Potential
from ..training import Training


@cli.command()
@click.option('-t', '--training', type=click.Path(exists=True))
@click.option('-p', '--potential', type=click.Path(exists=True))
@click.pass_context
def train(ctx, training, potential):
    dftfit = Dftfit()
    dftfit.fit(Training.from_file(training), Potential.from_file(potential))
