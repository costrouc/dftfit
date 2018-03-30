# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

 - adding move towards modern deployment following https://costrouc-python-package-template.readthedocs.io/en/latest/

## v0.3.0

 - cache filename and database filename now expand home directory `~/`
 - support for custom cache filename and directory. default is still
   `~/.cache/dftfit/cache.db`. `use_cache` changed to
   `cache_filename`.
 - adding `MgO` example it is most of the data used for publication
 - adding database merge functionallity allowing much easier management of calculations
 - fixed bug: parameters are now ordered when using charge constraint
 - adding get potential from evaluation
 - fixed bug: evaluation to potential does not apply charge constraint correctly
 - fixed bug: filter_(evaluation, potential) working properly to select best, random, worst
 - fixed bug: correct bounds for contraints. used to be discarded.
 - adding ability to easily write potential to file
 - adding ability to easily test potentials for static, lattice, elastic
 - adding feature to generate relaxed structure from potential
 - visualize progress of run `dftfit db progress --run-id=... database.db`
 - summarize all of the potential fitting in the database `dftfit db summary database.db`
 - adding feature visualize the pair distributions of the training set
