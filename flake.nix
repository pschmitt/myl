{
  description = "Flake for myl IMAP CLI client and myl-discovery, compatible with multiple systems";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };

        myl = pkgs.python3Packages.buildPythonApplication {
          pname = "myl";
          version = builtins.readFile ./version.txt;
          pyproject = true;

          src = ./.;

          buildInputs = [
            pkgs.python3Packages.setuptools
            pkgs.python3Packages.setuptools-scm
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            html2text
            imap-tools
            self.packages.${system}.myl-discovery
            rich
          ];

          meta = {
            description = "Dead simple IMAP CLI client";
            homepage = "https://pypi.org/project/myl/";
            license = pkgs.lib.licenses.gpl3Only;
            maintainers = with pkgs.lib.maintainers; [ pschmitt ];
            platforms = pkgs.lib.platforms.all;
          };
        };

        mylDiscovery = pkgs.python3Packages.buildPythonApplication rec {
          pname = "myl-discovery";
          version = "0.6.1";
          pyproject = true;

          src = pkgs.fetchPypi {
            pname = "myl_discovery";
            inherit version;
            sha256 = "sha256-5ulMzqd9YovEYCKO/B2nLTEvJC+bW76pJtDu1cNXLII=";
          };

          buildInputs = [
            pkgs.python3Packages.setuptools
            pkgs.python3Packages.setuptools-scm
          ];

          propagatedBuildInputs = with pkgs.python3Packages; [
            dnspython
            exchangelib
            requests
            rich
            xmltodict
          ];

          pythonImportsCheck = [ "myldiscovery" ];

          meta = {
            description = "Email autodiscovery";
            homepage = "https://pypi.org/project/myl-discovery/";
            license = pkgs.lib.licenses.gpl3Only;
            maintainers = with pkgs.lib.maintainers; [ pschmitt ];
            platforms = pkgs.lib.platforms.all;
          };
        };
      in
      {
        packages.myl = myl;
        packages."myl-discovery" = mylDiscovery;
        defaultPackage = myl;
      }
    );
}
