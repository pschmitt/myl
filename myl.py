#!/usr/bin/env python3
# coding: utf-8

from importlib.metadata import version, PackageNotFoundError
import argparse
import logging
import ssl
import sys
from json import dumps as json_dumps

import html2text
from imap_tools.consts import MailMessageFlags
from imap_tools.mailbox import (
    BaseMailBox,
    MailBox,
    MailBoxTls,
    MailBoxUnencrypted,
)
from imap_tools.query import AND
from myldiscovery import autodiscover
from rich import print, print_json
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

try:
    __version__ = version("myl")
except PackageNotFoundError:
    pass

LOGGER = logging.getLogger(__name__)
IMAP_PORT = 993
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = IMAP_PORT
GMAIL_SENT_FOLDER = "[Gmail]/Sent Mail"
# GMAIL_ALL_FOLDER = "[Gmail]/All Mail"


class MissingServerException(Exception):
    pass


def error_msg(msg):
    print(f"[red]{msg}[/red]", file=sys.stderr)


def mail_to_dict(msg, date_format="%Y-%m-%d %H:%M:%S"):
    return {
        "uid": msg.uid,
        "subject": msg.subject,
        "from": msg.from_,
        "to": msg.to,
        "date": msg.date.strftime(date_format),
        "timestamp": str(int(msg.date.timestamp())),
        "unread": mail_is_unread(msg),
        "flags": msg.flags,
        "content": {
            "raw": msg.obj.as_string(),
            "html": msg.html,
            "text": msg.text,
        },
        "attachments": msg.attachments,
    }


def mail_to_json(msg, date_format="%Y-%m-%d %H:%M:%S"):
    return json_dumps(mail_to_dict(msg, date_format))


def mail_is_unread(msg):
    return MailMessageFlags.SEEN not in msg.flags


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Default command: list all emails
    subparsers.add_parser("list", help="List all emails")

    # Get/show email command
    get_parser = subparsers.add_parser(
        "get", help="Retrieve a specific email or attachment"
    )
    get_parser.add_argument("MAILID", help="Mail ID to fetch", type=int)
    get_parser.add_argument(
        "ATTACHMENT",
        help="Name of the attachment to fetch",
        nargs="?",
        default=None,
    )

    # get most recent email
    last_parser = subparsers.add_parser(
        "last", aliases=["-1"], help="Retrieve the most recent email"
    )
    last_parser.add_argument(
        "ATTACHMENT",
        help="Name of the attachment to fetch",
        nargs="?",
        default=None,
    )

    # Delete email command
    delete_parser = subparsers.add_parser("delete", help="Delete an email")
    delete_parser.add_argument(
        "MAILIDS", help="Mail ID(s) to delete", type=int, nargs="+"
    )

    # Mark email as read/unread
    mark_read_parser = subparsers.add_parser(
        "read", help="mark an email as read"
    )
    mark_read_parser.add_argument(
        "MAILIDS", help="Mail ID(s) to mark as read", type=int, nargs="+"
    )
    mark_unread_parser = subparsers.add_parser(
        "unread", help="mark an email as unread"
    )
    mark_unread_parser.add_argument(
        "MAILIDS", help="Mail ID(s) to mark as unread", type=int, nargs="+"
    )

    # Optional arguments
    parser.add_argument(
        "-d", "--debug", help="Enable debug mode", action="store_true"
    )

    # IMAP connection settings
    parser.add_argument(
        "-s", "--server", help="IMAP server address", required=False
    )
    parser.add_argument(
        "--google",
        "--gmail",
        help="Use Google IMAP settings (overrides --port, --server etc.)",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-a",
        "--auto",
        help="Autodiscovery of the required server and port",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-P", "--port", help="IMAP server port", default=IMAP_PORT
    )
    parser.add_argument("--ssl", help="SSL", action="store_true", default=True)
    parser.add_argument(
        "--starttls", help="STARTTLS", action="store_true", default=False
    )
    parser.add_argument(
        "--insecure",
        help="Disable cert validation",
        action="store_true",
        default=False,
    )

    # Credentials
    parser.add_argument(
        "-u", "--username", help="IMAP username", required=True
    )
    password_group = parser.add_mutually_exclusive_group(required=True)
    password_group.add_argument("-p", "--password", help="IMAP password")
    password_group.add_argument(
        "--password-file",
        help="IMAP password (file path)",
        type=argparse.FileType("r"),
    )

    # Display preferences
    parser.add_argument(
        "-c",
        "--count",
        help="Number of messages to fetch",
        default=10,
        type=int,
    )
    parser.add_argument(
        "-t", "--no-title", help="Do not show title", action="store_true"
    )
    parser.add_argument(
        "--date-format", help="Date format", default="%H:%M %d/%m/%Y"
    )

    # IMAP actions
    parser.add_argument(
        "-m",
        "--mark-seen",
        help="Mark seen",
        action="store_true",
        default=False,
    )

    # Email filtering
    parser.add_argument("-f", "--folder", help="IMAP folder", default="INBOX")
    parser.add_argument(
        "--sent",
        help="Sent email",
        action="store_true",
    )
    parser.add_argument("-S", "--search", help="Search string", default="ALL")
    parser.add_argument(
        "--unread",
        help="Limit to unread emails",
        action="store_true",
        default=False,
    )

    # Output preferences
    parser.add_argument(
        "-H",
        "--html",
        help="Show HTML email",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-j",
        "--json",
        help="JSON output",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-r",
        "--raw",
        help="Show the raw email",
        action="store_true",
        default=False,
    )

    return parser.parse_args()


def mb_connect(console, args) -> BaseMailBox:
    imap_password = args.password or (
        args.password_file and args.password_file.read()
    )

    if args.google:
        args.server = GMAIL_IMAP_SERVER
        args.port = GMAIL_IMAP_PORT
        args.starttls = False

        if args.sent or args.folder == "Sent":
            args.folder = GMAIL_SENT_FOLDER
        # elif args.folder == "INBOX":
        #     args.folder = GMAIL_ALL_FOLDER
    else:
        if args.auto:
            try:
                settings = autodiscover(
                    args.username,
                    password=imap_password,
                    insecure=args.insecure,
                ).get("imap", {})
            except Exception:
                error_msg("Failed to autodiscover IMAP settings")
                if args.debug:
                    console.print_exception(show_locals=True)
                raise

            LOGGER.debug(f"Discovered settings: {settings})")
            args.server = settings.get("server")
            args.port = settings.get("port", IMAP_PORT)
            args.starttls = settings.get("starttls")
            args.ssl = settings.get("ssl")

        if args.sent:
            args.folder = "Sent"

    if not args.server:
        error_msg(
            "No server specified\n"
            "You need to either:\n"
            "- specify a server using --server HOSTNAME\n"
            "- set --google if you are using a Gmail account\n"
            "- use --auto to attempt autodiscovery"
        )
        raise MissingServerException()

    ssl_context = ssl.create_default_context()
    if args.insecure:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    mb_kwargs = {"host": args.server, "port": args.port}
    if args.ssl:
        mb = MailBox
        mb_kwargs["ssl_context"] = ssl_context
    elif args.starttls:
        mb = MailBoxTls
        mb_kwargs["ssl_context"] = ssl_context
    else:
        mb = MailBoxUnencrypted

    mailbox = mb(**mb_kwargs)
    mailbox.login(args.username, imap_password, args.folder)
    return mailbox


def display_single_mail(
    mailbox: BaseMailBox,
    mail_id: int | None = None,
    attachment: str | None = None,
    mark_seen: bool = False,
    raw: bool = False,
    html: bool = False,
    json: bool = False,
):
    if mail_id is None:
        LOGGER.debug("No mail_id provided, fetching the most recent mail")
        msg = next(
            mailbox.fetch(
                "ALL", reverse=True, bulk=True, limit=1, mark_seen=mark_seen
            )
        )
    else:
        LOGGER.debug("Fetch mail %s", mail_id)
        msg = next(mailbox.fetch(f"UID {mail_id}", mark_seen=mark_seen))
    LOGGER.debug("Fetched mail %s", msg)

    if attachment:
        for att in msg.attachments:
            if att.filename == attachment:
                sys.stdout.buffer.write(att.payload)
                return 0
        print(
            f"attachment {attachment} not found",
            file=sys.stderr,
        )
        return 1

    if html:
        output = msg.text
        if raw:
            output = msg.html
        else:
            output = html2text.html2text(msg.html)
        print(output)
    elif raw:
        print(msg.obj.as_string())
        return 0
    elif json:
        print_json(mail_to_json(msg))
        return 0
    else:
        print(msg.text)

    for att in msg.attachments:
        print(f"📎 Attachment: {att.filename}", file=sys.stderr)
    return 0


def display_emails(
    mailbox,
    console,
    no_title=False,
    search="ALL",
    unread_only=False,
    count=10,
    mark_seen=False,
    json=False,
    date_format="%H:%M %d/%m/%Y",
):
    json_data = []
    table = Table(
        show_header=not no_title,
        header_style="bold",
        expand=True,
        show_lines=False,
        show_edge=False,
        pad_edge=False,
        box=None,
        row_styles=["", "dim"],
    )
    table.add_column("ID", style="red", no_wrap=True)
    table.add_column("Subject", style="green", no_wrap=True, ratio=3)
    table.add_column("From", style="blue", no_wrap=True, ratio=2)
    table.add_column("Date", style="cyan", no_wrap=True)

    if unread_only:
        search = AND(seen=False)

    for msg in mailbox.fetch(
        criteria=search,
        reverse=True,
        bulk=True,
        limit=count,
        mark_seen=mark_seen,
        headers_only=False,  # required for attachments
    ):
        subj_prefix = "🆕 " if mail_is_unread(msg) else ""
        subj_prefix += "📎 " if len(msg.attachments) > 0 else ""
        subject = (
            msg.subject.replace("\n", "") if msg.subject else "<no-subject>"
        )
        if json:
            json_data.append(mail_to_dict(msg))
        else:
            table.add_row(
                msg.uid if msg.uid else "???",
                f"{subj_prefix}{subject}",
                msg.from_,
                (msg.date.strftime(date_format) if msg.date else "???"),
            )
        if table.row_count >= count:
            break

    if json:
        print_json(json_dumps(json_data))
    else:
        console.print(table)
        if table.row_count == 0:
            print(
                "[yellow italic]No messages[/yellow italic]",
                file=sys.stderr,
            )
    return 0


def delete_emails(mailbox: BaseMailBox, mail_ids: list):
    LOGGER.warning("Deleting mails %s", mail_ids)
    mailbox.delete([str(x) for x in mail_ids])
    return 0


def set_seen(mailbox: BaseMailBox, mail_ids: list, value=True):
    LOGGER.info(
        "Marking mails as %s: %s", "read" if value else "unread", mail_ids
    )
    mailbox.flag(
        [str(x) for x in mail_ids],
        flag_set=(MailMessageFlags.SEEN),
        value=value,
    )
    return 0


def mark_read(mailbox: BaseMailBox, mail_ids: list):
    return set_seen(mailbox, mail_ids, value=True)


def mark_unread(mailbox: BaseMailBox, mail_ids: list):
    return set_seen(mailbox, mail_ids, value=False)


def main() -> int:
    console = Console()
    args = parse_args()
    logging.basicConfig(
        format="%(message)s",
        handlers=[RichHandler(console=console)],
        level=logging.DEBUG if args.debug else logging.INFO,
    )
    LOGGER.debug(args)

    try:
        with mb_connect(console, args) as mailbox:
            # inbox display
            if args.command in ["list", None]:
                return display_emails(
                    mailbox=mailbox,
                    console=console,
                    no_title=args.no_title,
                    search=args.search,
                    unread_only=args.unread,
                    count=args.count,
                    mark_seen=args.mark_seen,
                    json=args.json,
                    date_format=args.date_format,
                )

            # single email
            # FIXME $ myl 219 raises an argparse error
            elif args.command in ["get", "show", "display"]:
                return display_single_mail(
                    mailbox=mailbox,
                    mail_id=args.MAILID,
                    attachment=args.ATTACHMENT,
                    mark_seen=args.mark_seen,
                    raw=args.raw,
                    html=args.html,
                    json=args.json,
                )

            elif args.command in ["-1", "last"]:
                return display_single_mail(
                    mailbox=mailbox,
                    mail_id=None,
                    attachment=args.ATTACHMENT,
                    mark_seen=args.mark_seen,
                    raw=args.raw,
                    html=args.html,
                    json=args.json,
                )

            # mark emails as read
            elif args.command in ["read"]:
                return mark_read(
                    mailbox=mailbox,
                    mail_ids=args.MAILIDS,
                )

            elif args.command in ["unread"]:
                return mark_unread(
                    mailbox=mailbox,
                    mail_ids=args.MAILIDS,
                )

            # delete email
            elif args.command in ["delete", "remove"]:
                return delete_emails(
                    mailbox=mailbox,
                    mail_ids=args.MAILIDS,
                )
            else:
                error_msg(f"Unknown command: {args.command}")
                return 1

    except Exception:
        console.print_exception(show_locals=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
