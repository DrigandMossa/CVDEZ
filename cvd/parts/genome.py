"""Genome coordinates and the cancer-gene / immune annotations used by the CNV analysis."""


# (chromosome length, approximate centromere position) in bp. Centromere positions are
# approximate (within a few Mb). Arm calls need 80% of an arm, so this does not change them.
BUILDS = {
    "hg38": {"1": (248956422, 123400000), "2": (242193529, 93900000), "3": (198295559, 90900000),
             "4": (190214555, 50000000), "5": (181538259, 48800000), "6": (170805979, 59800000),
             "7": (159345973, 60100000), "8": (145138636, 45200000), "9": (138394717, 43000000),
             "10": (133797422, 39800000), "11": (135086622, 53400000), "12": (133275309, 35500000),
             "13": (114364328, 17700000), "14": (107043718, 17200000), "15": (101991189, 19000000),
             "16": (90338345, 36800000), "17": (83257441, 25100000), "18": (80373285, 18500000),
             "19": (58617616, 26200000), "20": (64444167, 28100000), "21": (46709983, 12000000),
             "22": (50818468, 15000000)},
    "hg19": {"1": (249250621, 125000000), "2": (243199373, 93300000), "3": (198022430, 91000000),
             "4": (191154276, 50400000), "5": (180915260, 48400000), "6": (171115067, 61000000),
             "7": (159138663, 59900000), "8": (146364022, 45600000), "9": (141213431, 49000000),
             "10": (135534747, 40200000), "11": (135006516, 53700000), "12": (133851895, 35800000),
             "13": (115169878, 17900000), "14": (107349540, 17600000), "15": (102531392, 19000000),
             "16": (90354753, 36600000), "17": (81195210, 24000000), "18": (78077248, 17200000),
             "19": (59128983, 26500000), "20": (63025520, 27500000), "21": (48129895, 13200000),
             "22": (51304566, 14700000)},
}
ACROCENTRIC_P = {"13p", "14p", "15p", "21p", "22p"}          # not scored (no usable p-arm sequence)
AUTOSOMES = [str(i) for i in range(1, 23)]
ARM_ORDER = [c + s for c in AUTOSOMES for s in "pq"]
N_SCORED_ARMS = len([a for a in ARM_ORDER if a not in ACROCENTRIC_P])   # 39

# well-known cancer genes by chromosome arm: tumor suppressors (tsg) and oncogenes (onc)
ARM_GENES = {"TP53": ("17p", "tsg"), "PTEN": ("10q", "tsg"), "RB1": ("13q", "tsg"), "CDKN2A": ("9p", "tsg"),
             "VHL": ("3p", "tsg"), "SMAD4": ("18q", "tsg"), "STK11": ("19p", "tsg"), "CDKN1A": ("6p", "tsg"),
             "BRCA1": ("17q", "tsg"), "APC": ("5q", "tsg"), "NF1": ("17q", "tsg"),
             "KRAS": ("12p", "onc"), "MYC": ("8q", "onc"), "BRAF": ("7q", "onc"), "EGFR": ("7p", "onc"),
             "PIK3CA": ("3q", "onc"), "CTNNB1": ("3p", "onc"), "BCL2": ("18q", "onc")}

# arm, direction of change, what lives there, why it matters for immune attack
IMMUNE_ARM_NOTES = [
    ("6p", "loss", "HLA class I region (6p21.3)",
     "Loss here can lower MHC-I and weaken CD8 T-cell recognition. A flag that does not need MHC-I is attractive."),
    ("15q", "loss", "B2M (15q21.1)",
     "B2M is needed for MHC-I on the cell surface. Its loss is a known route of resistance to checkpoint blockade."),
    ("6q", "loss", "ULBP genes (6q25)",
     "The ULBP genes encode NKG2D ligands, so loss lowers the cells' own ligands. A vector-supplied ligand can offset that."),
    ("9p", "loss", "type I interferon cluster with CDKN2A (9p21.3)",
     "Deletions that take the interferon cluster have been linked to immune evasion and checkpoint-blockade resistance."),
    ("9p", "gain", "CD274 (PD-L1) and JAK2 (9p24.1)",
     "Extra copies can raise PD-L1, a checkpoint signal that restrains T cells."),
    ("3q", "gain", "CD47 (3q13.12)",
     "CD47 is the don't-eat-me signal for macrophages. Extra copies may raise it."),
]


# arm-level log2 ratios for the synthetic example (all other arms are neutral)
EXAMPLE_ARM_VALUES = {"1q": 0.40, "3q": 0.50, "5p": 0.45, "6p": -0.45, "7p": 0.50, "7q": 0.50, "8q": 0.60,
                      "9p": -0.70, "10q": -0.50, "13q": -0.45, "15q": -0.50, "17p": -0.80, "18q": -0.60, "20q": 0.40}
