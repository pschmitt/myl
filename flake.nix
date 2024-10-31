{
  description = "Flake for myl IMAP CLI client and myl-discovery, compatible with multiple systems";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    myl-discovery.url = "github:pschmitt/myl-discovery";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      myl-discovery,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

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
            myl-discovery.packages.${system}.myl-discovery
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

        devShell = pkgs.mkShell {
          name = "myl-devshell";

          buildInputs = [
            pkgs.python3
            pkgs.python3Packages.setuptools
            pkgs.python3Packages.setuptools-scm
            pkgs.python3Packages.html2text
            pkgs.python3Packages.imap-tools
            self.packages.${system}.myl-discovery
            pkgs.python3Packages.rich
          ];

          # Additional development tools
          nativeBuildInputs = [
            pkgs.gh # GitHub CLI
            pkgs.git
            pkgs.python3Packages.ipython
            pkgs.neovim
          ];

          # Environment variables and shell hooks
          shellHook = ''
            export PYTHONPATH=${self.packages.${system}.myl}/lib/python3.x/site-packages
            echo -e "\e[34mWelcome to the myl development shell!\e[0m"
            # Activate a virtual environment if desired
            # source .venv/bin/activate
          '';

          # Optional: Set up a Python virtual environment
          # if you prefer using virtualenv or similar tools
          # you can uncomment and configure the following lines
          # shellHook = ''
          #   if [ ! -d .venv ]; then
          #     python3 -m venv .venv
          #     source .venv/bin/activate
          #     pip install --upgrade pip
          #   else
          #     source .venv/bin/activate
          #   fi
          # '';
        };
      in
      {
        # pkgs
        packages.myl = myl;
        defaultPackage = myl;

        devShells.default = devShell;
      }
    );
}
