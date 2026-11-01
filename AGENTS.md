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
