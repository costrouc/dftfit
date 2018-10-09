{ pkgs ? import <nixpkgs> {}, pythonPackages ? "python36Packages" }:

let
  elem = builtins.elem;
  basename = path: with pkgs.lib; last (splitString "/" path);
  startsWith = prefix: full: let
    actualPrefix = builtins.substring 0 (builtins.stringLength prefix) full;
  in actualPrefix == prefix;

  src-filter = path: type: with pkgs.lib;
    let
      ext = last (splitString "." path);
    in
      !elem (basename path) [".git" "__pycache__" ".eggs"] &&
      !elem ext ["egg-info" "pyc"] &&
      !startsWith "result" path;

   basePythonPackages = if builtins.isAttrs pythonPackages
     then pythonPackages
     else builtins.getAttr pythonPackages pkgs;
in
basePythonPackages.buildPythonPackage rec {
  pname = "dftfit";
  version = "0.5.0";
  disabled = (!basePythonPackages.isPy3k);

  src = builtins.filterSource src-filter ./.;

  buildInputs = with basePythonPackages; [ pytestrunner pkgs.lammps ];
  checkInputs = with basePythonPackages; [ pytest pytestcov pytest-benchmark pkgs.openssh ];
  propagatedBuildInputs = with basePythonPackages; [
      pymatgen marshmallow pyyaml pygmo
      pandas scipy numpy scikitlearn
      lammps-cython pymatgen-lammps ];

  # tests require git lfs download. and is quite large so skip tests
  doCheck = true;

  checkPhase = ''
    pytest -m "not long"
  '';

  meta = with pkgs; {
    description = "Ab-Initio Molecular Dynamics Potential Development";
    homepage = https://gitlab.com/costrouc/dftfit;
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ costrouc ];
  };
}
