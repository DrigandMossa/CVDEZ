"""Cancer Gene Therapy Vector Designer.

Design viral vectors (lentivirus, AAV or plain plasmid) around cancer-relevant inserts,
check the insert sequence, call arm-level aneuploidy from copy-number segments, and export
GenBank, FASTA, SVG and text summaries.  Standard library only (Python 3.8+).

Research design tool.  Library elements use typical lengths and are written as runs of N
until verified sequences are supplied.  Producing virus requires institutional biosafety
approval; a clinical product requires GMP manufacturing, preclinical safety data and
regulatory authorization.

    python -m cvd                      open the graphical window
    python -m cvd --wizard             answer text prompts instead
    python -m cvd --list               show strategies, genes and parts
    python -m cvd --cnv segments.tsv   aneuploidy analysis and design suggestions
    python -m cvd --rank ...           ranked, prebuilt vector options for an insert

See README.md for the full option reference.
"""

from .version import __version__

__all__ = ["__version__"]
