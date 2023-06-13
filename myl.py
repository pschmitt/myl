import argparse
import logging
import re
import sys

import dns.resolver
import imap_tools
import requests
import xmltodict
from rich import print
from rich.console import Console
from rich.table import Table

LOGGER = logging.getLogger(__name__)
GMAIL_IMAP_SERVER = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
GMAIL_SENT_FOLDER = "[Gmail]/Sent Mail"
# GMAIL_ALL_FOLDER = "[Gmail]/All Mail"


def error_msg(msg):
    print(f"[red]{msg}[/red]", file=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser()
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
    parser.add_argument(
        "--sent",
        help="Sent email",
        action="store_true",
    )
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

    args = parser.parse_args()

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
            settings = autodiscover(args.username)
            args.server = settings.get("server")
            args.port = settings.get("port")
            args.starttls = settings.get("starttls")
        if args.sent:
            args.folder = "Sent"

    if not args.server:
        error_msg("No server specified")
        parser.print_help()
        sys.exit(2)

    return args


def resolve_txt(domain, criteria="^mailconf="):
    regex = re.compile(criteria)
    answers = dns.resolver.resolve(domain, "TXT")
    for rdata in answers:
        for txt_string in rdata.strings:
            txt_record = txt_string.decode("utf-8")
            if re.search(regex, txt_record):
                return txt_record


def resolve_srv(domain):
    answers = dns.resolver.resolve(domain, "SRV")
    data = []
    for rdata in answers:
        entry = {
            "hostname": ".".join(
                [
                    x.decode("utf-8")
                    for x in rdata.target.labels
                    if x.decode("utf-8") != ""
                ]
            ),
            "port": rdata.port,
        }
        data.append(entry)

    return data


# TODO export this a separate library
def autodiscover(email_addr):
    domain = email_addr.split("@")[-1]
    if not domain:
        raise ValueError(f"Invalid email address {email_addr}")

    autoconfig = None  # resolve_txt(domain)

    if not autoconfig:
        srv = resolve_srv(f"_imaps._tcp.{domain}")
        return {
            "server": srv[0].get("hostname"),
            "port": srv[0].get("port"),
            "starttls": False,
        }

    res = requests.get(autoconfig)
    res.raise_for_status()

    data = xmltodict.parse(res.text)
    imap = (
        data.get("clientConfig", {})
        .get("emailProvider", {})
        .get("incomingServer")
    )
    assert imap is not None
    return {
        "server": imap.get("hostname"),
        "port": imap.get("port"),
        "starttls": imap.get("socketType") == "STARTTLS",
    }


def main():
    console = Console()

    try:
        args = parse_args()

        table = Table(
            expand=True,
            show_header=not args.no_title,
            header_style="bold",
            show_lines=False,
            box=None,
        )
        table.add_column(
            "ID", style="red", no_wrap=not args.wrap, max_width=10
        )
        table.add_column(
            "Subject", style="green", no_wrap=not args.wrap, max_width=30
        )
        table.add_column(
            "From", style="blue", no_wrap=not args.wrap, max_width=30
        )
        table.add_column("Date", style="cyan", no_wrap=not args.wrap)
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

        console.print(table)
        return 0
    except Exception:
        console.print_exception(show_locals=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
