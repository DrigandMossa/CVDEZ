"""Command line for the tutorial: python -m cvdez"""

import argparse
import sys
from typing import List, Optional

from .lessons import LESSONS, Context
from .ui import Console, Quit
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cvdez", description="CVDEZ: a step-by-step tutorial for the CVD gene therapy vector designer.")
    p.add_argument("--auto", action="store_true", help="run every lesson without questions, taking the default answer each time")
    p.add_argument("--lesson", type=int, metavar="N", help="start at lesson N (1 to %d)" % len(LESSONS))
    p.add_argument("--list", action="store_true", help="list the lessons and exit")
    p.add_argument("--out", default="cvdez_output", help="folder for the files the tutorial writes (default: cvdez_output)")
    p.add_argument("--version", action="version", version="cvdez %s" % __version__)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        for i, (title, _) in enumerate(LESSONS, 1):
            print("%2d. %s" % (i, title))
        return 0
    start = args.lesson or 1
    if not 1 <= start <= len(LESSONS):
        print("Error: --lesson must be between 1 and %d." % len(LESSONS), file=sys.stderr)
        return 2
    ui = Console(auto=args.auto)
    ctx = Context(ui, args.out)
    try:
        # Lessons build on each other, so starting late still runs the quiet setup the earlier lessons would have done.
        if start > 1:
            quiet = Console(auto=True, out=_Null())
            qctx = Context(quiet, args.out)
            for _, fn in LESSONS[:start - 1]:
                fn(qctx)
            qctx.ui = ui
            ctx = qctx
        for _, fn in LESSONS[start - 1:]:
            fn(ctx)
    except Quit:
        print("\nLeaving the tutorial. Run it again any time; use --lesson N to jump back in.")
        return 0
    except (ValueError, OSError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    return 0


class _Null:
    def write(self, s):
        return len(s)

    def flush(self):
        pass
