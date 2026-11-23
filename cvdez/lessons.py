"""The lessons.  Each lesson is a function (Context) -> None that teaches one part of CVD and then
does that part for real with the CVD engine, so every screen shows genuine program output."""

import os
import pkgutil
from typing import Callable, List, Optional, Tuple

from cvd.cnv.advice import basis_text, config_from_recommendation, recommend
from cvd.cnv.analysis import analyze_aneuploidy
from cvd.cnv.report import aneuploidy_report, example_cnv_text, write_aneuploidy_files
from cvd.cnv.segments import parse_segments
from cvd.design.builder import build_design
from cvd.export.files import write_outputs
from cvd.model import Config
from cvd.parts.genes import GENES
from cvd.parts.strategies import STRATEGIES
from cvd.ranking import (config_for_option, explain_option, options_table, rank_vector_options,
                         ranking_summary, write_options_report)

from .glossary import explain_kind
from .ui import Console

# A deliberately tiny, made-up "gene" used only to show what the sequence checker does.
# It is NOT a real gene and must never be used for anything but this lesson.
TOY_ORF = "ATGGCTAATAAAGGTGAGTCCGAAGCTGGTTAA"


class Context:
    """Everything the lessons share: the console, the output folder and the choices made so far."""

    def __init__(self, ui: Console, out: str):
        self.ui = ui
        self.out = out
        self.seg_text = ""
        self.seg_name = "practice_tumor"
        self.result = None
        self.recs = []
        self.rec = None               # the suggestion the learner chose
        self.cfg = Config()
        self.setting = ""
        self.ranking = None
        self.option = None
        self.design = None
        self.files: List[str] = []


# ---------------------------------------------------------------------------
def welcome(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 1 of 10: Welcome")
    u.say("This tutorial walks you through CVD, a tool that helps you DESIGN a gene therapy delivery vector for a cancer. "
          "By the end you will have built a complete example design from start to finish, and you will know what every "
          "part of the program does.")
    u.say("You will make one example gene therapy: a replacement copy of the tumor suppressor TP53 for a practice tumor whose "
          "chromosome arm 17p (where TP53 lives) has been lost. Every step shows you what the real program prints.")
    u.say("Please keep three things in mind:\n\n"
          "- This is a design and learning tool. Nothing here makes a virus.\n\n"
          "- Parts of the vector are written as runs of N until you paste verified sequences. The lengths are typical, so "
          "the map and the size checks are meaningful, but the file is not ready to order.\n\n"
          "- Making real virus needs biosafety approval, and a medicine for patients needs manufacturing, safety data and "
          "regulatory approval.")
    u.say("You can type q at any prompt to leave. Press Enter to accept the suggested (default) answer.")
    u.pause()


def vocabulary(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 2 of 10: The five words you need")
    u.say("A gene therapy vector is a delivery truck. Five ideas explain almost everything in CVD:")
    u.say("  1. VECTOR   the truck: a virus with its harmful genes removed (lentivirus or AAV) or a plain plasmid.\n"
          "  2. INSERT   the cargo: the gene you want cells to make, here TP53.\n"
          "  3. PROMOTER the ignition: it decides when and how strongly the insert is switched on.\n"
          "  4. CASSETTE everything that gets packaged: promoter + insert + helpers. It sits between the ends of the virus.\n"
          "  5. CAPACITY the size of the truck bed. AAV holds about 4.7 kb, lentivirus about 8 kb. A cassette that is too "
          "big simply does not fit.")
    u.say("CVD's job is to line these up: pick a strategy, pick the insert, then build and check the cassette against the "
          "capacity of the vector.")
    u.say("Here are the strategies (the kinds of therapy) the program knows:")
    rows = ["  %-6s %s" % (k, v["name"]) for k, v in STRATEGIES.items()]
    u.say("\n".join(rows))
    u.say("In the real program you choose one with --strategy, for example --strategy rep. We will use rep, tumor suppressor "
          "replacement.")
    u.pause()


def meet_tumor(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 3 of 10: Look at the tumor (aneuploidy analysis)")
    u.say("Cancer cells often have the wrong number of whole chromosome arms. This is called ANEUPLOIDY. CVD reads a "
          "'copy-number segment file' (what a lab gets from sequencing or an array) and counts which arms are gained or "
          "lost. An arm counts as gained or lost when at least 80% of it changed.")
    choice = u.choose("Which tumor data do you want to practice on?",
                      ["Built-in practice tumor (made up, always available)",
                       "A real open-data tumor: TCGA-CHOL W5-AA2X-01 (bundled with CVDEZ)"],
                      default=1,
                      notes=["A synthetic file produced by CVD itself. Safe and quick.",
                             "Real public data. The result differs from the practice tumor, so the suggestions will too."])
    if choice == 1:
        c.seg_text, c.seg_name = example_cnv_text("hg38"), "practice_tumor"
    else:
        try:
            c.seg_text = pkgutil.get_data("cvdez", "data/tcga_chol_W5-AA2X-01.seg").decode("utf-8")
            c.seg_name = "TCGA-W5-AA2X-01"
        except (OSError, TypeError):
            u.say("The real-data file was not found, so the practice tumor is used instead.")
            c.seg_text, c.seg_name = example_cnv_text("hg38"), "practice_tumor"
    segs, vtype, notes, sample = parse_segments(c.seg_text, "auto", None)
    c.result = analyze_aneuploidy(segs, "hg38", vtype, None, True, 0.2, -0.2, sample or c.seg_name, notes)
    c.recs = recommend(c.result)
    u.say("Here is the report. Read the first lines: the aneuploidy score is the number of arms gained or lost.")
    text = aneuploidy_report(c.result, c.recs)
    u.raw(text.split("Recommended designs")[0])
    u.say("What to notice:\n\n"
          "- The score says how disturbed the genome is. Higher scores tend to go with immune evasion.\n\n"
          "- 'Immune-relevant findings' link lost or gained arms to genes that matter for immunity (for example B2M on 15q).\n\n"
          "- Log2 input cannot show whole-genome doubling. The report tells you when something cannot be called.")
    u.tip("On your own data run: python -m cvd --cnv yourfile.seg --build hg38")
    c.files += write_aneuploidy_files(c.result, c.recs, c.out, c.seg_name)
    u.pause()


def choose_goal(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 4 of 10: Turn findings into a plan")
    u.say("From the arm calls, CVD proposes designs. The rules follow known gene locations (for example, if 17p is lost, "
          "TP53 is probably missing a copy). They are suggestions, not predictions: confirm with mutation and "
          "expression data before committing to anything.")
    titles = ["%s  [%s]" % (r.title, r.gene) for r in c.recs]
    notes = [r.reason for r in c.recs]
    if not titles:
        u.say("This tumor produced no automatic suggestions, so we will use the teaching example: replacing TP53.")
        c.rec = None
        c.cfg = Config(strategy="rep", gene="TP53", name="CVDEZ_example_TP53")
    else:
        default = next((i for i, r in enumerate(c.recs, 1) if r.gene == "TP53" and r.strategy == "rep"), 1)
        if not any(r.gene == "TP53" and r.strategy == "rep" for r in c.recs):
            u.say("Note: this tumor does not show a 17p loss, so 'Replace TP53' is not on the list. You can still follow "
                  "the tutorial with whichever suggestion you pick; the steps are the same.")
        pick = u.choose("These are the suggestions for this tumor. For the main example we use 'Replace TP53'. Pick one:",
                        titles, default=default, notes=notes)
        c.rec = c.recs[pick - 1]
        c.cfg = config_from_recommendation(Config(), c.rec, basis_text(c.result, c.rec))
    c.cfg.name = "CVDEZ_example_%s" % (c.rec.gene if c.rec else "TP53")
    u.say("The plan is now: strategy = %s, gene = %s." % (STRATEGIES[c.cfg.strategy]["name"], c.cfg.gene))
    u.say("Reading the plan: STRATEGY is what kind of therapy this is. GENE is the cargo. The program also picked a "
          "default promoter (%s) for this strategy, which you can change later." % (c.cfg.promoter or STRATEGIES[c.cfg.strategy]["promoter"]))
    u.tip("The same plan on the command line: python -m cvd --strategy %s --gene \"%s\" --rank" % (c.cfg.strategy, c.cfg.gene))
    u.pause()


def insert_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 5 of 10: The insert (your gene's sequence)")
    info = GENES.get(c.cfg.gene)
    if info:
        u.say("For %s the program knows a typical coding length of %s bp. %s" % (c.cfg.gene, format(info[0], ","), info[1]))
    u.say("You can paste the real coding sequence (--seq FILE or --seq ACGT...). If you do not, CVD uses a placeholder of "
          "typical length written as N, so size and layout checks still work. Nothing is guessed about the sequence itself.")
    u.say("When you DO paste a sequence, CVD checks it. To see how, here is a tiny made-up sequence (NOT a real gene) with "
          "problems built in: an AATAAA polyadenylation-like signal in the middle and a stop codon at the end:")
    u.raw(TOY_ORF)
    toy = Config(strategy="rep", gene="Toy", sequence=TOY_ORF, name="toy")
    d = build_design(toy)
    u.say("CVD reports:")
    u.raw("\n".join("[%s] %s" % m for m in d.messages))
    u.say("Warnings like these help you catch a signal that could cut or splice the message in the middle, or a premature "
          "stop that would shorten the protein. For TP53 in this tutorial we use the placeholder.")
    u.pause()


def vector_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 6 of 10: Pick the delivery setting")
    u.say("The delivery SETTING changes which vector is sensible:\n\n"
          "- IN VIVO means the vector is injected into the patient. AAV is the usual choice: it reaches many cell types and "
          "mostly does not integrate into the genome.\n\n"
          "- EX VIVO means cells are taken out, modified in a lab, then returned. Lentivirus is the usual choice because it "
          "integrates and lasts as cells divide.\n\n"
          "- NOT SPECIFIED leaves the two on equal footing.")
    pick = u.choose("Which setting do you want for the example?", ["In vivo", "Ex vivo", "Not specified"], default=1)
    c.setting = ["in vivo", "ex vivo", ""][pick - 1]
    u.say("Chosen: %s." % (c.setting or "not specified"))
    u.pause()


def ranking_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 7 of 10: Ranked vector options and why")
    u.say("Now CVD builds a complete design for several options (AAV and lentivirus; a strong promoter, a compact one, a "
          "tumor-selective one) and scores each out of 100 on five criteria: packaging capacity (30), therapeutic "
          "setting (25), expression pattern (20), insert vs vector genome (15) and vector safety (10). An option that "
          "does not fit scores 0 and is ranked last.")
    c.ranking = rank_vector_options(c.cfg, c.setting, optimize=True)
    u.raw(ranking_summary(c.ranking) + "\n\n" + options_table(c.ranking))
    n = len(c.ranking.options)
    pick = u.choose("Which option do you want to study and build? Option 1 is the top-ranked one.",
                    ["%s (score %d)" % (o.title, o.applicability) for o in c.ranking.options][:n], default=1)
    c.option = c.ranking.options[pick - 1]
    u.say("Here is the program's explanation of why that option was suggested and how it compares with the others. "
          "Every sentence is generated from the actual score differences.")
    u.raw(explain_option(c.ranking, pick - 1, with_modifications=False))
    u.tip("On the command line: --rank --explain %d   (or --explain all)" % pick)
    c.files.append(write_options_report(c.ranking, c.out, "%s_%s" % (c.cfg.gene, c.cfg.strategy)))
    u.pause()


def modifications_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 8 of 10: Modifications that make the option work better")
    u.say("Each prebuilt option can be improved. CVD tries changes, rebuilds the vector for each one and measures the "
          "result. Changes that were applied are listed with the reason; changes that were considered but NOT applied are "
          "listed too, so you can see the trade-offs.")
    applied = c.option.applied_mods
    skipped = [m for m in c.option.mods if not m.applied]
    lines = []
    for m in applied:
        lines.append("APPLIED   %s\n          %s\n          Why: %s" % (m.title, m.change, m.reason))
    for m in skipped:
        lines.append("NOT DONE  %s\n          Why: %s" % (m.title, m.reason))
    if not lines:
        lines.append("No modifications were needed for this option.")
    u.raw("\n\n".join(lines))
    u.say("Typical examples: swapping the antibiotic gene to kanamycin for clinical-grade plasmids, using a shorter WPRE "
          "when an AAV cassette is nearly full, or turning a marker off for an injected therapeutic.")
    u.tip("Modifications are on by default. Use --no-optimize to see the unmodified version.")
    u.pause()


def build_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 9 of 10: Build the vector and read the map")
    c.cfg = config_for_option(c.cfg, c.ranking, c.option)
    c.design = build_design(c.cfg)
    d = c.design
    u.say("The design is built. Here is every part in order, with its position and size:")
    rows = ["%-8s %6d..%-6d %6d bp  %s" % (f.id, f.start, f.end, f.length, f.name) for f in d.features]
    u.raw("%s | %s | %s bp\n%s\n%s" % (d.name, d.vector, format(d.total, ","), "-" * 60, "\n".join(rows)))
    u.say("What each part does:")
    seen = set()
    expl = []
    for f in d.features:
        label, text = explain_kind(f.kind)
        if f.kind in seen:
            continue
        seen.add(f.kind)
        expl.append("- %s: %s. %s" % (f.name, label, text))
    u.say("\n".join(expl))
    cassette_len = sum(f.length for f in d.features if f.in_cassette)
    u.say("Capacity check: the packaged cassette (the parts between the vector ends) is %s bp. Parts such as the bacterial "
          "origin and antibiotic gene are outside it, because they only exist to grow the plasmid in bacteria."
          % format(cassette_len, ","))
    u.say("Design checks, straight from the program (E = error, W = warning, I = information):")
    u.raw("\n".join("[%s] %s" % m for m in d.messages))
    u.pause()


def export_lesson(c: Context) -> None:
    u = c.ui
    u.heading("Lesson 10 of 10: Export and what comes next")
    paths = write_outputs(c.design, os.path.join(c.out, "design"))
    c.files += paths
    meaning = {".gb": "GenBank file: opens in SnapGene, Benchling, ApE and others. Features are annotated.",
               ".fasta": "FASTA file: the raw sequence only (N where a part is a placeholder).",
               ".svg": "Map image: open it in any browser to see the circular vector.",
               ".txt": "Plain-text summary with the parts table, checks and the reasoning behind the design."}
    u.say("The program wrote these files:")
    u.raw("\n".join("%s\n    %s" % (p, meaning.get(os.path.splitext(p)[1], "")) for p in paths))
    u.say("Congratulations: you built an example gene therapy design. To turn it into something real you would:\n\n"
          "1. Replace each N placeholder with a verified sequence (--override ID=SEQ, or paste the gene with --seq).\n\n"
          "2. Confirm the target: check that the gene is truly lost or mutated in the tumor, with mutation and expression data.\n\n"
          "3. Order or clone the plasmid, with institutional biosafety approval.\n\n"
          "4. Test in cells and animals, including normal cells, before any clinical thinking.")
    u.say("Everything you did here can be repeated in one command. For this example:")
    cmd = "python -m cvd --strategy %s --gene \"%s\" --setting \"%s\" --rank --use-option %d" % (
        c.cfg.strategy, c.cfg.gene.replace("\"", ""), c.setting or "not specified", c.option.rank)
    u.raw(cmd)
    u.say("Where to go next: run python -m cvd for the graphical window, python -m cvd --list to see every strategy, gene "
          "and part, and the CVD repository's README and EXAMPLES.md for more worked examples.")
    u.say("Output folder: %s" % os.path.abspath(c.out))


LESSONS: List[Tuple[str, Callable[[Context], None]]] = [
    ("Welcome", welcome),
    ("The five words you need", vocabulary),
    ("Look at the tumor (aneuploidy)", meet_tumor),
    ("Turn findings into a plan", choose_goal),
    ("The insert", insert_lesson),
    ("Pick the delivery setting", vector_lesson),
    ("Ranked vector options and why", ranking_lesson),
    ("Modifications", modifications_lesson),
    ("Build the vector and read the map", build_lesson),
    ("Export and what comes next", export_lesson),
]
