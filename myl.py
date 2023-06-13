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
        "-c",
        "--count",
        help="Number of messages to fetch",
        default=10,
        type=int,
    )
    parser.add_argument(
        "-m", "--mark-seen", help="Mark seen", action="store_true"
    )
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
    parser.add_argument("-S", "--search", help="Search string", default="ALL")
    parser.add_argument("-w", "--wrap", help="Wrap text", action="store_true")
    parser.add_argument("-H", "--html", help="Show HTML", action="store_true")
    parser.add_argument(
        "-r",
        "--raw",
        help="Show the raw email",
        action="store_true",
        default=False,
    )
    parser.add_argument("MAILID", help="Mail ID to fetch", nargs="?")
    parser.add_argument(
        "ATTACHMENT", help="Name of the attachment to fetch", nargs="?"
    )
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
                msg = next(
                    mailbox.fetch(
                        f"UID {args.MAILID}", mark_seen=args.mark_seen
                    )
                )
                if args.ATTACHMENT:
                    for att in msg.attachments:
                        if att.filename == args.ATTACHMENT:
                            sys.stdout.buffer.write(att.payload)
                            return 0
                    print(
                        f"Attachment {args.ATTACHMENT} not found",
                        file=sys.stderr,
                    )
                    return 1
                else:
                    if args.raw:
                        print(msg.obj.as_string())
                        return 0
                    print(msg.text if not args.html else msg.html)
                    for att in msg.attachments:
                        print(f"📎 Attachment: {att.filename}", file=sys.stderr)
                return 0

            for msg in mailbox.fetch(
                criteria=args.search,
                reverse=True,
                bulk=True,
                limit=args.count,
                mark_seen=args.mark_seen,
                headers_only=False,  # required for attachments
            ):
                subj_suffix = "📎 " if len(msg.attachments) > 0 else ""
                table.add_row(
                    msg.uid if msg.uid else "???",
                    subj_suffix
                    + (msg.subject if msg.subject else "<no-subject>"),
                    msg.from_,
                    msg.date.strftime("%H:%M %d/%m/%Y") if msg.date else "???",
                )
                if len(table.rows) >= args.count:
                    break

        console = Console()
        console.print(table)
        return 0
    except Exception as e:
        LOGGER.error(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
