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
- Fetch a specific attachment (outputs to stdout)

## 🚀 Installation

To install myl, follow these steps:

```bash
pipx install myl
```

## 🛠️ Usage

Here's how you can use myl:

```bash
myl --help
```

This command will display the help information for the `myl` command.

Here are some examples of using flags with the `myl` command:

```bash
# Connect to an IMAP server
myl --server imap.example.com --username $username --password "$password"

# Use Google IMAP settings
myl --google --username "$username" --password "$password"

# Autodiscovery of the required server and port
myl --auto --username "$username" --password "$password"

# Fetch a specific number of messages
myl --count 5 --username "$username" --password "$password"

# Mark messages as seen
myl --mark-seen --username "$username" --password "$password"

# Fetch messages from a specific folder
myl --folder "INBOX" --username "$username" --password "$password"

# Search for specific strings in messages
myl --search "important" --username "$username" --password "$password"

# Show raw email
myl --raw --username "$username" --password "$password"

# Fetch a specific mail ID
myl --username "$username" --password "$password" "$MAILID"

# Show HTML
myl --html --username "$username" --password "$password" "$MAILID"

# raw email
myl --raw --username "$username" --password "$password" "$MAILID" > email.eml

# Fetch a specific attachment (outputs to stdout)
myl --username "$username" --password "$password" "$MAILID" "$ATT" > att.txt
```

Please replace `imap.example.com`, `$username`, `$password`, `$MAILID`,
and `$ATT` with your actual IMAP server details, username, password,
mail ID, and attachment name.

## 📜 License

This project is licensed under the GPL-3.0 license.
