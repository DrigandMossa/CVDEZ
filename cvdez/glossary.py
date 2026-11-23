"""Plain-language explanations of the parts of a vector, keyed by the feature kind CVD reports."""

KIND = {
    "itr": ("ITR (inverted terminal repeat)",
            "The two ends of an AAV genome. The virus uses them to copy and package the DNA. Everything you want delivered "
            "must fit BETWEEN them."),
    "ltr": ("LTR (long terminal repeat)",
            "The two ends of a lentiviral genome. Like ITRs, they mark what gets packaged and copied into the cell."),
    "promoter": ("Promoter",
                 "The 'on switch' that tells the cell to read the gene next to it. A strong promoter makes lots of protein; a "
                 "tumor-selective one (Survivin, hTERT) is mostly active in cancer cells."),
    "reg": ("Regulatory element",
            "A small helper such as a Kozak sequence (helps the cell start reading the gene) or WPRE (boosts how much "
            "message is made and kept)."),
    "cds": ("Your gene (coding sequence)",
            "The actual instructions for the protein you want the cell to make. This is the 'insert'."),
    "stop": ("Stop codon", "Tells the cell where the protein ends."),
    "polya": ("PolyA signal", "A 'full stop' for the messenger RNA that also makes it stable."),
    "marker": ("Marker", "A glowing or drug-resistance gene that lets you see or select the cells that took up the vector."),
    "link": ("Linker", "Joins the gene to a marker so both are made from one message (P2A makes two separate proteins)."),
    "tag": ("Tag", "A short protein label you can detect with an antibody."),
    "pack": ("Packaging element",
             "Lentivirus needs a few extra signals (Psi, RRE, cPPT) so the genome is recognised, exported and copied "
             "into the target cell."),
    "guide": ("Guide (shRNA or sgRNA)",
              "A short RNA that switches off or edits one target gene instead of adding a new one."),
    "ori": ("Origin of replication",
            "Lets bacteria copy the plasmid while you grow it. It lives OUTSIDE the packaged part, so it does not use "
            "up capacity."),
    "bact": ("Bacterial resistance gene",
             "Lets only plasmid-carrying bacteria grow in antibiotic. Also outside the packaged part."),
}

DEFAULT = ("Part", "A piece of the vector.")


def explain_kind(kind: str):
    return KIND.get(kind, DEFAULT)
