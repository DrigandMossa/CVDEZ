"""The --rank / --explain / --use-option modes: rank vector options for the insert."""

import argparse
import os
from typing import Optional, Tuple

from ..export.files import write_outputs
from ..model import Config
from ..parts.strategies import STRATEGIES
from ..ranking import (config_for_option, explain_option, options_table, parse_explain,
                       rank_vector_options, ranking_summary, write_options_report)


def wants_ranking(args: argparse.Namespace) -> bool:
    return bool(args.rank or args.explain is not None or args.use_option is not None)


def run_ranking(args: argparse.Namespace, cfg: Config, out: str) -> Tuple[Optional[int], Config]:
    """Print and write the ranking. Returns (exit status, config).

    The status is 0 when the run is finished and None when --use-option asks for the chosen
    option to be built, in which case the returned config is that option's.  ValueError is
    raised for a bad option number; the caller reports it.
    """
    ranking = rank_vector_options(cfg, args.setting, optimize=not args.no_optimize)
    count = len(ranking.options)
    if args.use_option is not None and not 1 <= args.use_option <= count:
        raise ValueError("--use-option must be between 1 and %d." % count)
    shown = parse_explain(args.explain, count) if args.explain is not None else []
    print("\n" + ranking_summary(ranking) + "\n\n" + options_table(ranking))
    for i in shown:
        print("\n" + "-" * 72 + "\n" + explain_option(ranking, i))
    stem = (cfg.gene.strip() or STRATEGIES[ranking.strategy]["name"]) + "_" + cfg.strategy
    report_path = write_options_report(ranking, out, stem)
    if not shown:
        print("\nUse --explain N (or all) to see why an option was suggested and how it compares.")
    written = [report_path]
    if args.export_options:
        for o in ranking.options:
            written += write_outputs(o.design, os.path.join(out, "option%d" % o.rank))
    print("\nFiles written:\n  " + "\n  ".join(written))
    if args.use_option is None:
        return 0, cfg
    chosen = ranking.options[args.use_option - 1]
    print("\nBuilding the vector for option %d: %s\n" % (args.use_option, chosen.title))
    return None, config_for_option(cfg, ranking, chosen)
