import argparse
import logging
import sys

import imap_tools
from rich.console import Console
from rich.table import Table

LOGGER = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--server", help="IMAP server address", required=True
    )
    parser.add_argument("-P", "--port", help="IMAP server port", default=143)
    parser.add_argument("--starttls", help="Start TLS", action="store_true")
    parser.add_argument(
        "-u", "--username", help="IMAP username", required=True
    )
    parser.add_argument(
        "-p", "--password", help="IMAP password", required=True
    )
    parser.add_argument(
        "-t", "--no-title", help="Do not show title", action="store_true"
    )
    parser.add_argument("-f", "--folder", help="IMAP folder", default="INBOX")
    parser.add_argument("-w", "--wrap", help="Wrap text", action="store_true")
    parser.add_argument("-H", "--html", help="Show HTML", action="store_true")
    parser.add_argument("MAILID", help="Mail ID to fetch", nargs="?")
    return parser.parse_args()


def main():
    args = parse_args()

    table = Table(
        expand=True,
        show_header=not args.no_title,
        header_style="bold",
        show_lines=False,
        box=None,
    )
    table.add_column("ID", style="red", no_wrap=not args.wrap, max_width=10)
    table.add_column(
        "Subject", style="green", no_wrap=not args.wrap, max_width=30
    )
    table.add_column("From", style="blue", no_wrap=not args.wrap, max_width=30)
    table.add_column("Date", style="cyan", no_wrap=not args.wrap)

    try:
        mb = imap_tools.MailBoxTls if args.starttls else imap_tools.MailBox

        with mb(args.server, port=args.port).login(
            args.username, args.password, args.folder
        ) as mailbox:
            if args.MAILID:
                msg = [x for x in mailbox.fetch(f"UID {args.MAILID}")][0]
                print(msg.text if not args.html else msg.html)
                return 0

            for msg in mailbox.fetch():
                table.add_row(
                    msg.uid,
                    msg.subject,
                    msg.from_,
                    msg.date.strftime("%d/%m/%Y %H:%M"),
                )

        console = Console()
        console.print(table)
        return 0
    except Exception as e:
        LOGGER.error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
