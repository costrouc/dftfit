import click

from . import cli

from ..dftfit import Dftfit
from ..potential import Potential
from ..training import Training


@cli.command()
@click.option('-t', '--training', type=click.Path(exists=True), required=True)
@click.option('-p', '--potential', type=click.Path(exists=True), required=True)
@click.option('-n', '--num-cores', type=click.IntRange(min=1), default=1)
@click.pass_context
def train(ctx, training, potential, num_cores):
    dftfit = Dftfit(cores=num_cores)
    dftfit.fit(Training.from_file(training), Potential.from_file(potential))
