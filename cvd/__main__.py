"""Entry point for `python -m cvd`."""

import sys

from .cli.run import main

if __name__ == "__main__":
    sys.exit(main())
