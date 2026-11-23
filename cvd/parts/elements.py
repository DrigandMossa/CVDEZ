"""Vector element catalogue: promoters, markers, tags, linkers and their lengths.

Lengths are typical values in base pairs.  Elements without a built-in sequence are
written as runs of N until the user supplies a verified sequence.
"""


VECTORS = ["lenti", "aav", "plasmid"]

PROMOTERS = {"CMV": 508, "EF1a": 1178, "EFS": 212, "CAG": 1733, "PGK": 516,
             "UbC": 1220, "hSyn": 469, "SV40": 330, "MND": 255,
             "hTERT": 450, "Survivin": 270}
TUMOR_SELECTIVE = {"hTERT", "Survivin"}
MARKERS = {"none": 0, "EGFP": 720, "mCherry": 711, "Puro": 600, "Neo": 795,
           "Blast": 399, "Hygro": 1026}
POLYA = {"bGH": 225, "SV40": 122, "none": 0}
WPRE_SHORT_LEN = 247          # shortened WPRE ("WPRE3"), Choi et al. 2014, Mol Brain 7:17
RESISTANCE = {"AmpR": 861, "KanR": 816}
TAGS = {"none": "",
        "FLAG3": "GACTACAAAGACCATGACGGTGATTATAAAGATCATGACATCGACTACAAGGATGACGATGACAAG",
        "HA": "TACCCATACGATGTTCCAGATTACGCT",
        "Myc": "GAACAAAAACTCATCTCAGAAGAGGATCTG",
        "His6": "CATCACCATCACCATCAC"}
LINKS = {"P2A": 0, "IRES": 580, "separate PGK promoter": 516}
HINGES = {"CD8a hinge/TM": 204, "CD28 hinge/TM": 201}
COSTIM = {"4-1BB": 126, "CD28": 123, "none": 0}
P2A_SEQ = "GGAAGCGGAGCTACTAACTTCAGCCTGCTGAAGCAGGCTGGAGACGTGGAGGAGAACCCTGGACCT"
SGRNA_SCAFFOLD = ("GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC")
SHRNA_LOOP = "TTCAAGAGA"


# element kind -> (SVG color, GenBank feature key)
KINDS = {
    "ltr": ("#6b7f90", "LTR"), "itr": ("#6b7f90", "repeat_region"),
    "pack": ("#9b7bd8", "misc_feature"), "promoter": ("#e8a317", "promoter"),
    "cds": ("#1fa971", "CDS"), "tag": ("#18a5b8", "misc_feature"),
    "marker": ("#e0483f", "CDS"), "reg": ("#7a63d1", "misc_feature"),
    "polya": ("#8497a5", "polyA_signal"), "ori": ("#a7b5c0", "rep_origin"),
    "bact": ("#d6479a", "CDS"), "link": ("#3b82d6", "misc_feature"),
    "stop": ("#c0392b", "misc_feature"), "guide": ("#e56b2f", "misc_feature"),
}
# these elements get their sequence from the insert options or are built in
BUILT_IN_IDS = {"goi", "guide", "kozak", "stop", "tag", "p2a", "term"}
