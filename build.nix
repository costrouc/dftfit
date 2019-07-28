{ pkgs ? import <nixpkgs> {}, pythonPackages ? "python3Packages" }:

rec {
  package = pythonPackages.buildPythonPackage rec {
    pname = "dftfit";
    version = "master";
    disabled = pythonPackages.isPy27;

    src = builtins.filterSource
      (path: _: !builtins.elem  (builtins.baseNameOf path) [".git" "result" "docs"])
      ./.;

    buildInputs = with pythonPackages; [
      pytestrunner
      pkgs.lammps
    ];

    checkInputs = with pythonPackages; [
      pytest
      pytestcov
      pytest-benchmark
      pkgs.openssh
      pkgs.lammps
    ];

    propagatedBuildInputs = with pythonPackages; [
      pymatgen
      marshmallow
      pyyaml
      pygmo
      pandas
      scipy
      numpy
      scikitlearn
      lammps-cython
      pymatgen-lammps
    ];

    checkPhase = ''
      pytest -m "not long" \
             --ignore tests/integration/test_md_lammps_cython_calculator.py \
             --ignore tests/integration/test_dftfit_lammps_cython_calculator.py \
    '';

    meta = with pkgs; {
      description = "Ab-Initio Molecular Dynamics Potential Development";
      homepage = https://github.com/costrouc/dftfit;
      license = lib.licenses.mit;
      maintainers = with lib.maintainers; [ costrouc ];
    };
  };

    docs = pkgs.stdenv.mkDerivation {
    name = "dftfit-docs";
    version = "master";

    src = builtins.filterSource
        (path: _: !builtins.elem  (builtins.baseNameOf path) [".git" "result"])
        ./.;

    buildInputs = with pythonPackages; [
      package
      sphinx
      sphinx_rtd_theme
    ];

    buildPhase = ''
      cd docs;
      sphinx-apidoc -o source/ ../dftfit
      sphinx-build -b html -d build/doctrees . build/html
    '';

    installPhase = ''
     mkdir -p $out
     cp -r build/html/* $out
     touch $out/.nojekyll
    '';
  };

  docker = pkgs.dockerTools.buildLayeredImage {
    name = "dftfit-docker";
    tag = "latest";
    contents = [
      (pythonPackages.python.withPackages
        (ps: with ps; [ jupyterlab package ipython ]))
    ];
    config.Cmd = [ "ipython" ];
    maxLayers = 120;
  };
}
