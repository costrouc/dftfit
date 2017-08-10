from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

long_description = """DFTFIT is a package for creating
molecular dyanmics potentials by fitting ab initio dft data.
Our package is unique in that it takes advantage of LAMMPS, a well
established molecular dynamics package."""

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


setup(
    name='dftfit',
    version="0.1",
    description='Ab-Initio Molecular Dynamics Potential Development',
    install_requires=['numpy', 'scipy', 'ase', 'pymatgen', 'pymatgen-lammps'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
    url='https://github.com/costrou/dftfit',
    maintainer='Christopher Ostrouchov',
    maintainer_email='chris.ostrouchov+dftfit@gmail.com',
    license='LGPLv2.1+',
    platforms=['linux'],
    packages=find_packages(exclude=('tests', 'docs', 'notebooks', 'examples')),
    long_description=long_description,
)
