# 📧 myl

myl is a dead simple IMAP CLI client hosted on GitHub at
https://github.com/pschmitt/myl

## 📝 Description

myl is a command-line interface client for IMAP, designed to provide a
straightforward way to interact with IMAP servers.

## ⭐ Features

- Simple command-line interface
- Support for various IMAP operations
- Autodiscovery of the required server and port
- Support for Google IMAP settings
- Fetch a specific number of messages
- Mark messages as seen
- Fetch messages from a specific folder
- Search for specific strings in messages
- Output HTML email
- Output raw email
- Fetch a specific mail by ID
- Fetch a specific attachment

## 🚀 Installation

To install myl, follow these steps:

```shell
pipx install myl
# or:
pip install --user myl
```

on nix you can do this:

```shell
nix run github:pschmitt/myl -- --help
```

## 🛠️ Usage

Here's how you can use myl:

```shell
myl --help
```

This command will display the help information for the `myl` command.

Here are some examples of using flags with the `myl` command:

```shell
# Connect to an IMAP server
myl --server imap.example.com --port 143 --starttls --username "$username" --password "$password"

# Use Google IMAP settings
myl --google --username "$username" --password "$password"

# Autodiscovery of the required server and port
myl --auto --username "$username" --password "$password"

# We won't repeat the server connection flags from here
alias myl="command myl --auto --username \"$username\" --password \"$password\""

# Fetch a specific number of messages
myl --count 5

# Mark messages as seen
myl --mark-seen

# Fetch messages from a specific folder
myl --folder "INBOX"

# Search for specific strings in messages
myl --search "important"

# Fetch a specific mail ID
myl "$MAILID"

# Show HTML
myl --html "$MAILID"

# raw email
myl --raw "$MAILID" > email.eml

# Fetch a specific attachment (outputs to stdout)
myl "$MAILID" "$ATT" > att.txt
```

Please replace `imap.example.com`, `$username`, `$password`, `$MAILID`,
and `$ATT` with your actual IMAP server details, username, password,
mail ID, and attachment name.

## 📜 License

This project is licensed under the GPL-3.0 license.
