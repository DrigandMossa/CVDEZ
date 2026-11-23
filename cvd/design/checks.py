"""Sequence-level design checks that produce the (level, text) message list."""

import re

from ..parts.enzymes import RESTRICTION_SITES
from ..seqops import count_overlapping, gc_percent


def check_insert(msgs: list, seq: str, label: str, vector: str, check_atg: bool) -> None:
    n = len(seq)
    if n % 3:
        msgs.append(("warn", "%s length (%d bp) is not a multiple of 3." % (label, n)))
    else:
        stops, first = 0, 0
        for i in range(0, n - 3, 3):
            if seq[i:i + 3] in ("TAA", "TAG", "TGA"):
                stops += 1
                first = first or i // 3 + 1
        if stops:
            msgs.append(("error", "%d in-frame stop codon(s) inside %s; the first is at codon %d. "
                         "Check the reading frame, or confirm the premature stop is intended." % (stops, label, first)))
    if check_atg and not seq.startswith("ATG"):
        msgs.append(("warn", "%s does not start with ATG." % label))
    if n % 3 == 0 and seq[-3:] in ("TAA", "TAG", "TGA"):
        msgs.append(("warn", "%s ends in a stop codon. Remove it if you use a tag or a P2A reporter." % label))
    msgs.append(("info", "%s: %s bp, %d%% GC." % (label, format(n, ","), gc_percent(seq))))
    if vector == "lenti" and re.search("AATAAA|ATTAAA", seq):
        msgs.append(("warn", "%s contains a polyadenylation signal (AATAAA or ATTAAA). In a lentiviral genome "
                     "this can truncate the vector RNA and lower titer." % label))
    free, cut = [], []
    for enzyme, site in RESTRICTION_SITES.items():
        c = count_overlapping(seq, site)
        (cut.append("%s x%d" % (enzyme, c)) if c else free.append(enzyme))
    text = "Restriction sites in %s: none for %s." % (label, ", ".join(free) or "any listed enzyme")
    if cut:
        text += " Cut by %s." % ", ".join(cut)
    msgs.append(("info", text))
