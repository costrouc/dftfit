# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


version='0.5.1'
setup(
    name='dftfit',
    version=version,
    description='Ab-Initio Molecular Dynamics Potential Development',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/costrouc/dftfit',
    author='Chris Ostrouchov',
    author_email='chris.ostrouchov+dftfit@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='materials dft molecular dynamics lammps science hpc',
    download_url='https://github.com/costrouc/dftfit/archive/v%s.zip' % version,
    packages=find_packages(exclude=('tests', 'docs', 'examples', 'test_files')),
    install_requires=[
        'pymatgen',
        'marshmallow',
        'pyyaml',
        'pygmo',
        'pandas',
        'scipy',
        'numpy',
        'scikit-learn',
        'lammps-cython',
        'pymatgen_lammps',
    ],
    setup_requires=['pytest-runner', 'setuptools>=38.6.0'],  # >38.6.0 needed for markdown README.md
    extras_require={
        'mattoolkit': 'mattoolkit'
    },
    tests_require=['pytest', 'pytest-benchmark'],
    entry_points={
        'console_scripts': [
            'dftfit=dftfit.__main__:main'
        ]
    },
)
