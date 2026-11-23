"""GenBank export."""

import datetime
import re

from ..model import Design
from ..parts.elements import KINDS


def _ascii(text: str) -> str:
    return text.encode("ascii", "replace").decode().replace('"', "")


def to_genbank(d: Design) -> str:
    today = datetime.date.today()
    mon = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()[today.month - 1]
    # re.ASCII keeps the LOCUS name ASCII: GenBank has no encoding for anything else,
    # and an unflagged \w matches Unicode letters.
    locus = re.sub(r"[^\w.-]", "_", d.name, flags=re.ASCII)[:16]
    out = ["LOCUS       %-16s %7d bp    DNA     circular SYN %02d-%s-%d" % (locus, d.total, today.day, mon, today.year),
           "DEFINITION  %s, designed with Cancer Gene Therapy Vector Designer." % _ascii(d.name),
           "FEATURES             Location/Qualifiers"]
    for f in d.features:
        out.append("     %-16s%d..%d" % (KINDS[f.kind][1], f.start, f.end))
        out.append('                     /label="%s"' % _ascii(f.name))
    out.append("ORIGIN")
    s = d.seq.lower()
    for i in range(0, len(s), 60):
        line = s[i:i + 60]
        out.append("%9d %s" % (i + 1, " ".join(line[j:j + 10] for j in range(0, len(line), 10))))
    out.append("//")
    return "\n".join(out) + "\n"
