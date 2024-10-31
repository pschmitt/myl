{
  description = "flake for myl IMAP CLI client and myl-discovery";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      pkgs = import nixpkgs {
        system = "x86_64-linux";
      };
    in
    {
      packages.x86_64-linux.default = self.packages.x86_64-linux.myl;
      packages.x86_64-linux.myl = pkgs.python3.pkgs.buildPythonApplication {
        pname = "myl";
        version = builtins.readFile ./version.txt;
        pyproject = true;

        src = ./.;

        buildInputs = [
          pkgs.python3.pkgs.setuptools
          pkgs.python3.pkgs.setuptools-scm
        ];

        propagatedBuildInputs = with pkgs.python3.pkgs; [
          html2text
          imap-tools
          self.packages.x86_64-linux.myl-discovery
          rich
        ];

        meta = {
          description = "Dead simple IMAP CLI client";
          homepage = "https://pypi.org/project/myl/";
          license = pkgs.lib.licenses.gpl3Only;
          maintainers = with pkgs.lib.maintainers; [ pschmitt ];
          mainProgram = "myl";
        };
      };

      packages.x86_64-linux.myl-discovery = pkgs.python3.pkgs.buildPythonApplication rec {
        pname = "myl-discovery";
        version = "0.6.1";
        pyproject = true;

        src = pkgs.fetchPypi {
          pname = "myl_discovery";
          inherit version;
          hash = "sha256-5ulMzqd9YovEYCKO/B2nLTEvJC+bW76pJtDu1cNXLII=";
        };

        buildInputs = [
          pkgs.python3.pkgs.setuptools
          pkgs.python3.pkgs.setuptools-scm
        ];

        propagatedBuildInputs = with pkgs.python3.pkgs; [
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
          mainProgram = "myl-discovery";
        };
      };
    };
}

