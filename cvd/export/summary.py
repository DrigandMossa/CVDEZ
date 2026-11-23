"""Human-readable text summary of a design."""

from ..model import Design
from ..parts.strategies import STRATEGIES


def to_summary(d: Design) -> str:
    lines = [d.name, "=" * len(d.name),
             "Vector: %s    Strategy: %s    Size: %s bp" % (d.vector, STRATEGIES[d.strategy]["name"], format(d.total, ",")),
             "", "%-8s %-14s %7s  %s" % ("id", "position", "bp", "element")]
    for f in d.features:
        note = "  (your sequence)" if f.custom or f.id in ("goi", "guide") and "N" not in f.seq else ""
        lines.append("%-8s %-14s %7d  %s%s" % (f.id, "%d..%d" % (f.start, f.end), f.length, f.name, note))
    lines += ["", "Design checks"] + ["  [%s] %s" % (lv, tx) for lv, tx in d.messages]
    if d.basis:
        lines += ["", "Design basis", d.basis]
    lines += ["", "Elements written as N have a typical length only. Supply verified sequences with",
              "--override ID=SEQUENCE (ids are in the first column) or --seq for the insert."]
    return "\n".join(lines) + "\n"
