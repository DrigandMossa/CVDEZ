"""Fixed tables behind the ranking: capacities, criteria weights, layouts and the rule text."""


RANKED_VECTORS = ["lenti", "aav"]


VECTOR_SHORT = {"lenti": "Lenti", "aav": "AAV"}


VECTOR_LABEL = {"lenti": "Lentivirus", "aav": "AAV"}


SETTING_CHOICES = ["Not specified", "In vivo", "Ex vivo"]


SETTING_BY_STRATEGY = {"car": "ex vivo", "model": "ex vivo"}


CAPACITY = {"aav": (4700, "about 4.7 kb between the ITRs"),
            "lenti": (8000, "about 8 kb between the LTRs; titer falls as inserts grow")}


LENTI_HARD_LIMIT = 1.25


CRITERIA = [("capacity", "Packaging capacity", 30), ("setting", "Therapeutic setting", 25),
            ("expression", "Expression pattern", 20), ("insert", "Insert vs vector genome", 15),
            ("safety", "Vector safety profile", 10)]


HOW_SCORES_WORK = ("How the score works: packaging capacity 30 + therapeutic setting 25 + expression pattern 20 + "
                   "insert vs vector genome 15 + vector safety profile 10 = 100. Options that exceed their vector's "
                   "capacity score 0 and rank after those that fit, closest fit first. Ties keep the layouts in a "
                   "fixed order (strong, compact, selective, T-cell), then the smaller cassette, then the vector "
                   "name. Each option is a complete prebuilt vector that has already been modified where the part library "
                   "allows (see its Modifications), and the scores are for the modified vector. The scores rank the "
                   "options generated here against each other using these rules; a high "
                   "score means the best fit among them, not a prediction of titer or efficacy.")


ARRANGEMENTS = {
    "strong": dict(label="strong constitutive promoter", promoter="EF1a", wpre=True),
    "compact": dict(label="compact promoter, no WPRE", promoter="EFS", wpre=False),
    "selective": dict(label="tumor-selective promoter", promoter="Survivin", wpre=True),
    "tcell": dict(label="T-cell promoter", promoter="MND", wpre=True),
    "standard": dict(label="U6 hairpin cassette", promoter=None, wpre=None),
}


ARRANGEMENT_ORDER = ["strong", "compact", "selective", "tcell", "standard"]


ARRANGEMENTS_BY_STRATEGY = {
    "rep": ["strong", "compact", "selective"], "sui": ["strong", "compact", "selective"],
    "cyt": ["strong", "compact", "selective"], "flag": ["strong", "compact", "selective"],
    "car": ["strong", "compact", "tcell"], "model": ["strong", "compact"], "guide": ["standard"]}


STRENGTH_WORD = {1: "weak", 2: "moderate", 3: "strong"}


PROMOTER_TRAITS = {"EF1a": dict(strength=3, selective=False, tcell=True),
                   "EFS": dict(strength=2, selective=False, tcell=True),
                   "MND": dict(strength=3, selective=False, tcell=True),
                   "Survivin": dict(strength=1, selective=True, tcell=False)}


STRATEGY_NEEDS = {
    "rep": (0, 2, False, "A replacement gene needs enough expression to restore function; restricting it to tumor "
                         "cells is optional."),
    "sui": (2, 1, False, "A suicide gene kills every cell that makes it, so restricting expression to tumor cells "
                         "matters most; modest expression can be enough because the prodrug or dimerizer drives the kill."),
    "cyt": (1, 2, False, "Cytokines such as IL-12 can be toxic when made throughout the body, so tumor-restricted "
                         "expression helps, but they still need reasonable expression."),
    "flag": (2, 2, False, "An immune flag marks every cell that makes it, so tumor-restricted expression matters "
                          "most, though a weak promoter may leave too little on the cell surface."),
    "car": (0, 3, True, "CAR constructs are expressed in T cells, so the promoter must be strong and work there."),
    "model": (0, 3, False, "Oncogene modeling needs strong, stable expression in cultured cells; tumor selectivity "
                           "is not needed.")}


SETTING_FIT = {
    "ex vivo": {
        "lenti": (25, "keeps gene in dividing cells",
                  "Cells are engineered outside the body and then expand. Lentivirus integrates, so the gene is "
                  "copied with the cell; this is why it is the usual choice for engineering T cells and cultured cells."),
        "aav": (8, "episome diluted by division",
                "AAV genomes mostly stay as episomes that are not copied when a cell divides, so expression fades "
                "as engineered cells expand.")},
    "in vivo": {
        "aav": (25, "direct, non-integrating",
                "The vector is injected into the patient. AAV is the usual choice: it transduces many non-dividing "
                "tissues, mostly does not integrate, and can express for a long time in cells that do not divide. "
                "In rapidly dividing tumor cells the episome is diluted, so expression there can be short-lived."),
        "lenti": (12, "integrating",
                  "Lentivirus can be injected, but it integrates into the host genome, which raises the "
                  "insertional-mutagenesis concern when it is given directly to a patient.")},
    "unspecified": {
        "lenti": (17, "not specified", "No delivery setting is set, so both vectors get the same points here. "
                                       "Choose in vivo or ex vivo to separate them."),
        "aav": (17, "not specified", "No delivery setting is set, so both vectors get the same points here. "
                                     "Choose in vivo or ex vivo to separate them.")}}


SAFETY = {"aav": (10, "mostly episomal", "AAV genomes mostly stay as episomes and rarely integrate, so the "
                                         "insertional-mutagenesis risk is low."),
          "lenti": (6, "integrates", "Lentivirus integrates into the host genome. A self-inactivating (dU3) LTR, "
                                     "which this design uses, lowers but does not remove the insertional-mutagenesis risk.")}


VECTOR_NOTES = {
    "aav": ["Many people already carry antibodies to AAV capsids, which can block delivery in vivo; choose the capsid "
            "and screen for neutralizing antibodies.",
            "High systemic AAV doses have been linked to liver toxicity, so local delivery or lower doses are preferred "
            "where possible.",
            "Self-complementary AAV roughly halves the capacity (not modeled here)."],
    "lenti": ["Production needs packaging plasmids and biosafety approval.",
              "Integration sites cannot be controlled, so clinical studies track them."]}


THERAPEUTIC = {"rep", "sui", "cyt", "flag", "car"}


WPRE_NOTE = ("In a published AAV comparison, the 247 bp short WPRE kept about 83% of the full element's expression "
             "(a difference the authors did not find significant), so a little enhancement is traded for space "
             "(Choi et al. 2014, Mol Brain 7:17; neuron data, so other tissues may differ).")
