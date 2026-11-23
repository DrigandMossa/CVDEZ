"""Write every export format for a design to a folder."""

import os
import re
from typing import List

from ..model import Design
from .fasta import to_fasta
from .genbank import to_genbank
from .summary import to_summary
from .svgmap import to_svg


def write_outputs(d: Design, outdir: str) -> List[str]:
    os.makedirs(outdir, exist_ok=True)
    stem = re.sub(r"[^\w.-]+", "_", d.name).strip("_") or "vector"
    paths = []
    for ext, text in ((".gb", to_genbank(d)), (".fasta", to_fasta(d)), (".svg", to_svg(d)), (".txt", to_summary(d))):
        p = os.path.join(outdir, stem + ext)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        paths.append(p)
    return paths
