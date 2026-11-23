"""Scoring rules: insert profile, capacity, expression and insert-vs-genome points."""

import re
from typing import List, Optional, Tuple

from ..model import Config
from ..parts.elements import PROMOTERS
from ..parts.genes import GENES
from ..parts.strategies import STRATEGIES
from ..seqops import clean_sequence, pick
from .model import InsertProfile
from .tables import (
    ARRANGEMENTS, CAPACITY, LENTI_HARD_LIMIT, PROMOTER_TRAITS, STRATEGY_NEEDS, STRENGTH_WORD,
    VECTOR_LABEL)


def fmt_int(n: int) -> str:
    return format(n, ",")


def parse_setting(text: str) -> str:
    t = (text or "").strip().lower().replace("-", " ")
    if t in ("", "not specified", "unspecified", "auto"):
        return ""
    if t in ("in vivo", "ex vivo"):
        return t
    raise ValueError("Unknown delivery setting %r. Choose from: not specified, in vivo, ex vivo." % text)


def profile_insert(cfg: Config) -> InsertProfile:
    """Describe the insert: size, composition and the motifs that matter for packaging."""
    strat = pick(cfg.strategy, STRATEGIES, "strategy")
    is_guide, is_car = strat == "guide", strat == "car"
    seq = clean_sequence(cfg.target if is_guide else cfg.sequence)[0]
    if is_guide:
        seq = seq.replace("N", "")
    gene_in = (cfg.gene or "").strip()
    lib = next((g for g in GENES if g.lower() == gene_in.lower()
                or g.lower().startswith(gene_in.lower() + " (")), None)
    named = lib if lib and lib != "Custom" else None
    typical = GENES[named][0] if named else GENES["Custom"][0]
    kind = "guide target" if is_guide else ("scFv" if is_car else "coding sequence")
    name = named or gene_in or "the insert"
    sgrna = (cfg.guide_type or "").lower() == "sgrna"
    if seq:
        length, source, known = len(seq), "pasted sequence", True
    elif is_guide:
        length, source, known = (20 if sgrna else 21), "placeholder target", False
    else:
        length, source, known = typical, "typical length of %s" % (named or "a custom insert"), False

    gc = None
    polya: List[int] = []
    donors: List[int] = []
    stops = first = 0
    issues: List[Tuple[str, str]] = []
    if not known:
        issues.append(("info", "No sequence was pasted, so the length is %s bp (%s) and the sequence checks were "
                               "skipped. Paste your sequence for a sequence-specific ranking." % (fmt_int(length), source)))
    elif is_guide:
        if "TTTT" in seq:
            issues.append(("error", "The target contains TTTT, which ends Pol III transcription early."))
        lo, hi = (20, 20) if sgrna else (19, 25)
        if not lo <= len(seq) <= hi:
            issues.append(("warn", "%s are usually %s nt (yours: %d)." % (
                "sgRNA protospacers" if sgrna else "shRNA sense strands", "20" if sgrna else "19 to 25", len(seq))))
    else:
        gc = round(100 * sum(c in "GC" for c in seq) / len(seq))
        polya = [m.start() + 1 for m in re.finditer("(?=AATAAA|ATTAAA)", seq)]
        donors = [m.start() + 1 for m in re.finditer("(?=[AC]AGGT[AG]AGT)", seq)]
        in_frame = len(seq) % 3 == 0
        if in_frame:
            for i in range(0, len(seq) - 3, 3):
                if seq[i:i + 3] in ("TAA", "TAG", "TGA"):
                    stops += 1
                    first = first or i // 3 + 1
        else:
            issues.append(("warn", "The length (%s bp) is not a multiple of 3." % fmt_int(len(seq))))
        if stops:
            issues.append(("error", "%d in-frame stop codon(s) inside the sequence; the first is at codon %d."
                           % (stops, first)))
        if not is_car and not seq.startswith("ATG"):
            issues.append(("warn", "The sequence does not start with ATG."))
        if in_frame and seq[-3:] in ("TAA", "TAG", "TGA"):
            issues.append(("warn", "The sequence ends in a stop codon; remove it if you use a tag or a P2A reporter."))
        if len(seq) < 150:
            issues.append(("warn", "Only %d bp: short for a coding sequence. If this is an shRNA target or sgRNA "
                                   "protospacer, choose the guide strategy." % len(seq)))
        if gc > 65 or gc < 35:
            issues.append(("info", "GC content is %d%%, outside 35 to 65%%: harder to synthesize and clone, and may "
                                   "lower vector yield." % gc))
    return InsertProfile(kind, name, length, source, known, gc, polya, donors, stops, first, issues)


def capacity_points(vector: str, cassette: int) -> Tuple[int, bool, str, str]:
    limit, limit_text = CAPACITY[vector]
    util = cassette / limit
    if util <= 0.75:
        pts = 30.0
    elif util <= 0.93:
        pts = 30 - (util - 0.75) / 0.18 * 15
    elif util <= 1.0:
        pts = 15 - (util - 0.93) / 0.07 * 10
    elif vector == "lenti" and util <= LENTI_HARD_LIMIT:
        pts = 5 - (util - 1.0) / (LENTI_HARD_LIMIT - 1.0) * 5
    else:
        pts = 0.0
    feasible = util <= 1.0 or (vector == "lenti" and util <= LENTI_HARD_LIMIT)
    room = limit - cassette
    short = "%s/%s bp" % (fmt_int(cassette), fmt_int(limit))
    if util <= 1.0:
        reason = "The cassette is %s bp of %s bp (%d%%; %s), leaving %s bp spare." % (
            fmt_int(cassette), fmt_int(limit), round(100 * util), limit_text, fmt_int(room))
    elif feasible:
        reason = ("The cassette is %s bp, %s bp above the usual %s bp ceiling (%s); expect a much lower titer."
                  % (fmt_int(cassette), fmt_int(-room), fmt_int(limit), limit_text))
    else:
        reason = "The cassette is %s bp, %s bp over the %s bp limit (%s), so it will not package." % (
            fmt_int(cassette), fmt_int(-room), fmt_int(limit), limit_text)
    return int(round(pts)), feasible, reason, short


def expression_points(strategy: str, promoter: Optional[str]) -> Tuple[int, str, str]:
    if strategy == "guide" or promoter is None:
        return 20, "U6 drives the hairpin in every layout, so the promoter choice does not change this score.", "U6 hairpin"
    need_sel, need_str, need_t, why = STRATEGY_NEEDS[strategy]
    t = PROMOTER_TRAITS[promoter]
    sel = 1.0 if need_sel == 0 or t["selective"] else (0.6 if need_sel == 1 else 0.2)
    stren = 1.0 if t["strength"] >= need_str else max(0.2, 1 - 0.3 * (need_str - t["strength"]))
    f = 0.5 * sel + 0.5 * stren
    flaws = []
    if sel < 1.0:
        flaws.append("it is not tumor-selective, which this strategy %s" % ("needs" if need_sel == 2 else "benefits from"))
    if stren < 1.0:
        flaws.append("it is weaker than the strategy needs")
    if need_t and not t["tcell"]:
        f *= 0.4
        flaws.append("it is not designed for expression in T cells")
    desc = "%s is a %s promoter%s." % (promoter, STRENGTH_WORD[t["strength"]],
                                      ", selective for tumor cells" if t["selective"] else ", not tumor-selective")
    tail = " Held back because %s." % " and ".join(flaws) if flaws else " It meets these needs."
    return int(round(20 * f)), "%s %s%s" % (desc, why, tail), "%s %s" % (promoter, STRENGTH_WORD[t["strength"]])


def insert_points(vector: str, p: InsertProfile) -> Tuple[int, str, str]:
    if not p.known:
        return 15, "No sequence was pasted, so motifs were not checked (every option gets the same points).", "not checked"
    if p.kind == "guide target":
        return 15, "A short guide target has no internal polyadenylation or splice signals to check.", "short target"
    pts, notes, flags = 15, [], []
    if p.polya:
        where = ", ".join(str(x) for x in p.polya[:3]) + (" ..." if len(p.polya) > 3 else "")
        if vector == "lenti":
            pts -= 8
            notes.append("%d polyadenylation signal(s) (AATAAA or ATTAAA) at position %s; in a lentiviral genome they "
                         "can cut the vector RNA short and lower titer (-8)." % (len(p.polya), where))
        else:
            pts -= 3
            notes.append("%d polyadenylation signal(s) (AATAAA or ATTAAA) at position %s; they can end the transgene "
                         "mRNA early, a smaller risk because the AAV genome is DNA (-3)." % (len(p.polya), where))
        flags.append("polyA signal")
    if p.donors and vector == "lenti":
        pts -= 4
        where = ", ".join(str(x) for x in p.donors[:3]) + (" ..." if len(p.donors) > 3 else "")
        notes.append("%d splice-donor-like motif(s) (MAGGTRAGT) at position %s; the lentiviral genome RNA can be "
                     "spliced inside the insert (-4)." % (len(p.donors), where))
        flags.append("splice donor")
    if not notes:
        return 15, "No internal polyadenylation signal or strong splice-donor motif was found.", "no flags"
    return pts, " ".join(notes), " + ".join(flags)


def arrangement_rationale(strategy: str, arr: str, vector: str, cassette: int, reference: int) -> str:
    limit = CAPACITY[vector][0]
    spec = ARRANGEMENTS[arr]
    if arr == "strong":
        return ("Reference layout: the EF1a promoter, strong in most cell types, with WPRE to raise expression. "
                "The other layouts are variations on it.")
    if arr == "compact":
        saved = reference - cassette
        text = ("Generated to save room: the EFS promoter is %s bp shorter than EF1a and WPRE is left out, which "
                "saves %s bp compared with the strong layout (%s bp)." % (
                    fmt_int(PROMOTERS["EF1a"] - PROMOTERS["EFS"]), fmt_int(saved), fmt_int(reference)))
        if reference / limit > 1.0:
            text += " This matters here because the strong layout does not fit: it is %d%% of the %s capacity." % (
                round(100 * reference / limit), VECTOR_LABEL[vector])
        elif reference / limit > 0.75:
            text += " This matters here because the strong layout already uses %d%% of the %s capacity." % (
                round(100 * reference / limit), VECTOR_LABEL[vector])
        else:
            text += " The insert is small enough that capacity is not the constraint, so this layout mainly trades " \
                    "some expression strength for space."
        return text
    if arr == "selective":
        if STRATEGY_NEEDS[strategy][0] > 0:
            return "Generated because this strategy rewards tumor-restricted expression. " + STRATEGY_NEEDS[strategy][3]
        return "Included as a tumor-restricted alternative, although this strategy does not require it."
    if arr == "tcell":
        return ("Generated because CAR constructs are expressed in T cells, and MND is built for strong expression "
                "in T cells and other blood cells.")
    return "The only layout for a U6 hairpin, so the options differ by vector, not by promoter."
