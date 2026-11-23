"""Arm-level gain/loss calling and the aneuploidy score."""

import math
from typing import Dict, List, Optional

from ..model import AneuploidyResult, ArmResult, Segment
from ..parts.genome import (ACROCENTRIC_P, ARM_ORDER, AUTOSOMES, BUILDS, IMMUNE_ARM_NOTES,
                            N_SCORED_ARMS)
from ..seqops import pick
from .segments import weighted_median


def aneuploidy_level(score: int) -> str:
    """Rough orientation bins only; compare with the distribution for your tumor type."""
    return "low" if score <= 2 else ("intermediate" if score <= 9 else "high")


def analyze_aneuploidy(segments: List[Segment], build: str = "hg38", value_type: str = "log2",
                       ploidy: Optional[float] = None, center: bool = True, gain: float = 0.2,
                       loss: float = -0.2, sample: str = "", notes: Optional[List[str]] = None) -> AneuploidyResult:
    """Call arm-level gains and losses and compute an aneuploidy score.

    An arm is called gained or lost when at least 80% of its covered length changes in one
    direction, and neutral when at most 20% does (the rule used by Taylor et al., Cancer Cell 2018).
    The score is the number of gained or lost arms among the 39 scorable autosomal arms.
    """
    build = pick(build, BUILDS, "genome build")
    value_type = pick(value_type, ["cn", "log2"], "value type")
    if not (gain > 0 > loss):
        raise ValueError("The gain threshold must be above 0 and the loss threshold below 0.")
    dims = BUILDS[build]
    notes = list(notes or [])
    by_chrom: Dict[str, List[Segment]] = {}
    for s in segments:
        if s.chrom in dims:
            a, b = max(0, s.start), min(dims[s.chrom][0], s.end)
            if b > a:
                by_chrom.setdefault(s.chrom, []).append(Segment(s.chrom, a, b, s.value))
    clipped = [s for segs in by_chrom.values() for s in segs]
    if not clipped:
        raise ValueError("No autosomal segments overlap the %s chromosomes. Check the genome build and chromosome names." % build)

    weights = [(s.value, s.end - s.start) for s in clipped]
    if value_type == "cn":
        base = (float(ploidy) if ploidy is not None
                else float(max(1, round(weighted_median(weights)))))
        if base <= 0:
            raise ValueError("Ploidy must be above 0.")
        desc = "baseline copy number %g (%s)" % (base, "given" if ploidy else "genome-wide median")

        def to_lr(v: float) -> float:
            return math.log2(max(v, 0.1) / base)
    else:
        centre = weighted_median(weights) if center else 0.0
        desc = "log2 ratios centred on %+.3f" % centre if center else "log2 ratios, not centred"

        def to_lr(v: float) -> float:
            return v - centre
        base = 2.0
        notes.append("Log2 ratios cannot show absolute ploidy, so whole-genome doubling cannot be called."
                     + (" The --ploidy value is only used with copy-number input." if ploidy else ""))

    arms: List[ArmResult] = []
    for arm in ARM_ORDER:
        chrom, side = arm[:-1], arm[-1]
        length, cen = dims[chrom]
        lo, hi = (0, cen) if side == "p" else (cen, length)
        cov = g = l = 0
        weighted = 0.0
        for s in by_chrom.get(chrom, []):
            ov = min(s.end, hi) - max(s.start, lo)
            if ov <= 0:
                continue
            r = to_lr(s.value)
            cov += ov
            weighted += r * ov
            if r >= gain:
                g += ov
            elif r <= loss:
                l += ov
        cov_eff = min(cov, hi - lo)
        fg, fl = (min(g / cov, 1.0), min(l / cov, 1.0)) if cov else (0.0, 0.0)
        coverage = cov_eff / (hi - lo)
        if arm in ACROCENTRIC_P:
            call = "not scored"
        elif coverage < 0.5:
            call = "no data"
        elif fg >= 0.8:
            call = "gain"
        elif fl >= 0.8:
            call = "loss"
        elif max(fg, fl) <= 0.2:
            call = "neutral"
        else:
            call = "partial"
        arms.append(ArmResult(arm, coverage, weighted / cov if cov else 0.0, fg, fl, call))

    by_arm = {a.arm: a for a in arms}
    whole = []
    for chrom in AUTOSOMES:
        if chrom + "p" in ACROCENTRIC_P:      # the p arm cannot be assessed, so the q-arm call stands alone
            continue
        sides = [by_arm[chrom + s].call for s in "pq"]
        for direction in ("gain", "loss"):
            if all(c == direction for c in sides):
                whole.append("%s %s" % (chrom, direction))
    gains = sum(a.call == "gain" for a in arms)
    losses = sum(a.call == "loss" for a in arms)
    covered = sum(s.end - s.start for s in clipped)
    altered = sum(s.end - s.start for s in clipped if to_lr(s.value) >= gain or to_lr(s.value) <= loss)
    calls = {a.arm: a.call for a in arms}
    findings = [("%s %s: %s" % (arm, direction, label), note)
                for arm, direction, label, note in IMMUNE_ARM_NOTES if calls.get(arm) == direction]
    with_data = sum(a.call not in ("no data", "not scored") for a in arms)
    if with_data < 20:
        notes.append("Only %d of the %d scorable arms had enough data, so the score is a lower bound."
                     % (with_data, N_SCORED_ARMS))
    if gains + losses < 3:
        notes.append("Few arm-level events were found. Check the baseline or ploidy before relying on the "
                     "aneuploidy-directed choices below.")
    return AneuploidyResult(sample, build, value_type, desc, arms, whole, gains, losses,
                            100.0 * altered / covered, value_type == "cn" and base >= 3, findings, notes)
