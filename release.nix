{ pkgs ? import <nixpkgs> { } }:

let build = import ./build.nix {
      inherit pkgs;
      pythonPackages = pkgs.python3Packages;
    };
in {
  dftfit = build.package;
  dftfit-docs = build.docs;
  dftfit-docker = build.docker;
}
