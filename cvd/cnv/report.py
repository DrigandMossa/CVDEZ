"""Text and TSV reports for the aneuploidy analysis, plus the synthetic example file."""

import os
import re
from typing import List

from ..model import AneuploidyResult, Recommendation
from ..parts.genome import ACROCENTRIC_P, AUTOSOMES, BUILDS, EXAMPLE_ARM_VALUES, N_SCORED_ARMS
from ..parts.strategies import STRATEGIES
from .analysis import aneuploidy_level


def aneuploidy_report(res: AneuploidyResult, recs: List[Recommendation]) -> str:
    def arms_with(call: str) -> str:
        return ", ".join(a.arm for a in res.arms if a.call == call) or "none"

    title = "Aneuploidy analysis" + (": " + res.sample if res.sample else "")
    lines = [title, "=" * len(title),
             "Genome build %s. Input: %s; %s." % (res.build, "copy number" if res.value_type == "cn" else "log2 ratios",
                                                 res.baseline_desc),
             "",
             "Aneuploidy score: %d of %d scorable arms (%d gains, %d losses). Level: %s (orientation only)."
             % (res.score, N_SCORED_ARMS, res.gains, res.losses, aneuploidy_level(res.score)),
             "Fraction of the genome gained or lost: %.0f%%." % res.fga,
             "Gained arms: " + arms_with("gain"),
             "Lost arms: " + arms_with("loss")]
    if res.whole_chromosomes:
        lines.append("Whole-chromosome events: " + ", ".join(res.whole_chromosomes))
    lines.append("Partly altered, not called (20 to 80% of the arm): " + arms_with("partial"))
    lines.append("Not enough data (under 50% of the arm covered): " + arms_with("no data"))
    if res.wgd_suspected:
        lines.append("The baseline copy number is 3 or more, which suggests whole-genome doubling.")
    lines += ["Note: " + n for n in res.notes]
    if res.findings:
        lines += ["", "Immune-relevant findings"] + ["  - %s. %s" % f for f in res.findings]
    lines += ["", "Recommended designs (use --design-from-cnv N, or the button in the window)"]
    for i, r in enumerate(recs, 1):
        lines += ["  %d. %s: %s [%s]" % (i, r.title, r.gene, STRATEGIES[r.strategy]["name"]), "     " + r.reason]
    lines += ["", "Limits",
              "  - Arm-level calls from segments are a screen. Confirm with purity- and ploidy-corrected, allele-specific data.",
              "  - The vector cannot sense aneuploidy. Selectivity comes from delivery and the promoter.",
              "  - Aneuploid cells can occur in some normal tissues. Test expression and killing in normal cells.",
              "  - Suggestions follow known gene locations and published associations. They do not predict response."]
    return "\n".join(lines) + "\n"


def arms_tsv(res: AneuploidyResult) -> str:
    rows = ["arm\tcoverage\tmean_log2_ratio\tfraction_gain\tfraction_loss\tcall"]
    rows += ["%s\t%.3f\t%.3f\t%.3f\t%.3f\t%s" % (a.arm, a.coverage, a.mean_lr, a.frac_gain, a.frac_loss, a.call)
             for a in res.arms]
    return "\n".join(rows) + "\n"


def write_aneuploidy_files(res: AneuploidyResult, recs: List[Recommendation], outdir: str, stem: str) -> List[str]:
    os.makedirs(outdir, exist_ok=True)
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_") or "sample"
    paths = []
    for suffix, text in (("_aneuploidy.txt", aneuploidy_report(res, recs)), ("_arms.tsv", arms_tsv(res))):
        path = os.path.join(outdir, stem + suffix)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        paths.append(path)
    return paths


def example_cnv_text(build: str = "hg38") -> str:
    """A synthetic segment file for trying the analysis. It is not patient data."""
    lines = ["# Synthetic example for testing only. This is not patient data.", "chrom\tstart\tend\tlog2"]
    for chrom in AUTOSOMES:
        length, cen = BUILDS[build][chrom]
        for side, lo, hi in (("p", 1, cen), ("q", cen, length)):
            arm = chrom + side
            if arm in ACROCENTRIC_P:
                continue
            if arm == "4q":                       # only 60% of the arm is altered, so it stays uncalled
                cut = cen + int(0.6 * (length - cen))
                lines += ["%s\t%d\t%d\t-0.50" % (chrom, lo, cut), "%s\t%d\t%d\t0.02" % (chrom, cut, hi)]
            else:
                lines.append("%s\t%d\t%d\t%.2f" % (chrom, lo, hi, EXAMPLE_ARM_VALUES.get(arm, 0.02)))
    return "\n".join(lines) + "\n"
