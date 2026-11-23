"""Argument parsing, the parts catalogue listing, and Config construction."""

import argparse
import os
from typing import Optional

from ..model import Config
from ..parts.elements import (COSTIM, HINGES, LINKS, MARKERS, POLYA, PROMOTERS, RESISTANCE,
                              TAGS, VECTORS)
from ..parts.strategies import STRATEGIES
from ..version import __version__


def read_seq_arg(value: Optional[str]) -> str:
    """A path to a text/FASTA file, or the sequence itself."""
    if not value:
        return ""
    if os.path.isfile(value):
        with open(value, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    return value


def print_catalog() -> None:
    print("Vectors:      " + ", ".join(VECTORS))
    print("\nStrategies and their genes:")
    for k, v in STRATEGIES.items():
        print("  %-6s %s\n         genes: %s\n         %s" % (k, v["name"], ", ".join(v["genes"]), v["tip"]))
    for label, opts in (("Promoters", PROMOTERS), ("Markers", MARKERS), ("Linkers", LINKS), ("Tags", TAGS),
                        ("PolyA", POLYA), ("Bacterial selection", RESISTANCE),
                        ("CAR hinges", HINGES), ("CAR costimulatory", COSTIM)):
        print("%s: %s" % (label, ", ".join(opts)))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cvd", description="Cancer gene therapy viral vector designer.",
        epilog="Run with no arguments to open the graphical window. Use --list to see the available parts.")
    p.add_argument("--gui", action="store_true", help="open the graphical window (the default with no arguments)")
    p.add_argument("--wizard", action="store_true", help="answer text prompts instead of using the window")
    p.add_argument("--list", action="store_true", help="list strategies, genes and parts, then exit")
    p.add_argument("--vector", default="lenti", help="lenti, aav or plasmid (default: lenti)")
    p.add_argument("--strategy", default="rep", help="rep, sui, cyt, car, guide or model (default: rep)")
    p.add_argument("--gene", default="", help="gene or antigen name (library entry or any custom name)")
    p.add_argument("--variant", default="", help="variant label, for example R175H")
    p.add_argument("--seq", default="", help="insert ORF (or CAR scFv) as a file path or a sequence")
    p.add_argument("--promoter", help="promoter (default depends on strategy)")
    p.add_argument("--marker", help="reporter or selection marker (default depends on strategy)")
    p.add_argument("--link", default="P2A", help="how the marker is linked: P2A, IRES or 'separate PGK promoter'")
    p.add_argument("--tag", default="none", help="C-terminal tag")
    p.add_argument("--polya", help="polyadenylation signal: bGH, SV40 or none")
    p.add_argument("--resistance", default="AmpR", help="bacterial selection: AmpR or KanR")
    p.add_argument("--no-wpre", action="store_true", help="leave out WPRE")
    p.add_argument("--wpre", action="store_true", help="force WPRE on (default: on except for plasmid)")
    p.add_argument("--no-kozak", action="store_true", help="leave out the Kozak sequence")
    p.add_argument("--hinge", default="CD8a hinge/TM", help="CAR hinge/transmembrane domain")
    p.add_argument("--costim", default="4-1BB", help="CAR costimulatory domain: 4-1BB, CD28 or none")
    p.add_argument("--guide-type", default="shRNA", help="shRNA or sgRNA (guide strategy)")
    p.add_argument("--target", default="", help="shRNA sense strand or sgRNA protospacer (no PAM), or a file path")
    p.add_argument("--override", action="append", default=[], metavar="ID=SEQ",
                   help="replace a placeholder element with a verified sequence or file (repeatable)")
    p.add_argument("--cnv", metavar="FILE", help="copy-number segment file to analyze for aneuploidy")
    p.add_argument("--build", default="hg38", help="genome build of the segment file: hg38 or hg19 (default: hg38)")
    p.add_argument("--cnv-type", default="auto", help="value column: auto, cn (copy number) or log2")
    p.add_argument("--sample", help="sample name, when the segment file holds more than one")
    p.add_argument("--ploidy", type=float, help="baseline copy number for copy-number input (default: genome median)")
    p.add_argument("--gain-threshold", type=float, default=0.2, help="log2 ratio for a gain (default: 0.2)")
    p.add_argument("--loss-threshold", type=float, default=-0.2, help="log2 ratio for a loss (default: -0.2)")
    p.add_argument("--no-center", action="store_true", help="do not centre log2 ratios on their median")
    p.add_argument("--design-from-cnv", type=int, nargs="?", const=1, metavar="N",
                   help="after the analysis, build the vector for suggestion N (default 1)")
    p.add_argument("--example-cnv", metavar="FILE", help="write a synthetic example segment file and exit")
    p.add_argument("--rank", action="store_true",
                   help="generate and rank vector options for the insert, print the ranking and write an options report")
    p.add_argument("--explain", metavar="N|all",
                   help="print why ranked option N (or all) was suggested and how it compares; implies --rank")
    p.add_argument("--use-option", type=int, metavar="N",
                   help="build the vector for ranked option N; implies --rank")
    p.add_argument("--no-optimize", action="store_true",
                   help="rank the plain layouts without the suggested modifications")
    p.add_argument("--export-options", action="store_true",
                   help="with --rank, also write every prebuilt option (GenBank, FASTA, map, summary) to its own folder")
    p.add_argument("--short-wpre", action="store_true",
                   help="use the 247 bp short WPRE instead of the 589 bp WPRE (saves space in AAV)")
    p.add_argument("--setting", default="",
                   help="delivery setting used for ranking: 'in vivo' or 'ex vivo' (default: not specified)")
    p.add_argument("--name", default="", help="vector name (default: generated)")
    p.add_argument("--out", default=".", help="output folder (default: current folder)")
    p.add_argument("--strict", action="store_true", help="exit with status 1 if any design check reports an error")
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    return p


def config_from_args(a: argparse.Namespace) -> Config:
    overrides = {}
    for item in a.override:
        if "=" not in item:
            raise ValueError("--override needs ID=SEQUENCE, got %r" % item)
        key, val = item.split("=", 1)
        overrides[key.strip()] = read_seq_arg(val.strip())
    wpre = True if a.wpre else (False if a.no_wpre else None)
    return Config(vector=a.vector, strategy=a.strategy, gene=a.gene, variant=a.variant,
                  sequence=read_seq_arg(a.seq), promoter=a.promoter, marker=a.marker, link=a.link,
                  tag=a.tag, polya=a.polya, resistance=a.resistance, wpre=wpre, wpre_short=a.short_wpre,
                  kozak=not a.no_kozak,
                  hinge=a.hinge, costim=a.costim, guide_type=a.guide_type,
                  target=read_seq_arg(a.target), name=a.name, overrides=overrides)
