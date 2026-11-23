"""FASTA export."""

import re

from ..model import Design


def to_fasta(d: Design) -> str:
    header = ">%s %d bp circular" % (re.sub(r"\s+", "_", d.name), d.total)
    return header + "\n" + "\n".join(d.seq[i:i + 70] for i in range(0, d.total, 70)) + "\n"
