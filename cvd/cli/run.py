"""Mode dispatch and the process entry point."""

import os
import sys
from typing import List, Optional

from ..cnv.advice import basis_text, config_from_recommendation, recommend
from ..cnv.analysis import analyze_aneuploidy
from ..cnv.report import aneuploidy_report, example_cnv_text, write_aneuploidy_files
from ..cnv.segments import parse_segments
from ..design.builder import build_design
from ..export.files import write_outputs
from ..gui import launch_gui
from ..model import Design, Recommendation
from ..parts.genome import BUILDS
from .args import build_parser, config_from_args, print_catalog
from .rank import run_ranking, wants_ranking
from .wizard import wizard

def report(d: Design, paths: List[str]) -> None:
    print("\n%s  |  %s  |  %s bp" % (d.name, d.vector, format(d.total, ",")))
    print("-" * 60)
    for f in d.features:
        print("%-10s %5d..%-6d %6d bp  %s" % (f.id, f.start, f.end, f.length, f.name))
    print("\nDesign checks")
    for level, text in d.messages:
        print("  [%s] %s" % (level, text))
    print("\nFiles written:")
    for p in paths:
        print("  " + p)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    no_arguments = argv is None and len(sys.argv) == 1
    args = parser.parse_args(argv)
    if args.list:
        print_catalog()
        return 0
    if args.example_cnv:
        try:
            with open(args.example_cnv, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(example_cnv_text(args.build if args.build in BUILDS else "hg38"))
        except OSError as exc:
            print("Error: %s" % exc, file=sys.stderr)
            return 2
        print("Wrote a synthetic example segment file to %s. Try: python -m cvd --cnv %s"
              % (args.example_cnv, args.example_cnv))
        return 0
    cnv_rec: Optional[Recommendation] = None
    cnv_basis = ""
    if args.cnv:
        try:
            with open(args.cnv, "r", encoding="utf-8", errors="replace") as fh:
                segments, vtype, notes, sample_name = parse_segments(fh.read(), args.cnv_type, args.sample)
            result = analyze_aneuploidy(segments, args.build, vtype, args.ploidy, not args.no_center,
                                        args.gain_threshold, args.loss_threshold, sample_name, notes)
            recs = recommend(result)
            if args.design_from_cnv is not None and not 1 <= args.design_from_cnv <= len(recs):
                raise ValueError("--design-from-cnv must be between 1 and %d." % len(recs))
            stem = sample_name or os.path.splitext(os.path.basename(args.cnv))[0]
            files = write_aneuploidy_files(result, recs, args.out, stem)
        except (ValueError, OSError) as exc:
            print("Error: %s" % exc, file=sys.stderr)
            return 2
        print(aneuploidy_report(result, recs))
        print("Files written:\n  " + "\n  ".join(files))
        if args.design_from_cnv is None:
            return 0
        cnv_rec = recs[args.design_from_cnv - 1]
        cnv_basis = basis_text(result, cnv_rec)
        print("\nBuilding the vector for suggestion %d: %s (%s)\n" % (args.design_from_cnv, cnv_rec.title, cnv_rec.gene))
    elif args.design_from_cnv is not None:
        print("Error: --design-from-cnv needs --cnv FILE.", file=sys.stderr)
        return 2
    wizard_mode = args.wizard
    if not wizard_mode and (args.gui or no_arguments):
        status = launch_gui()
        if status == 0 or args.gui:
            return status
        print("Falling back to text prompts.\n", file=sys.stderr)
        wizard_mode = True
    try:
        if wizard_mode:
            cfg, out = wizard()
        else:
            cfg, out = config_from_args(args), args.out
            if cnv_rec is not None:
                cfg = config_from_recommendation(cfg, cnv_rec, cnv_basis, keep_promoter=bool(args.promoter))
            if wants_ranking(args):
                status, cfg = run_ranking(args, cfg, out)
                if status is not None:
                    return status
        design = build_design(cfg)
        paths = write_outputs(design, out)
    except (ValueError, OSError) as exc:
        print("Error: %s" % exc, file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return 130
    report(design, paths)
    if args.strict and any(level == "error" for level, _ in design.messages):
        return 1
    return 0
