{ lib
, pkgs
, pythonPackages
}:

pythonPackages.buildPythonPackage rec {
  pname = "dftfit";
  version = "a79fd4a638b6995fc329ee653d2a5ead13b47201";
  disabled = (!pythonPackages.isPy3k);

  src = ./.;

  buildInputs = with pythonPackages; [ pytestrunner ];
  checkInputs = with pythonPackages; [ pytest pytestcov pytest-benchmark pkgs.openssh ];
  propagatedBuildInputs = with pythonPackages; [
      pymatgen marshmallow pyyaml pygmo
      pandas scipy numpy scikitlearn
      lammps-cython pymatgen-lammps ];

  # tests require git lfs download. and is quite large so skip tests
  doCheck = false;

  meta = {
    description = "Ab-Initio Molecular Dynamics Potential Development";
    homepage = https://gitlab.com/costrouc/dftfit;
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ costrouc ];
  };
}
