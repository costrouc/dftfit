from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
# To use a consistent encoding
from codecs import open
from os import path
import sys
import shlex


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        if isinstance(self.pytest_args, str):
            self.pytest_args = shlex.split(self.pytest_args)
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


version='0.1.8'
setup(
    name='dftfit',
    version=version,
    description='Ab-Initio Molecular Dynamics Potential Development',
    long_description=long_description,
    url='https://gitlab.aves.io/costrouc/dftfit',
    author='Chris Ostrouchov',
    author_email='chris.ostrouchov+dftfit@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass = {'test': PyTest},
    keywords='materials dft molecular dynamics lammps science hpc',
    download_url='https://gitlab.aves.io/costrouc/dftfit/repository/archive.zip?ref=v%s' % version,
    packages=find_packages(exclude=('tests', 'docs', 'notebooks', 'examples')),
    install_requires=['pymatgen==2017.7.4', 'pymatgen-lammps', 'marshmallow', 'pyyaml', 'pygmo'],
    extras_require={
        'mattoolkit': 'mattoolkit',
    },
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'dftfit=dftfit.__main__:main'
        ]
    },
    license='LGPLv2.1+',
)
