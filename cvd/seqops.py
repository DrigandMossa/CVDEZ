"""Pure sequence and option helpers.  No dependencies on the parts library."""

import re
from typing import Tuple


_COMP = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}


def clean_sequence(text: str) -> Tuple[str, int]:
    """Strip FASTA headers, whitespace and digits; U -> T. Returns (ACGTN, removed)."""
    text = re.sub(r"^>.*$", "", text or "", flags=re.M)
    text = re.sub(r"[\s\d]", "", text).upper().replace("U", "T")
    kept = re.sub(r"[^ACGTN]", "", text)
    return kept, len(text) - len(kept)


def revcomp(seq: str) -> str:
    return "".join(_COMP[c] for c in reversed(seq))


def gc_percent(seq: str) -> int:
    return round(100 * sum(c in "GC" for c in seq) / len(seq)) if seq else 0


def count_overlapping(seq: str, motif: str) -> int:
    n, i = 0, seq.find(motif)
    while i >= 0:
        n += 1
        i = seq.find(motif, i + 1)
    return n


def pick(value: str, options, what: str) -> str:
    """Case-insensitive choice from a dict/list, with a helpful error."""
    for opt in options:
        if str(opt).lower() == str(value).lower():
            return opt
    raise ValueError("Unknown %s %r. Choose from: %s" % (what, value, ", ".join(map(str, options))))
