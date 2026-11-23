"""Interactive text prompts, used with --wizard or when no window can be opened."""

from typing import List, Tuple

from ..model import Config
from ..parts.elements import (COSTIM, HINGES, LINKS, MARKERS, PROMOTERS, TAGS, VECTORS)
from ..parts.strategies import STRATEGIES
from ..version import __version__
from .args import read_seq_arg


def _choose(label: str, options: List[str], default: str) -> str:
    print("\n%s" % label)
    for i, o in enumerate(options, 1):
        print("  %2d) %s%s" % (i, o, "   [default]" if o == default else ""))
    while True:
        raw = input("Choose 1-%d or type a name (Enter for default): " % len(options)).strip()
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        for o in options:
            if o.lower() == raw.lower():
                return o
        print("Not an option, try again.")


def wizard() -> Tuple[Config, str]:
    print("Cancer Gene Therapy Vector Designer %s" % __version__)
    print("Answer the prompts, or press Enter to accept a default.")
    cfg = Config()
    cfg.vector = _choose("Vector type", VECTORS, "lenti")
    keys = list(STRATEGIES)
    labels = ["%s: %s" % (k, STRATEGIES[k]["name"]) for k in keys]
    chosen = _choose("Therapeutic strategy", labels, labels[0])
    cfg.strategy = keys[labels.index(chosen)]
    S = STRATEGIES[cfg.strategy]
    print("\n" + S["tip"])
    cfg.gene = _choose("Gene", S["genes"], S["genes"][0])
    if cfg.gene == "Custom":
        cfg.gene = input("Gene name: ").strip() or "Custom"
    if cfg.strategy == "guide":
        cfg.guide_type = _choose("Guide type", ["shRNA", "sgRNA"], "shRNA")
        cfg.target = read_seq_arg(input("\nTarget sequence (or file path; Enter for a placeholder): ").strip())
    else:
        if cfg.strategy != "guide":
            cfg.variant = input("\nVariant label, for example R175H (Enter to skip): ").strip()
        cfg.sequence = read_seq_arg(input("Insert sequence or FASTA file path (Enter for a placeholder): ").strip())
        if cfg.strategy == "car":
            cfg.hinge = _choose("CAR hinge/transmembrane", list(HINGES), "CD8a hinge/TM")
            cfg.costim = _choose("Costimulatory domain", list(COSTIM), "4-1BB")
        else:
            cfg.tag = _choose("C-terminal tag", list(TAGS), "none")
    cfg.promoter = _choose("Promoter", list(PROMOTERS), S["promoter"]) if cfg.strategy != "guide" else None
    cfg.marker = _choose("Reporter / selection marker", list(MARKERS), S["marker"])
    if cfg.marker != "none" and cfg.strategy != "guide":
        cfg.link = _choose("Marker linked by", list(LINKS), "P2A")
    cfg.name = input("\nVector name (Enter for a generated name): ").strip()
    out = input("Output folder (Enter for the current folder): ").strip() or "."
    return cfg, out
