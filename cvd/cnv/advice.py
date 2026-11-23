"""Rule-based design suggestions from arm-level calls.

The rules follow known gene locations and published associations.  They are not
predictions of response.
"""

from typing import List

from ..model import AneuploidyResult, Config, Recommendation
from ..parts.genes import GENES
from ..parts.genome import ARM_GENES
from ..parts.strategies import STRATEGIES


def recommend(res: AneuploidyResult) -> List[Recommendation]:
    """Rule-based design suggestions from the arm calls. They follow known gene locations and
    published associations; they are not predictions of response."""
    calls = {a.arm: a.call for a in res.arms}
    recs: List[Recommendation] = []

    def add(strategy: str, gene: str, title: str, reason: str) -> None:
        if not any(r.strategy == strategy and r.gene == gene for r in recs):
            recs.append(Recommendation(strategy, gene, STRATEGIES[strategy]["promoter"], title, reason))

    why = []
    if calls.get("6p") == "loss" or calls.get("15q") == "loss":
        why.append("6p or 15q is lost (HLA class I region, B2M), which points to weaker MHC-I presentation, so a flag "
                   "that does not need MHC-I is attractive.")
    if calls.get("6q") == "loss":
        why.append("6q is lost and carries the ULBP genes, so the cells probably have fewer NKG2D ligands of their own.")
    add("flag", "ULBP2", "NKG2D ligand flag",
        " ".join(why + ["NKG2D ligands mark stressed or transformed cells for attack by NK cells and CD8 T cells. Shed "
                        "soluble ligand can blunt the effect, so check that it stays on the surface in your model."]))
    add("flag", "tEGFR (surface tag)", "Surface tag for cetuximab",
        "Adds an inert surface epitope that cetuximab can target (ADCC and CDC), and that a matching CAR could target. "
        "It does not rely on MHC-I or on NKG2D.")
    if calls.get("3q") == "gain":
        add("flag", "CALR", "Calreticulin eat-me signal",
            "3q is gained and carries CD47, the don't-eat-me signal. Surface calreticulin is the opposing eat-me signal "
            "for macrophages.")
        add("guide", "CD47", "CD47 knockdown", "3q is gained, so CD47 dosage may be raised. Knocking it down exposes "
                                              "the cells to macrophages. Pair with an eat-me flag.")
    if res.score >= 10 or res.wgd_suspected:
        add("cyt", "IL-12 (single chain)", "Cytokine to warm up the tumor",
            "Tumors with many arm-level events tend to show markers of immune evasion and respond less well to "
            "immunotherapy (Davoli et al., Science 2017). Local IL-12 can help recruit and activate immune cells. "
            "Watch for systemic toxicity.")
    if calls.get("9p") == "gain":
        add("guide", "CD274", "PD-L1 knockdown", "9p is gained and carries CD274 (PD-L1) and JAK2. Knocking PD-L1 down "
                                                "can release T cells.")
    n_tsg = n_onc = 0
    for gene, (arm, role) in ARM_GENES.items():
        if role == "tsg" and calls.get(arm) == "loss" and n_tsg < 2 and GENES[gene][0] <= 3000:
            n_tsg += 1
            add("rep", gene, "Replace %s" % gene,
                "%s is lost and carries the tumor suppressor %s. Arm-level loss does not prove the gene is inactive, so "
                "confirm with mutation and expression data." % (arm, gene))
        elif role == "onc" and calls.get(arm) == "gain" and n_onc < 2:
            n_onc += 1
            add("guide", gene, "Knock down %s" % gene,
                "%s is gained and carries the oncogene %s. Confirm that %s is a dependency in your model before "
                "committing." % (arm, gene, gene))
    return recs


def basis_text(res: AneuploidyResult, rec: Recommendation) -> str:
    where = "sample %s, " % res.sample if res.sample else ""
    return ("Aneuploidy analysis (%s%s): score %d (%d gains, %d losses), %.0f%% of the genome altered.\n"
            "Chosen design: %s (%s). %s" % (where, res.build, res.score, res.gains, res.losses, res.fga,
                                          rec.title, rec.gene, rec.reason))


def config_from_recommendation(cfg: Config, rec: Recommendation, basis: str, keep_promoter: bool = False) -> Config:
    cfg.strategy, cfg.gene, cfg.basis = rec.strategy, rec.gene, basis
    if rec.promoter and not keep_promoter:
        cfg.promoter = rec.promoter
    return cfg
