#!/usr/bin/python3
from setuptools import setup, find_packages

long_description = """DFTFIT is a package for creating
molecular dyanmics potentials by fitting ab initio dft data.
Our package is unique in that it takes advantage of LAMMPS, a well
established molecular dynamics package."""

setup(
    name='dftfit',
    version="0.1",
    description='Ab-Initio Molecular Dynamics Potential Development',
    install_requires=['numpy', 'scipy', 'ase'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov'],
    url='https://github.com/costrou/dftfit',
    maintainer='Christopher Ostrouchov',
    maintainer_email='chris.ostrouchov+dftfit@gmail.com',
    license='LGPLv2.1+',
    platforms=['linux'],
    packages=find_packages(exclude=('tests', 'docs', 'notebooks', 'examples')),
    long_description=long_description,
)
