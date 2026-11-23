"""Modifications that make a prebuilt option as effective as the part library allows."""

import dataclasses
from typing import List, Tuple

from ..design.builder import build_design
from ..model import Config
from ..parts.elements import WPRE_SHORT_LEN
from ..parts.strategies import STRATEGIES
from .model import InsertProfile, Modification
from .scoring import capacity_points
from .tables import CAPACITY, THERAPEUTIC, VECTOR_LABEL, WPRE_NOTE


def cassette_size(cfg: Config) -> int:
    return sum(f.length for f in build_design(cfg).features if f.in_cassette)


def optimize_config(c: Config, strat: str, vector: str, setting: str,
                    profile: InsertProfile) -> Tuple[Config, List[Modification]]:
    """Make a candidate as effective as the part library allows. Every change is rebuilt and measured, and every
    change (and every change considered but not made) is returned as a Modification."""
    mods: List[Modification] = []
    cur, size = c, cassette_size(c)
    limit = CAPACITY[vector][0]
    therapeutic = strat in THERAPEUTIC

    def fits() -> bool:
        return capacity_points(vector, size)[1]

    def apply(new: Config, key: str, title: str, change: str, reason: str, tradeoff: str = "") -> None:
        nonlocal cur, size
        n = cassette_size(new)
        mods.append(Modification(key, title, change, reason, n - size, True, tradeoff))
        cur, size = new, n

    def skip(key: str, title: str, reason: str) -> None:
        mods.append(Modification(key, title, "not changed", reason, 0, False))

    marker = cur.marker or STRATEGIES[strat]["marker"]
    if strat != "guide":
        if not cur.kozak:
            apply(dataclasses.replace(cur, kozak=True), "kozak", "Add a Kozak sequence",
                  "Kozak: off -> on", "A Kozak consensus before the start codon improves translation initiation "
                  "for a few base pairs.")
        if marker != "none" and cur.link != "P2A" and not (therapeutic and setting == "in vivo"):
            note = "IRES" if cur.link == "IRES" else "a second promoter"
            apply(dataclasses.replace(cur, link="P2A"), "link", "Link the marker with P2A",
                  "Marker link: %s -> P2A" % cur.link,
                  "P2A is much shorter than %s and makes the marker in equal amounts from one transcript, which "
                  "leaves more room for the transgene." % note)
    if vector == "aav" and cur.polya == "bGH":
        apply(dataclasses.replace(cur, polya="SV40"), "polya", "Use the SV40 late polyA signal",
              "polyA: bGH -> SV40", "The SV40 late signal is about 100 bp shorter than bGH and gave equal or "
              "higher expression in the same published AAV comparison (Choi et al. 2014).")
    if therapeutic and cur.tag != "none" and strat != "car":
        apply(dataclasses.replace(cur, tag="none"), "tag", "Remove the C-terminal tag",
              "Tag: %s -> none" % cur.tag, "A tag is a foreign sequence that can be recognized by the immune system, "
              "and it takes space. Tags are for detection in research, not for a therapeutic construct.")
    marker = cur.marker or STRATEGIES[strat]["marker"]
    if marker != "none" and strat != "guide":
        remove = (therapeutic and setting == "in vivo") or not fits()
        if remove:
            why = ("A fluorescent or selection marker is a foreign protein that can trigger an immune response in "
                   "a patient, and it takes space." if therapeutic and setting == "in vivo"
                   else "The cassette does not fit with the marker, so it is removed to make room.")
            apply(dataclasses.replace(cur, marker="none"), "marker", "Remove the reporter or selection marker",
                  "Marker: %s -> none" % marker, why,
                  "You can no longer track or select transduced cells by the marker.")
        elif therapeutic:
            skip("marker", "Remove the reporter or selection marker", "%s is kept because it helps you track "
                 "transduced cells ex vivo. Remove it for a clinical-grade product." % marker)
    if vector == "aav" and cur.wpre and not cur.wpre_short and (size / limit > 0.75 or not fits()):
        apply(dataclasses.replace(cur, wpre_short=True), "wpre-short", "Use the short WPRE3",
              "WPRE: 589 bp -> %d bp" % WPRE_SHORT_LEN,
              "The cassette uses %d%% of the AAV capacity, so the 589 bp WPRE is replaced by the %d bp version."
              % (round(100 * size / limit), WPRE_SHORT_LEN), WPRE_NOTE)
    if cur.wpre and not fits():
        trial = dataclasses.replace(cur, wpre=False, wpre_short=False)
        if capacity_points(vector, cassette_size(trial))[1]:
            apply(trial, "wpre-drop", "Remove WPRE to fit", "WPRE: on -> off",
                  "The cassette is too large for the %s and is the only change that makes it fit." % VECTOR_LABEL[vector],
                  "Expect lower expression: WPRE usually raises it, and in a published AAV comparison a cassette "
                  "without it gave about 29% of the level with it (Choi et al. 2014).")
        else:
            skip("wpre-drop", "Remove WPRE to fit", "Removing WPRE would not make the cassette fit, so the "
                 "enhancer is kept.")
    if vector == "aav" and cur.wpre and not cur.wpre_short and size / limit <= 0.75:
        saved = 589 - WPRE_SHORT_LEN
        skip("wpre-short", "Use the short WPRE3", "The cassette uses %d%% of the AAV capacity, so the full WPRE is "
             "kept. The short WPRE3 would save %d bp at some cost in expression if you need room." %
             (round(100 * size / limit), saved))
    if vector == "aav":
        skip("synthetic-polya", "Use a 49 bp synthetic polyA", "It is the smallest signal, but it roughly halved "
             "expression in the published comparison, so SV40 late (122 bp) is used instead.")
    if therapeutic and cur.resistance != "KanR":
        apply(dataclasses.replace(cur, resistance="KanR"), "resistance", "Use kanamycin selection for the plasmid",
              "Bacterial selection: %s -> KanR" % cur.resistance,
              "Kanamycin resistance is preferred over ampicillin for plasmids that make clinical vector, because "
              "regulators prefer to avoid beta-lactam resistance genes. It sits outside the cassette, so it does "
              "not change capacity.")
    if vector == "lenti" and (profile.polya or profile.donors):
        parts = []
        if profile.polya:
            parts.append("%d polyA-like signal(s)" % len(profile.polya))
        if profile.donors:
            parts.append("%d splice-donor-like site(s)" % len(profile.donors))
        skip("recode", "Remove cryptic polyA and splice sites", "The insert has %s that can truncate the lentiviral "
             "genome. Fixing that means editing your sequence (silent recoding), which this tool does not do for you."
             % " and ".join(parts))
    return cur, mods
