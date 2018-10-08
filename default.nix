let
  # nixpkgs
  nixpkgs = builtins.fetchTarball {
    url = "https://github.com/costrouc/nixpkgs/archive/277e3d723f01e690db49eb4feaaf8900610cb0e1.tar.gz";
    sha256 = "020i81rfhzzzc0fx132p1rxk2cazbpdpk2jz9viwa3hxjv07hksd";
  };
  pkgs = import nixpkgs { config = { allowUnfree = true; }; };
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    # build dependecies
    lammps
    python36Packages.pymatgen python36Packages.marshmallow
    python36Packages.pyyaml python36Packages.pygmo
    python36Packages.pandas python36Packages.scipy
    python36Packages.numpy python36Packages.scikitlearn
    python36Packages.lammps-cython python36Packages.pymatgen-lammps
    # test dependencies
    python36Packages.pytest
    python36Packages.pytest-benchmark
    python36Packages.pytestcov
  ];

  shellHook = ''
    export NIX_PATH="nixpkgs=nixpkgs:."
    # usually link in a nix-built vendor directory or other housekeeping


  '';
}
