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
- Nixpkgs is pinned to a revision that does not support `x86_64-darwin`; this
  is an existing platform limitation, not a regression in package outputs.
