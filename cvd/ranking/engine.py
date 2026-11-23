"""Build every candidate layout for an insert, modify it, score it and rank it."""

import dataclasses
from typing import Dict, List

from ..design.builder import build_design
from ..model import Config
from ..parts.strategies import STRATEGIES
from ..seqops import pick
from .explain import basis_for_option
from .model import CriterionScore, Modification, RankingResult, VectorOption
from .optimize import cassette_size, optimize_config
from .scoring import (
    arrangement_rationale, capacity_points, expression_points, insert_points, parse_setting,
    profile_insert)
from .tables import (
    ARRANGEMENTS, ARRANGEMENTS_BY_STRATEGY, ARRANGEMENT_ORDER, CAPACITY, CRITERIA,
    RANKED_VECTORS, SAFETY, SETTING_BY_STRATEGY, SETTING_FIT, VECTOR_LABEL)


def rank_vector_options(cfg: Config, setting: str = "", optimize: bool = True) -> RankingResult:
    """Build every candidate layout for the insert, score it, and rank the candidates."""
    strat = pick(cfg.strategy, STRATEGIES, "strategy")
    user_setting = parse_setting(setting)
    if user_setting:
        eff, note = user_setting, "set by you"
    elif strat in SETTING_BY_STRATEGY:
        eff, note = SETTING_BY_STRATEGY[strat], "assumed for this strategy; choose a setting to override"
    else:
        eff, note = "unspecified", "not specified, so it does not separate the options"
    profile = profile_insert(cfg)
    options: List[VectorOption] = []
    reference: Dict[str, int] = {}
    for vector in RANKED_VECTORS:
        for arr in ARRANGEMENTS_BY_STRATEGY[strat]:
            spec = ARRANGEMENTS[arr]
            c = dataclasses.replace(cfg, vector=vector, promoter=spec["promoter"], wpre=spec["wpre"],
                                    overrides={}, basis="")
            base_cassette = cassette_size(c)
            mods: List[Modification] = []
            if optimize:
                c, mods = optimize_config(c, strat, vector, eff, profile)
            design = build_design(c)
            cassette = sum(f.length for f in design.features if f.in_cassette)
            reference.setdefault(vector, cassette)
            cap_pts, feasible, cap_reason, cap_short = capacity_points(vector, cassette)
            set_pts, set_short, set_reason = SETTING_FIT[eff][vector]
            exp_pts, exp_reason, exp_short = expression_points(strat, spec["promoter"])
            ins_pts, ins_reason, ins_short = insert_points(vector, profile)
            saf_pts, saf_short, saf_reason = (10, "research use", "Research use only: clinical safety is not scored "
                                              "for oncogene modeling.") if strat == "model" else SAFETY[vector]
            raw = {"capacity": (cap_pts, cap_reason, cap_short), "setting": (set_pts, set_reason, set_short),
                   "expression": (exp_pts, exp_reason, exp_short), "insert": (ins_pts, ins_reason, ins_short),
                   "safety": (saf_pts, saf_reason, saf_short)}
            scores = [CriterionScore(k, label, raw[k][0], mx, raw[k][1], raw[k][2]) for k, label, mx in CRITERIA]
            layout = spec["label"] + (" (%s)" % spec["promoter"] if spec["promoter"] else "")
            options.append(VectorOption(
                key="%s|%s" % (vector, arr), vector=vector, arrangement=arr, layout=layout,
                title="%s, %s" % (VECTOR_LABEL[vector], layout), config=c, design=design, cassette=cassette,
                limit=CAPACITY[vector][0], feasible=feasible, scores=scores, total=sum(s.points for s in scores),
                base_cassette=base_cassette, mods=mods))
    for o in options:
        o.generated_because = arrangement_rationale(strat, o.arrangement, o.vector, o.cassette, reference[o.vector])
    # options that fit come first, best score first; options that do not fit follow, closest fit first
    options.sort(key=lambda o: (not o.feasible, -o.total if o.feasible else o.cassette / o.limit,
                                ARRANGEMENT_ORDER.index(o.arrangement), o.cassette, o.vector))
    for i, o in enumerate(options, 1):
        o.rank = i
    res = RankingResult(strat, profile, eff, note, options, optimize)
    for o in options:
        o.design.basis = basis_for_option(res, o)
    return res
