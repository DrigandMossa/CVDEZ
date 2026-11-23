"""Parse copy-number segment files (TSV, CSV or whitespace separated)."""

import re
from typing import List, Optional, Tuple

from ..model import Segment
from ..seqops import pick


_CHROM_NAMES = ("chrom", "chromosome", "chr", "seqnames", "seqname", "contig")
_START_NAMES = ("start", "loc.start", "begin", "startpos", "start_pos", "chromstart", "segment_start")
_END_NAMES = ("end", "loc.end", "stop", "endpos", "end_pos", "chromend", "segment_end")
_CN_NAMES = ("cn", "copy_number", "copynumber", "total_cn", "tcn", "total_copy_number", "copy.number", "tcn.em", "totalcn")
_LOG2_NAMES = ("log2", "log2ratio", "log2_ratio", "seg.mean", "segmean", "seg_mean", "logr",
               "log2_copy_ratio", "segment_mean", "mean", "value")
_SAMPLE_NAMES = ("sample", "sample_id", "sampleid", "id", "tumor_sample_barcode", "case", "barcode")


def _num(text: str) -> Optional[float]:
    try:
        return float(text)
    except ValueError:
        return None


def norm_chrom(name: str) -> Optional[str]:
    """'chr7' -> '7', '23' -> 'X'. Returns None for mitochondrial and unplaced contigs."""
    s = re.sub(r"^chr", "", name.strip(), flags=re.I).upper()
    if s in ("X", "23"):
        return "X"
    if s in ("Y", "24"):
        return "Y"
    return str(int(s)) if s.isdigit() and 1 <= int(s) <= 22 else None


def weighted_median(pairs: List[Tuple[float, float]]) -> float:
    pairs = sorted(p for p in pairs if p[1] > 0)
    total, acc = sum(w for _, w in pairs), 0.0
    for value, weight in pairs:
        acc += weight
        if acc >= total / 2:
            return value
    return 0.0


def parse_segments(text: str, value_type: str = "auto", sample: Optional[str] = None
                   ) -> Tuple[List[Segment], str, List[str], str]:
    """Read a copy-number segment file (TSV, CSV or whitespace separated).

    Needs chromosome, start, end and one value column (copy number or log2 ratio).
    Returns (segments, value type 'cn' or 'log2', notes, sample name).
    """
    value_type = pick(value_type, ["auto", "cn", "log2"], "value type")
    rows = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not rows:
        raise ValueError("The copy-number file is empty.")
    delim = "\t" if "\t" in rows[0] else ("," if "," in rows[0] else None)

    def split(line: str) -> List[str]:
        return [c.strip().strip('"') for c in (line.split(delim) if delim else line.split())]

    first = split(rows[0])
    notes: List[str] = []
    i_sample: Optional[int] = None
    if not any(_num(c) is not None for c in first):          # header row present
        names = [c.lower() for c in first]

        def find(options):
            return next((names.index(o) for o in options if o in names), None)

        i_chr, i_start, i_end = find(_CHROM_NAMES), find(_START_NAMES), find(_END_NAMES)
        if None in (i_chr, i_start, i_end):
            raise ValueError("Could not find chromosome, start and end columns. Header found: " + ", ".join(first))
        i_sample, i_cn, i_log = find(_SAMPLE_NAMES), find(_CN_NAMES), find(_LOG2_NAMES)
        vt = value_type
        if vt == "cn":
            i_val = i_cn
        elif vt == "log2":
            i_val = i_log
        else:
            vt, i_val = ("cn", i_cn) if i_cn is not None else ("log2", i_log)
        if i_val is None:
            raise ValueError("Could not find a %s column. Header found: %s"
                             % ("copy-number" if vt == "cn" else "log2 ratio" if vt == "log2" else "copy-number or log2 ratio",
                                ", ".join(first)))
        body = rows[1:]
    else:                                                     # no header: guess from the column count
        vt = value_type
        if len(first) == 4:
            i_chr, i_start, i_end, i_val = 0, 1, 2, 3
        elif len(first) == 6:                                 # DNAcopy: ID, chrom, start, end, n.marks, seg.mean
            i_sample, i_chr, i_start, i_end, i_val = 0, 1, 2, 3, 5
        else:
            raise ValueError("No header row and %d columns. Add a header (chrom, start, end, log2 or copy_number) "
                             "or use 4 columns: chrom, start, end, value." % len(first))
        body = rows

    parsed, skipped = [], 0
    for line in body:
        c = split(line)
        try:
            parsed.append((c[i_sample] if i_sample is not None else "", c[i_chr],
                           int(float(c[i_start])), int(float(c[i_end])), float(c[i_val])))
        except (ValueError, IndexError):
            skipped += 1
    if not parsed:
        raise ValueError("No usable rows were found. Check the delimiter and the column order.")
    if skipped:
        notes.append("%d row(s) could not be read and were skipped." % skipped)

    chosen = ""
    if i_sample is not None:
        names_in_file = list(dict.fromkeys(p[0] for p in parsed))
        if len(names_in_file) > 1 and not sample:
            shown = ", ".join(names_in_file[:5]) + (" ..." if len(names_in_file) > 5 else "")
            raise ValueError("The file holds %d samples (%s). Choose one with --sample." % (len(names_in_file), shown))
        chosen = sample or names_in_file[0]
        if chosen not in names_in_file:
            raise ValueError("Sample %r is not in the file." % chosen)
        parsed = [p for p in parsed if p[0] == chosen]
    if vt == "auto":
        vt = "log2" if any(p[4] < 0 for p in parsed) else "cn"
        notes.append("The value column was not named, so it was read as %s." % ("log2 ratios" if vt == "log2" else "copy numbers"))

    segments = []
    for _sample, chrom, start, end, value in parsed:
        ch = norm_chrom(chrom)
        if ch is not None and end != start:
            segments.append(Segment(ch, min(start, end), max(start, end), value))
    return segments, vt, notes, chosen
