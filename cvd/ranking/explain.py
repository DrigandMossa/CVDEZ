"""Text for the ranking: tables, explanations, the modifications report and option-to-config helpers."""

import dataclasses
import os
import re
from typing import List, Tuple

from ..model import Config
from .model import RankingResult, VectorOption
from .scoring import fmt_int
from .tables import HOW_SCORES_WORK, VECTOR_LABEL, VECTOR_NOTES


def fit_text(o: VectorOption) -> str:
    util = round(100 * o.cassette / o.limit)
    if o.cassette <= o.limit:
        return "fits (%d%%)" % util
    return ("over ceiling (%d%%)" if o.feasible else "too large (%d%%)") % util


def ranking_summary(res: RankingResult) -> str:
    p = res.profile
    first = "Insert: %s, %s bp (%s)" % (p.kind, fmt_int(p.length), p.source)
    if p.gc is not None:
        first += ", %d%% GC" % p.gc
    lines = [first + ".", "Delivery setting: %s (%s)." % (res.setting, res.setting_note)]
    names = {"error": "Error", "warn": "Warning", "info": "Note"}
    for level, text in sorted(p.issues, key=lambda i: ("error", "warn", "info").index(i[0])):
        lines.append("%s: %s" % (names[level], text))
    if any(level in ("error", "warn") for level, _ in p.issues):
        lines.append("The issues above affect every option, so they do not change the ranking.")
    if not any(o.feasible for o in res.options):
        lines.append("No option fits its vector's capacity; the list shows the closest fits. Consider splitting the "
                     "cargo or a vector with more room (not modeled here, for example helper-dependent adenovirus or "
                     "dual AAV).")
    return "\n".join(lines)


def options_table(res: RankingResult) -> str:
    rows = ["%-4s %-6s %-11s %-46s %-9s %s" % ("Rank", "Score", "Vector", "Layout", "Cassette", "Capacity")]
    for o in res.options:
        rows.append("%-4d %-6d %-11s %-46s %-9s %s" % (o.rank, o.applicability, VECTOR_LABEL[o.vector], o.layout,
                                                      fmt_int(o.cassette), fit_text(o)))
    return "\n".join(rows)


def compare_line(a: VectorOption, b: VectorOption) -> Tuple[str, str]:
    """(tag, text) saying why option a ranks above or below option b, from the actual score differences."""
    above = a.rank < b.rank
    head = "%s #%d, %s (%d):" % ("Above" if above else "Below", b.rank, b.title, b.applicability)
    tag = "good" if above else "bad"
    cap_a, cap_b = a.score("capacity").short, b.score("capacity").short
    if a.feasible != b.feasible:
        who = "it fits while #%d does not" % b.rank if a.feasible else "it does not fit while #%d does" % b.rank
        return tag, "%s options that fit always rank first, and %s (cassette %s vs %s)." % (head, who, cap_a, cap_b)
    if not a.feasible:
        ua, ub = a.cassette / a.limit, b.cassette / b.limit
        if abs(ua - ub) > 1e-9:
            return tag, "%s neither fits; the closer fit ranks first (cassette %d%% of its limit vs %d%%)." % (
                head, round(100 * ua), round(100 * ub))
    else:
        delta = a.total - b.total
        if delta != 0:
            diffs = sorted(((s.points - b.score(s.key).points, s, b.score(s.key)) for s in a.scores
                            if s.points != b.score(s.key).points), key=lambda d: -abs(d[0]))
            bits = ["%s %+d (%s vs %s)" % (s.label.lower(), d, s.short, t.short) for d, s, t in diffs[:3]]
            if len(diffs) > 3:
                bits.append("%d smaller difference%s" % (len(diffs) - 3, "s" if len(diffs) > 4 else ""))
            return tag, "%s score %+d: %s." % (head, delta, "; ".join(bits))
    if a.arrangement != b.arrangement:
        return tag, "%s same score; ties keep the layouts in a fixed order (strong, compact, selective, T-cell)." % head
    return tag, "%s same score and layout; ties go to the smaller cassette, then to the vector name." % head


def modification_parts(res: RankingResult, index: int) -> List[Tuple[str, str]]:
    """Every modification made to one prebuilt option, as (tag, text) parts, for its own tab."""
    o = res.options[index]
    parts: List[Tuple[str, str]] = [("title", "Modifications to option %d: %s" % (o.rank, o.title))]
    if not res.optimized:
        parts.append(("text", "Modifications are switched off, so this is the plain layout: %s bp." % fmt_int(o.cassette)))
        return parts
    done, skipped = o.applied_mods, [m for m in o.mods if not m.applied]
    saved = o.base_cassette - o.cassette
    if done:
        if saved > 0:
            delta = ", %s bp smaller" % fmt_int(saved)
        elif saved < 0:
            delta = ", %s bp larger" % fmt_int(-saved)
        else:
            delta = ", the same size"
        parts.append(("text", "The plain layout is %s bp. After %d modification%s the prebuilt vector is %s bp "
                              "(%d%% of the %s bp limit)%s." % (
            fmt_int(o.base_cassette), len(done), "" if len(done) == 1 else "s", fmt_int(o.cassette),
            round(100 * o.cassette / o.limit), fmt_int(o.limit), delta)))
        if not o.feasible:
            parts.append(("bad", "It still does not fit this vector."))
    else:
        parts.append(("text", "No modification was needed: the plain layout (%s bp) is already the prebuilt vector."
                      % fmt_int(o.cassette)))
    if done:
        parts.append(("head", "Applied (%d)" % len(done)))
        for i, m in enumerate(done, 1):
            parts.append(("good", "%d. %s" % (i, m.title)))
            parts.append(("text", "   Change: %s" % m.change))
            parts.append(("text", "   Why: %s" % m.reason))
            parts.append(("text", "   Cassette size: %s" % ("%+d bp" % m.bp if m.bp else "no change")))
            if m.tradeoff:
                parts.append(("bad", "   Cost: %s" % m.tradeoff))
    if skipped:
        parts.append(("head", "Considered but not applied (%d)" % len(skipped)))
        for m in skipped:
            parts.append(("mute", "- %s: %s" % (m.title, m.reason)))
    parts.append(("mute", "Each change was rebuilt and measured on the design. Switch modifications off (the 'Apply "
                          "suggested modifications' box, or --no-optimize) to compare with the plain layouts."))
    return parts


def _flatten(parts: List[Tuple[str, str]]) -> str:
    out = []
    for tag, text in parts:
        if tag == "title":
            out += [text, "=" * len(text)]
        elif tag == "head":
            out += ["", text.upper()]
        else:
            out.append(text)
    return "\n".join(out) + "\n"


def explain_option_parts(res: RankingResult, index: int) -> List[Tuple[str, str]]:
    """The reasoning for one option as (tag, text) parts. Tags: title, head, text, good, bad, mute."""
    o = res.options[index]
    parts: List[Tuple[str, str]] = [
        ("title", "%d. %s" % (o.rank, o.title)),
        ("text", "Applicability %d of 100. Rank %d of %d. Cassette %s bp (%d%% of the %s bp limit)." % (
            o.applicability, o.rank, len(res.options), fmt_int(o.cassette), round(100 * o.cassette / o.limit),
            fmt_int(o.limit)))]
    if not o.feasible:
        others = sum(s.maximum for s in o.scores if s.key != "capacity")
        parts.append(("bad", "Does not fit this vector's capacity, so its applicability is 0 and it ranks below "
                             "every option that fits. On its other criteria it would score %d of %d."
                      % (o.total - o.score("capacity").points, others)))
    strong = [s for s in o.scores if s.points >= 0.8 * s.maximum]
    weak = [s for s in o.scores if s.points <= 0.5 * s.maximum]
    parts.append(("head", "Why it was suggested"))
    parts.append(("text", o.generated_because))
    for s in strong:
        parts.append(("good", "+ %s (%d/%d): %s" % (s.label, s.points, s.maximum, s.reason)))
    if not strong:
        parts.append(("text", "No criterion scores highly; it is listed for completeness."))
    if weak:
        parts.append(("head", "What holds it back"))
        for s in weak:
            parts.append(("bad", "- %s (%d/%d): %s" % (s.label, s.points, s.maximum, s.reason)))
    parts.append(("head", "Score breakdown"))
    for s in o.scores:
        line = "%s: %d of %d (%s)." % (s.label, s.points, s.maximum, s.short)
        if s not in strong and s not in weak:
            line += " " + s.reason
        parts.append(("text", line))
    parts.append(("head", "Why it ranks above or below the other suggestions"))
    for other in res.options:
        if other is not o:
            parts.append(compare_line(o, other))
    parts.append(("head", "Also worth knowing (not scored)"))
    for note in VECTOR_NOTES[o.vector]:
        parts.append(("mute", "- " + note))
    parts.append(("mute", HOW_SCORES_WORK))
    return parts


def explain_option(res: RankingResult, index: int, with_modifications: bool = True) -> str:
    text = _flatten(explain_option_parts(res, index))
    if with_modifications:
        text += "\n" + _flatten(modification_parts(res, index))
    return text


def options_report(res: RankingResult) -> str:
    title = "Vector options for %s" % res.profile.name
    lines = [title, "=" * len(title), ranking_summary(res), "", options_table(res), "", HOW_SCORES_WORK]
    for i in range(len(res.options)):
        lines += ["", "-" * 72, explain_option(res, i).rstrip()]
    return "\n".join(lines) + "\n"


def write_options_report(res: RankingResult, outdir: str, stem: str) -> str:
    os.makedirs(outdir, exist_ok=True)
    stem = re.sub(r"[^\w.-]+", "_", stem).strip("_") or "vector"
    path = os.path.join(outdir, stem + "_vector_options.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(options_report(res))
    return path


def basis_for_option(res: RankingResult, o: VectorOption) -> str:
    best = [s.label.lower() for s in o.scores if s.points >= 0.8 * s.maximum]
    text = "Vector option #%d of %d (%s), applicability %d/100. Strongest points: %s. Delivery setting: %s." % (
        o.rank, len(res.options), o.title, o.applicability, ", ".join(best) or "none", res.setting)
    done = o.applied_mods
    if done:
        text += " Modifications: " + "; ".join("%s (%s)" % (m.title.lower(), m.change) for m in done) + "."
    return text


def config_for_option(cfg: Config, res: RankingResult, o: VectorOption) -> Config:
    """The user's configuration with the vector, promoter and WPRE of a ranked option."""
    oc = o.config
    c = dataclasses.replace(cfg, vector=o.vector,
                            promoter=oc.promoter or cfg.promoter,
                            wpre=oc.wpre if oc.wpre is not None else cfg.wpre,
                            wpre_short=oc.wpre_short, kozak=oc.kozak, link=oc.link, tag=oc.tag,
                            polya=oc.polya, resistance=oc.resistance, marker=oc.marker)
    c.basis = "\n".join(x for x in (cfg.basis, basis_for_option(res, o)) if x)
    return c


def parse_explain(text: str, n: int) -> List[int]:
    """Zero-based option indexes from --explain N or --explain all."""
    if text.strip().lower() == "all":
        return list(range(n))
    try:
        k = int(text)
    except ValueError:
        raise ValueError("--explain needs an option number or 'all', got %r." % text)
    if not 1 <= k <= n:
        raise ValueError("--explain must be between 1 and %d." % n)
    return [k - 1]
