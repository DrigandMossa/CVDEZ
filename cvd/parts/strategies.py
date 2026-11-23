"""Therapeutic strategies: the genes they offer, their defaults and their guidance."""


STRATEGIES = {
    "rep": dict(name="Tumor suppressor replacement",
                genes=["TP53", "PTEN", "RB1", "CDKN2A", "VHL", "SMAD4", "STK11",
                       "CDKN1A", "BRCA1", "APC", "NF1", "Custom"],
                promoter="EF1a", marker="none",
                tip="Restores a lost tumor suppressor. Use the wild-type ORF. AAV suits in vivo delivery; lentivirus suits ex vivo work."),
    "sui": dict(name="Suicide gene and prodrug",
                genes=["HSV-TK", "iCasp9", "CD::UPRT", "Custom"],
                promoter="Survivin", marker="none",
                tip="Tumor-selective promoters (hTERT, Survivin) limit expression to cancer cells. A prodrug or dimerizer then kills the transduced cells."),
    "cyt": dict(name="Immunostimulatory cytokine",
                genes=["IL-12 (single chain)", "IL-15", "IL-2", "GM-CSF", "Custom"],
                promoter="EF1a", marker="none",
                tip="Local cytokine expression recruits and activates immune cells. Watch for systemic toxicity."),
    "flag": dict(name="Immune flagging of aneuploid tumor cells",
                 genes=["ULBP2", "ULBP1", "MICA", "MICB", "CALR", "tEGFR (surface tag)",
                        "Bispecific T-cell engager (secreted)", "Custom"],
                 promoter="Survivin", marker="none",
                 tip="Expresses a protein that marks tumor cells for immune attack: an NKG2D ligand (NK and CD8 T cells), "
                     "calreticulin (macrophage 'eat me' signal), a surface tag for cetuximab, or a secreted T-cell engager. "
                     "Run the aneuploidy analysis to choose the payload. The vector cannot sense aneuploidy itself; "
                     "selectivity comes from delivery and the tumor-selective promoter."),
    "car": dict(name="CAR T-cell therapy",
                genes=["CD19", "BCMA", "HER2", "GD2", "Mesothelin", "EGFRvIII", "CD22", "Custom"],
                promoter="MND", marker="none",
                tip="Lentivirus is the usual choice for ex vivo T-cell engineering. Supply your scFv sequence and pick the hinge and costimulatory domains."),
    "guide": dict(name="Oncogene knockdown or editing",
                  genes=["KRAS", "MYC", "BCL2", "BRAF", "EGFR", "CTNNB1", "PIK3CA", "CD274", "CD47", "Custom"],
                  promoter="EF1a", marker="Puro",
                  tip="U6-driven vector to knock down (shRNA) or edit (sgRNA) an oncogene, a mutant allele or an immune "
                      "checkpoint or don't-eat-me gene (CD274, CD47). Supply your target sequence."),
    "model": dict(name="Cancer modeling (research use)",
                  genes=["KRAS", "MYC", "BRAF", "EGFR", "PIK3CA", "CTNNB1", "BCL2", "Custom"],
                  promoter="EF1a", marker="Puro",
                  tip="Oncogene expression for transformation assays and animal models. Use the variant label for hotspot mutations."),
}
