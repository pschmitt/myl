# Agent notes

`myl` is a Python IMAP command-line client with support for mail-server
autodiscovery.

- Preserve the commands and options documented in `README.md`.
- Run the repository's Python lint workflow and add focused tests for behavior
  changes.
- Use a test mailbox for integration checks; avoid marking messages seen or
  otherwise changing a personal mailbox during validation.
- Before changing workflows, check for reusable workflows or actions in
  [ci-workflows](https://github.com/pschmitt/ci-workflows) and preserve
  existing triggers, parameters, and check coverage.
- Keep `packages.default` canonical and retain the named `myl` and
  `myl-discovery` package outputs; do not add the legacy `defaultPackage` alias.
- The Python dev shell should inherit app dependencies with `inputsFrom` and
  include the checkout in `PYTHONPATH` for direct source imports.
- Run Nix evaluation and builds on an `rworker`, never on the local host.
- The flake tracks the final Nixpkgs release that supports `x86_64-darwin`
  (`nixpkgs-26.05-darwin`). Keep that targeted pin while Intel macOS support
  is part of the package contract; Nixpkgs 26.11 and later drop the platform.
