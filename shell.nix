{ pkgs ? import <nixpkgs> { }, pythonPackages ? pkgs.python3Packages }:

pkgs.mkShell {
  buildInputs = with pythonPackages; [
    # build dependecies
    pkgs.lammps
    pymatgen marshmallow pyyaml pygmo pybtex
    pandas scipy numpy scikitlearn
    lammps-cython pymatgen-lammps
    # test dependencies
    pytest pytest-benchmark pytestcov
    # jupyter lab demonstrations
    elpy
  ];

  shellHook = ''

  '';
}
