"""Gene library: typical ORF length (bp, without the stop codon) and a short note."""

from typing import Dict, Tuple


GENES: Dict[str, Tuple[int, str]] = {
    "Custom": (1000, ""),
    "TP53": (1182, "TP53 is the most frequently mutated tumor suppressor. Use the wild-type sequence for replacement."),
    "PTEN": (1212, ""), "RB1": (2787, ""), "CDKN2A": (471, "Encodes p16INK4a."),
    "VHL": (639, ""), "SMAD4": (1659, ""), "STK11": (1302, ""),
    "CDKN1A": (495, "Encodes p21."),
    "BRCA1": (5592, "Large ORF: check the capacity message for your vector type."),
    "APC": (8532, "Very large ORF: too big for AAV and difficult for lentivirus."),
    "NF1": (8520, "Very large ORF: too big for AAV and difficult for lentivirus."),
    "HSV-TK": (1131, "Pair with ganciclovir to kill transduced cells."),
    "iCasp9": (1170, "The dimerizer AP1903 (rimiducid) triggers apoptosis."),
    "CD::UPRT": (1100, "Converts 5-fluorocytosine (5-FC) into toxic 5-FU."),
    "IL-12 (single chain)": (1600, "p40-linker-p35 fusion."),
    "IL-15": (486, ""), "IL-2": (462, ""), "GM-CSF": (435, ""),
    "CD19": (750, ""), "BCMA": (750, ""), "HER2": (750, ""), "GD2": (750, ""),
    "Mesothelin": (750, ""), "EGFRvIII": (750, ""), "CD22": (750, ""),
    "KRAS": (570, ""), "MYC": (1311, ""), "BRAF": (2301, ""), "EGFR": (3633, ""),
    "PIK3CA": (3207, ""), "CTNNB1": (2346, ""), "BCL2": (720, ""),
    # immune-flag payloads (typical ORF lengths without the stop codon)
    "ULBP2": (738, "NKG2D ligand. Marks cells for NK and CD8 T-cell attack without needing MHC-I. Proteases can shed "
                   "NKG2D ligands from the surface and the soluble form can blunt NKG2D, so check surface retention."),
    "ULBP1": (732, "NKG2D ligand, GPI-anchored. Marks cells for NK and CD8 T-cell attack without needing MHC-I."),
    "MICA": (1149, "NKG2D ligand. Proteases (ADAM10, ADAM17) can shed it from tumor cells, which blunts the effect."),
    "MICB": (1149, "NKG2D ligand. Can be shed from tumor cells in the same way as MICA."),
    "CALR": (1251, "Calreticulin. Surface calreticulin is an 'eat me' signal for macrophages. Often paired with CD47 knockdown."),
    "tEGFR (surface tag)": (1071, "Truncated EGFR without its signaling domain. Cetuximab binds it and can kill cells "
                                  "through ADCC and CDC. Length is approximate; paste your sequence."),
    "Bispecific T-cell engager (secreted)": (1600, "Secreted anti-CD3 by tumor-antigen engager. Paste your scFv sequences; "
                                                   "length is approximate."),
    "CD47": (969, "Don't-eat-me signal for macrophages. Knock it down with an shRNA."),
    "CD274": (870, "PD-L1. Knock it down with an shRNA to release T cells."),
}
