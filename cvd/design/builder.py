"""Assemble a Design from a Config: element layout, overrides and design checks."""

import re
from typing import List, Tuple

from ..model import Config, Design, Feature
from ..parts.elements import (BUILT_IN_IDS, COSTIM, HINGES, LINKS, MARKERS, P2A_SEQ, POLYA,
                              PROMOTERS, RESISTANCE, SGRNA_SCAFFOLD, SHRNA_LOOP, TAGS,
                              TUMOR_SELECTIVE, VECTORS, WPRE_SHORT_LEN)
from ..parts.genes import GENES
from ..parts.strategies import STRATEGIES
from ..seqops import clean_sequence, gc_percent, pick, revcomp
from .checks import check_insert


def build_design(cfg: Config) -> Design:
    vector = pick(cfg.vector, VECTORS, "vector")
    strat_key = pick(cfg.strategy, STRATEGIES, "strategy")
    S = STRATEGIES[strat_key]
    is_guide, is_car = strat_key == "guide", strat_key == "car"

    prom = pick(cfg.promoter or S["promoter"], PROMOTERS, "promoter")
    marker = pick(cfg.marker or S["marker"], MARKERS, "marker")
    link = "separate PGK promoter" if is_guide else pick(cfg.link, LINKS, "link")
    tag = "none" if (is_guide or is_car) else pick(cfg.tag, TAGS, "tag")
    polya = pick(cfg.polya or ("bGH" if vector == "plasmid" else "SV40"), POLYA, "polyadenylation signal")
    res = pick(cfg.resistance, RESISTANCE, "bacterial selection")
    wpre = cfg.wpre if cfg.wpre is not None else vector != "plasmid"
    hinge = pick(cfg.hinge, HINGES, "hinge")
    costim = pick(cfg.costim, COSTIM, "costimulatory domain")
    sgrna = pick(cfg.guide_type, ["shRNA", "sgRNA"], "guide type") == "sgRNA"

    gene_in = (cfg.gene or "").strip()
    lib_name = next((g for g in GENES if g.lower() == gene_in.lower()
                     or g.lower().startswith(gene_in.lower() + " (")), None)
    gene_info = GENES[lib_name] if lib_name and lib_name != "Custom" else GENES["Custom"]
    gene = lib_name if lib_name and lib_name != "Custom" else (gene_in or ("Target" if is_guide else "Transgene"))
    if cfg.variant and not is_guide:
        gene += " " + cfg.variant.strip()

    insert, bad = (("", 0) if is_guide else clean_sequence(cfg.sequence))
    target = clean_sequence(cfg.target)[0].replace("N", "") if is_guide else ""
    msgs: List[Tuple[str, str]] = []

    feats: List[Feature] = []
    cassette = False

    def add(fid, name, kind, length, seq=None):
        feats.append(Feature(fid, name, kind, length, seq, cassette))

    if vector == "lenti":
        add("ltr5", "5' LTR", "ltr", 634)
        add("psi", "Psi packaging signal", "pack", 124)
        add("rre", "RRE", "pack", 234)
        add("cppt", "cPPT/CTS", "pack", 118)
    if vector == "aav":
        add("itr5", "5' ITR", "itr", 145)
    cassette = True

    p2a = marker != "none" and link == "P2A" and not is_guide
    if is_guide:
        add("u6", "U6 promoter", "promoter", 241)
    else:
        add("prom", prom + " promoter", "promoter", PROMOTERS[prom])
        if cfg.kozak:
            add("kozak", "Kozak", "reg", 6, "GCCACC")

    if is_guide:
        n = target or "N" * (20 if sgrna else 21)
        hairpin = n + SGRNA_SCAFFOLD if sgrna else n + SHRNA_LOOP + revcomp(n)
        add("guide", gene + (" sgRNA" if sgrna else " shRNA"), "guide", len(hairpin), hairpin)
        add("term", "Pol III terminator", "polya", 6, "TTTTTT")
    elif is_car:
        add("lead", "CD8a signal peptide", "tag", 63)
        add("goi", "anti-%s scFv" % gene, "cds", len(insert) or gene_info[0], insert or None)
        add("hinge", hinge, "tag", HINGES[hinge])
        if costim != "none":
            add("costim", costim + " costimulatory domain", "tag", COSTIM[costim])
        add("cd3z", "CD3zeta signaling domain", "tag", 336)
    else:
        add("goi", gene, "cds", len(insert) or gene_info[0], insert or None)

    if tag != "none":
        add("tag", tag + " tag", "tag", len(TAGS[tag]), TAGS[tag])
    if not p2a and not is_guide:
        add("stop", "Stop (TAA)", "stop", 3, "TAA")
    if marker != "none" and not is_guide:
        if link == "P2A":
            add("p2a", "P2A", "link", 66, P2A_SEQ)
        if link == "IRES":
            add("ires", "IRES (EMCV)", "link", 580)
        add("mark", marker, "marker", MARKERS[marker])
        if p2a:
            add("stop", "Stop (TAA)", "stop", 3, "TAA")
    if wpre and not is_guide:
        if cfg.wpre_short:
            add("wpre", "WPRE3 (short)", "reg", WPRE_SHORT_LEN)
        else:
            add("wpre", "WPRE", "reg", 589)
    if polya != "none" and not is_guide:
        add("pa", polya + " polyA", "polya", POLYA[polya])
    if marker != "none" and link.startswith("separate"):
        add("pgk", "PGK promoter", "promoter", 516)
        add("mark2", marker + " (PGK)", "marker", MARKERS[marker])
    cassette = False
    if vector == "lenti":
        add("ltr3", "3' dU3 LTR", "ltr", 234)
    if vector == "aav":
        add("itr3", "3' ITR", "itr", 145)
    if vector != "plasmid":
        add("f1", "f1 ori", "ori", 429)
    add("res", res, "bact", RESISTANCE[res])
    add("ori", "pUC ori", "ori", 589)

    # user overrides (verified sequences for placeholder elements)
    ids = {f.id for f in feats}
    for fid, raw in cfg.overrides.items():
        if fid in BUILT_IN_IDS:
            raise ValueError("Element %r takes its sequence from --seq, --target or the built-in library; "
                             "it cannot be overridden." % fid)
        if fid not in ids:
            raise ValueError("No element with id %r in this design. Ids in this design: %s"
                             % (fid, ", ".join(sorted(ids - BUILT_IN_IDS))))
        s, _ = clean_sequence(raw)
        if not s:
            raise ValueError("Override for %r contains no A, C, G, T or N." % fid)
        f = next(f for f in feats if f.id == fid)
        f.seq, f.length, f.custom = s, len(s), True

    pos, parts = 1, []
    for f in feats:
        if not f.seq:
            f.seq = "N" * f.length
        f.start, f.end = pos, pos + f.length - 1
        pos += f.length
        parts.append(f.seq)
    seq = "".join(parts)

    # ---- design checks -------------------------------------------------
    if not is_guide and not insert:
        msgs.append(("warn", "No sequence supplied, so a %s bp placeholder (typical length) is used for %s."
                     % (format(gene_info[0], ","), gene)))
    if bad:
        msgs.append(("warn", "%d non-nucleotide character(s) were removed from the insert sequence." % bad))
    if not is_guide and insert:
        check_insert(msgs, insert, "scFv" if is_car else "Insert", vector, check_atg=not is_car)
    if not is_guide and not is_car and gene_info[1]:
        msgs.append(("info", gene_info[1]))
    if is_guide:
        if not target:
            msgs.append(("warn", "No target sequence supplied, so an N-filled placeholder is used."))
        else:
            if sgrna and len(target) != 20:
                msgs.append(("warn", "sgRNA protospacers are usually 20 nt (yours: %d)." % len(target)))
            if not sgrna and not 19 <= len(target) <= 25:
                msgs.append(("warn", "shRNA sense strands are usually 19 to 25 nt (yours: %d)." % len(target)))
            if "TTTT" in target:
                msgs.append(("error", "The target contains TTTT, which ends Pol III transcription early. Choose another site."))
            if not sgrna and not 30 <= gc_percent(target) <= 60:
                msgs.append(("warn", "Target GC content is %d%%. Most shRNA designs aim for 30 to 55%%." % gc_percent(target)))
            if target[0] != "G":
                msgs.append(("info", "U6 transcribes best from a 5' G. Consider adding one to the 5' end."))
        if sgrna:
            msgs.append(("info", "This vector carries the sgRNA only. Pair it with Cas9 (SaCas9 fits AAV)."))
    if strat_key == "model":
        msgs.append(("info", "Research use only: oncogene expression for transformation assays and animal models. "
                             "This is not a therapeutic design."))
    if is_car:
        msgs.append(("info", "CAR domains use typical lengths and are written as N until you supply verified sequences. "
                             "Keep the scFv, hinge, costimulatory and CD3zeta domains in frame."))
    if strat_key == "flag":
        msgs.append(("info", "This vector cannot sense aneuploidy. Selectivity comes from delivery and the "
                             "tumor-selective promoter, not from the payload."))
        msgs.append(("warn", "Aneuploid cells can also occur in some normal tissues. Test expression and immune killing "
                             "in normal cells before trusting the selectivity."))
    if p2a:
        msgs.append(("info", "P2A selected: keep the insert (and tag) in frame with P2A and the reporter."))
    if prom in TUMOR_SELECTIVE and not is_guide:
        msgs.append(("info", "%s is a tumor-selective promoter. Expression is limited to cells where it is active "
                             "and is usually weaker than EF1a or CMV, so confirm activity in your cell model." % prom))
    if vector != "plasmid":
        cas = sum(f.length for f in feats if f.in_cassette)
        n = format(cas, ",")
        if vector == "aav":
            if cas > 4700:
                msgs.append(("error", "Cassette between the ITRs is %s bp, above the roughly 4.7 kb AAV packaging limit." % n))
            elif cas > 4400:
                msgs.append(("warn", "Cassette between the ITRs is %s bp, close to the roughly 4.7 kb AAV limit." % n))
            else:
                msgs.append(("info", "Cassette between the ITRs: %s bp (limit about 4.7 kb)." % n))
        else:
            if cas > 8000:
                msgs.append(("warn", "Insert region between the LTRs is %s bp. Large inserts lower lentiviral titer." % n))
            else:
                msgs.append(("info", "Insert region between the LTRs: %s bp." % n))
        if vector == "lenti":
            msgs.append(("info", "Lentiviral vectors integrate. This design uses a self-inactivating (dU3) 3' LTR."))

    msgs.sort(key=lambda m: ("error", "warn", "info").index(m[0]))

    prefix = {"lenti": "pLV", "aav": "pAAV", "plasmid": "pEx"}[vector]
    tagpart = "-" + tag if tag != "none" else ""
    markpart = ""
    if marker != "none":
        markpart = "-%s-%s" % ({"P2A": "P2A", "IRES": "IRES"}.get(link, "PGK"), marker)
    lead = ("sg" if sgrna else "sh") if is_guide else ("CAR-" if is_car else "")
    short = re.sub(r"\s+", "_", re.sub(r"\s*\([^)]*\)", "", gene).strip())
    auto = "%s-%s>%s%s%s%s" % (prefix, "U6" if is_guide else prom, lead, short, tagpart, markpart)
    return Design(cfg.name.strip() or auto, vector, strat_key, feats, seq, msgs, cfg.basis)
