"""Command line for the tutorial: python -m cvdez"""

import argparse
import sys
from typing import List, Optional

from .lessons import LESSONS, Context
from .ui import Console, Quit
from .version import __version__


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cvdez", description="CVDEZ: a hands-on tutorial that runs inside the real CVD gene therapy vector designer. "
                                  "With no options it opens the CVD window with a coach beside it.")
    p.add_argument("--part", type=int, choices=(1, 2), default=1,
                   help="start the window tutorial at Part 1 (tour of every control) or Part 2 (build your own example)")
    p.add_argument("--console", action="store_true",
                   help="use the text-only tutorial in the terminal instead of the CVD window (also used when tkinter is missing)")
    p.add_argument("--auto", action="store_true", help="run every lesson without questions, taking the default answer each time")
    p.add_argument("--lesson", type=int, metavar="N", help="(text tutorial) start at lesson N (1 to %d)" % len(LESSONS))
    p.add_argument("--list", action="store_true", help="list the steps of the window tutorial and the lessons of the text tutorial, then exit")
    p.add_argument("--out", default="cvdez_output", help="folder for the files the tutorial writes (default: cvdez_output)")
    p.add_argument("--version", action="version", version="cvdez %s" % __version__)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        from .steps import STEPS
        print("Window tutorial (python -m cvdez):")
        for i, st in enumerate(STEPS, 1):
            print("%3d. [part %d] %s" % (i, st.part, st.title))
        print("\nText tutorial (python -m cvdez --console):")
        for i, (title, _) in enumerate(LESSONS, 1):
            print("%3d. %s" % (i, title))
        return 0
    if not (args.console or args.auto or args.lesson):
        status = _window(args)
        if status != -1:
            return status
        print("Falling back to the text tutorial.\n", file=sys.stderr)
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


def _window(args) -> int:
    """Open the real CVD window with the coach.  Returns -1 when no window is possible."""
    try:
        from .coach import launch
    except ImportError:
        print("The window tutorial needs tkinter, which is not installed. On Debian/Ubuntu run: sudo apt install python3-tk",
              file=sys.stderr)
        return -1
    status = launch(args.out, args.part)
    return -1 if status == 2 else status


class _Null:
    def write(self, s):
        return len(s)

    def flush(self):
        pass
