"""The lesson content: every step of the guided tour and of the hands-on build.

This module is pure data and small predicate functions.  It never imports tkinter, so the content can be
tested without a display.  A step says WHICH control to point at (target), WHAT it is, what it DOES and WHY
it is there.  Hands-on steps also carry a task and a check that becomes true when the learner has done it.

Text fields may be plain strings or functions of the tutorial context (ctx), so a step can show live numbers
from the design the learner is building.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Union

Text = Union[str, Callable[["object"], str]]
PRACTICE_GENE = "TP53"
PRACTICE_NAME = "CVDEZ_TP53_AAV"
REP_NAME = "Tumor suppressor replacement"


@dataclass
class Step:
    key: str
    part: int                       # 1 = tour, 2 = build your own
    title: str
    target: str = ""               # which widget to outline (see coach.resolve); "" = none
    what: Text = ""
    does: Text = ""
    why: Text = ""
    task: Text = ""                # what the learner should do now (hands-on steps)
    check: Optional[Callable] = None   # ctx -> bool ; step is "done" when true
    tab: str = ""                  # "design" or "options": switch the main window to this tab first
    detail: Optional[int] = None   # select tab 0/1 of the options detail notebook
    strategy: Optional[str] = REP_NAME   # strategy to show for this step (tour only); None = leave alone
    setup: Optional[Callable] = None     # ctx -> None, run when the step opens
    action: Optional[Callable] = None    # ctx -> None, run by the optional action button
    action_label: str = ""


def txt(value: Text, ctx) -> str:
    return value(ctx) if callable(value) else value


# ----------------------------------------------------------------------------- predicates
def _app(ctx):
    return ctx.app


def chose_aav(ctx) -> bool:
    return _app(ctx).var["vector"].get() == "aav"


def opened_aneuploidy(ctx) -> bool:
    return getattr(_app(ctx), "aneu", None) is not None and _alive(_app(ctx).aneu)


def _alive(aneu) -> bool:
    try:
        return bool(aneu.top.winfo_exists())
    except Exception:
        return False


def filled_path(ctx) -> bool:
    a = getattr(_app(ctx), "aneu", None)
    return a is not None and bool(a.v["path"].get().strip())


def analyzed(ctx) -> bool:
    a = getattr(_app(ctx), "aneu", None)
    return a is not None and a.result is not None


def picked_tp53_suggestion(ctx) -> bool:
    a = getattr(_app(ctx), "aneu", None)
    if a is None:
        return False
    sel = a.rec_tree.selection()
    if not sel:
        return False
    try:
        return a.recs[int(sel[0])].gene == PRACTICE_GENE
    except (ValueError, IndexError, KeyError):
        return False


def used_suggestion(ctx) -> bool:
    app = _app(ctx)
    return app.var["gene"].get() == PRACTICE_GENE and bool(app.basis)


def on_options_tab(ctx) -> bool:
    app = _app(ctx)
    return str(app.tabs.select()) == str(app.options_tab)


def on_design_tab(ctx) -> bool:
    app = _app(ctx)
    return str(app.tabs.select()) == str(app.design_tab)


def setting_in_vivo(ctx) -> bool:
    return _app(ctx).var["setting"].get() == "In vivo"


def picked_second_option(ctx) -> bool:
    o = _app(ctx).current_option()
    return o is not None and o.rank == 2


def opened_prebuilt(ctx) -> bool:
    return bool(getattr(_app(ctx), "expanded", False))


def applied_top_option(ctx) -> bool:
    return _app(ctx).option_basis.startswith("Vector option #1 ")


def named_vector(ctx) -> bool:
    return bool(_app(ctx).var["name"].get().strip())


def exported(ctx) -> bool:
    return bool(getattr(_app(ctx), "exported", False))


# ----------------------------------------------------------------------------- setup actions
def reset_designer(ctx) -> None:
    """Return the designer to its starting state before the learner builds their own example."""
    app = ctx.app
    app.var["vector"].set("lenti")
    app.on_vector()
    app.var["strategy"].set(REP_NAME)
    app.on_strategy()
    app.var["name"].set("")
    app.var["variant"].set("")
    app.var["setting"].set("Not specified")
    app.insert_box.delete("1.0", "end")
    app.overrides.clear()
    app.basis = ""
    app.option_basis = ""
    app.optimize.set(True)
    app.schedule()


def write_practice_file(ctx) -> None:
    """Write the built-in practice tumor segment file and put its path in the analysis window."""
    from cvd.cnv.report import example_cnv_text
    import os
    os.makedirs(ctx.out, exist_ok=True)
    path = os.path.join(ctx.out, "practice_tumor_segments.tsv")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(example_cnv_text("hg38"))
    ctx.app.aneu.v["path"].set(path)
    ctx.app.set_status("Practice tumor file written to %s" % path)


# ----------------------------------------------------------------------------- live text
def design_summary(ctx) -> str:
    d = ctx.app.design
    if d is None:
        return "The design is still being built."
    cas = sum(f.length for f in d.features if f.in_cassette)
    return ("Right now the design is %s: %s bp in total, %d elements, and the packaged cassette is %s bp."
            % (d.name, format(d.total, ","), len(d.features), format(cas, ",")))


def option_summary(ctx) -> str:
    app = ctx.app
    o = app.current_option()
    if o is None or app.ranking is None:
        return ""
    return ("You selected option %d of %d: %s, applicability %d out of 100, cassette %s bp of %s bp."
            % (o.rank, len(app.ranking.options), o.title, o.applicability, format(o.cassette, ","),
               format(o.limit, ",")))


def mods_summary(ctx) -> str:
    o = ctx.app.current_option()
    if o is None:
        return ""
    done = [m.title for m in o.applied_mods]
    skipped = [m.title for m in o.mods if not m.applied]
    out = "For the option you selected, "
    out += ("these changes were applied: " + "; ".join(done) + ". ") if done else "no changes were needed. "
    if skipped:
        out += "Considered but not applied: " + "; ".join(skipped) + "."
    return out


def export_summary(ctx) -> str:
    d = ctx.app.design
    name = d.name if d is not None else "your vector"
    return ("Four files are written, all named after the vector (%s): .gb (GenBank), .fasta, .svg (the map) and "
            ".txt (a text summary with the checks and the reasoning). A good folder for this tutorial is %s."
            % (name, ctx.out))


# ----------------------------------------------------------------------------- Part 1: the tour
TOUR: List[Step] = [
    Step("welcome", 1, "Welcome to the real program", target="",
         what="You are looking at the real CVD vector designer. CVDEZ did not make a copy: it opened CVD itself and added "
              "this coach window beside it. Every control you will see is a real control, and anything you change really "
              "changes the design.",
         does="The LEFT side holds the choices you make. The RIGHT side shows the result at once: a map, a table of parts, "
              "and checks. There are two tabs on the right, Design and Vector options. The menu bar has File, Analysis and "
              "Help.",
         why="Part 1 (about 35 short steps) points at every control and explains what it is, what it does and why it is "
             "there. Part 2 then has you build an example gene therapy yourself and export it. Use Next and Back. "
             "You can drag this coach window anywhere.",
         strategy=None),
    Step("menu", 1, "The menu bar", target="",
         what="At the top of the CVD window: File, Analysis, Help.",
         does="File > Export all files writes the design to a folder, and Copy GenBank / Copy FASTA put the sequence on "
              "your clipboard. Analysis > Aneuploidy analysis opens the tumor analysis window. Help > About shows the "
              "version and the safety note.",
         why="These are shortcuts to the same actions as the buttons on the right. You will use the buttons in Part 2.",
         strategy=None),
    # ---- left panel
    Step("vector", 1, "Vector type", target="vec",
         what="Three radio buttons choose the delivery vehicle: Lentivirus, AAV or Plasmid.",
         does="Lentivirus integrates into the cell's DNA and holds about 8 kb between its LTRs; it suits cells taken out of "
              "the body and put back (ex vivo), such as CAR T-cells. AAV mostly stays outside the genome, holds only about "
              "4.7 kb between its ITRs, and suits injection into the body (in vivo). Plasmid is plain DNA for lab work, "
              "with no virus packaging.",
         why="The vector sets the size limit for everything you add and decides which extra parts are included "
             "(LTRs and packaging signals for lentivirus, ITRs for AAV). Switching it also resets WPRE and the "
             "polyadenylation signal to sensible defaults."),
    Step("strategy", 1, "Therapeutic strategy", target="strat:0",
         what="A drop-down with seven kinds of therapy: Tumor suppressor replacement, Suicide gene and prodrug, "
              "Immunostimulatory cytokine, Immune flagging of aneuploid tumor cells, CAR T-cell therapy, Oncogene "
              "knockdown or editing, and Cancer modeling.",
         does="Choosing a strategy fills in a typical gene list, promoter and marker for that kind of therapy, and "
              "changes which parts of the window appear. For example, CAR T-cell therapy shows the CAR domains box and "
              "Oncogene knockdown shows the Guide RNA box.",
         why="Different therapies need different vector designs. Starting from a strategy means you begin from a "
             "sensible layout instead of a blank page."),
    Step("tip", 1, "The strategy note", target="strat:1",
         what="The grey sentence under the strategy list.",
         does="It describes the chosen strategy and its main caution. It changes when you change the strategy.",
         why="It tells you the key idea and the main risk before you spend time on details."),
    Step("gene", 1, "Gene", target="strat:2",
         what="A box you can pick from or type into. The list holds the genes that suit the strategy, for example TP53, "
              "PTEN and RB1 for tumor suppressor replacement.",
         does="The gene names the insert, sets its typical length when you have not pasted a sequence, and shows any "
              "note about that gene (for instance, that APC is too large for AAV).",
         why="The insert is the cargo, and its size is the biggest factor in whether the vector fits. You can type any "
             "gene name, not only the ones in the list."),
    Step("variant", 1, "Variant label", target="strat:3",
         what="An optional text box.",
         does="Whatever you type, such as R175H, is added to the vector's name.",
         why="It keeps designs apart when you make a wild-type and a mutant version of the same gene. It is only a label; "
             "it does not change the sequence."),
    Step("insert", 1, "Insert sequence", target="insert:1",
         what="A large text box for the coding sequence (the ORF) of your gene, as plain DNA or FASTA.",
         does="If you paste a sequence, CVD uses its real length and checks it: reading frame, premature stop codons, "
              "polyadenylation signals, splice-donor-like motifs and restriction sites. If you leave it empty, CVD "
              "uses a placeholder of typical length written as N.",
         why="A placeholder is fine for planning size and layout. A real sequence is needed for a real design, and the "
             "checks catch mistakes that would waste weeks in the lab."),
    Step("loadfile", 1, "Load file and Clear", target="insert:2",
         what="Two buttons under the insert box.",
         does="Load file... reads a FASTA or text file into the box. Clear empties the box and goes back to the "
              "placeholder.",
         why="Long genes are easier to load from a file than to paste."),
    Step("guide", 1, "Guide RNA (knockdown strategy)", target="guide", strategy="Oncogene knockdown or editing",
         what="This box only appears for the Oncogene knockdown or editing strategy (the coach switched to it for this "
              "step). Radio buttons choose shRNA or sgRNA, and a box takes the target sequence.",
         does="An shRNA lowers the amount of a target gene's message; give the 19 to 25 letter sense strand. An sgRNA "
              "guides a CRISPR enzyme to edit the gene; give the 20 letter protospacer without the PAM.",
         why="Instead of adding a gene, this strategy switches one off, for example KRAS, MYC or an immune checkpoint "
             "such as PD-L1 (CD274). The insert box is hidden because there is no ORF to add."),
    Step("car", 1, "CAR domains (CAR strategy)", target="car", strategy="CAR T-cell therapy",
         what="This box only appears for the CAR T-cell therapy strategy (the coach switched to it). It has two "
              "drop-downs: Hinge / transmembrane and Costimulatory domain.",
         does="The hinge and transmembrane part (CD8a or CD28) positions the receptor on the T-cell surface. The "
              "costimulatory domain (4-1BB, CD28 or none) sets how the T-cell behaves once activated: 4-1BB tends to "
              "support persistence, CD28 faster activation. Your scFv goes in the insert box.",
         why="A CAR is assembled from parts, and the choice of parts changes how the engineered T-cell behaves."),
    # ---- expression
    Step("promoter", 1, "Promoter", target="expr:0",
         what="A drop-down of eleven promoters: CMV, EF1a, EFS, CAG, PGK, UbC, hSyn, SV40, MND, hTERT, Survivin.",
         does="The promoter is the switch that turns the gene on. EF1a, CAG and CMV are strong in most cells. EFS is "
              "short (212 bp), which saves room. MND is favored in T-cells. hTERT and Survivin are mostly active in "
              "cancer cells. hSyn is for neurons.",
         why="Strength, size and selectivity all trade off. A tumor-selective promoter adds a layer of selectivity, "
             "at the cost of weaker expression."),
    Step("tag", 1, "C-terminal tag", target="expr:1",
         what="A drop-down: none, FLAG3, HA, Myc, His6.",
         does="Adds a short protein label to the end of your protein so you can detect it with an antibody.",
         why="Useful in the lab to prove your protein is made. Leave it off for a therapeutic, because a tag is extra "
             "foreign sequence."),
    Step("marker", 1, "Reporter / selection", target="expr:2",
         what="A drop-down: none, EGFP, mCherry, Puro, Neo, Blast, Hygro.",
         does="EGFP and mCherry glow so you can see which cells took up the vector. Puro, Neo, Blast and Hygro make "
              "cells resistant to a drug so only transduced cells survive.",
         why="Markers help you check delivery in experiments, but they use up capacity, so they are usually "
             "dropped for an injected therapy."),
    Step("link", 1, "Linked by", target="expr:3",
         what="A drop-down: P2A, IRES, separate PGK promoter. It only appears when a marker is chosen.",
         does="Decides how the marker is joined to your gene. P2A (66 bp) makes two separate proteins from one message. "
              "IRES (580 bp) is larger and usually weaker for the second gene. A separate PGK promoter (516 bp) "
              "gives the marker its own switch.",
         why="P2A costs the least space, which is why CVD prefers it when it improves a design.",
         setup=lambda ctx: ctx.app.var["marker"].set("EGFP")),
    Step("polya", 1, "Polyadenylation", target="expr:4",
         what="A drop-down: bGH, SV40, none.",
         does="Adds the signal that ends the messenger RNA and keeps it stable. SV40 is 122 bp and bGH is 225 bp.",
         why="Without a polyadenylation signal, little protein is made. SV40 is shorter, which matters in AAV.",
         setup=lambda ctx: ctx.app.var["marker"].set("none")),
    Step("resist", 1, "Bacterial selection", target="expr:5",
         what="A drop-down: AmpR (ampicillin resistance) or KanR (kanamycin resistance).",
         does="Selects which antibiotic-resistance gene is on the plasmid backbone. It sits outside the packaged part, "
              "so it does not change capacity.",
         why="It lets only plasmid-carrying bacteria grow while you make DNA. KanR is preferred for plasmids used to "
             "make clinical vector, because regulators prefer to avoid beta-lactam resistance genes."),
    Step("wpre", 1, "Include WPRE", target="expr:6",
         what="A check box.",
         does="Adds the WPRE element (589 bp), which raises how much message is made and kept.",
         why="It boosts expression, but it is large. Turn it off when space is tight."),
    Step("kozak", 1, "Add Kozak (GCCACC)", target="expr:7",
         what="A check box.",
         does="Adds the six-letter GCCACC sequence in front of the start codon.",
         why="It helps the cell start reading the gene efficiently, for only 6 bp. It is on by default."),
    Step("shortwpre", 1, "Short WPRE", target="expr:8",
         what="A check box: Short WPRE (247 bp, for AAV).",
         does="Swaps the 589 bp WPRE for the 247 bp WPRE3, saving 342 bp.",
         why="AAV has very little room. The short version keeps most of the benefit and can make a tight cassette "
             "fit (Choi et al. 2014)."),
    Step("name", 1, "Vector name", target="name",
         what="A text box.",
         does="Sets the name used in the map, the file names and the GenBank record. Empty means a generated name such "
              "as pAAV-EF1a>TP53.",
         why="Good names make files easy to find later."),
    # ---- right panel
    Step("tabs", 1, "The two tabs on the right", target="tabs", tab="design", strategy=None,
         what="Design shows the vector you are building right now. Vector options shows ranked, ready-made alternatives.",
         does="Click a tab to switch. Both update live as you change the left side.",
         why="Design is for fine control; Vector options is for deciding between layouts."),
    Step("map", 1, "The circular map", target="map", tab="design", strategy=None,
         what="A ring diagram of the whole plasmid. Each colored arc is one element, drawn to scale.",
         does="Click a row in the table and its arc gets thicker, so you can see where that element sits.",
         why="You can spot at a glance which element takes the most room. A bigger arc means more of the packaging "
             "budget.",
         ),
    Step("table", 1, "The element table", target="tree", tab="design", strategy=None,
         what="One row per element, with its position, length in base pairs and the start of its sequence.",
         does=lambda ctx: "Double-click a row to paste a verified sequence for that element, for example a promoter you "
                          "have in the lab. Elements with N are still placeholders. " + design_summary(ctx),
         why="Placeholders let you plan the size before you have every sequence. Replacing them one by one turns the "
             "plan into a real design."),
    Step("checks", 1, "Design checks", target="msgs", tab="design", strategy=None,
         what="A list of notes, each marked Error, Warning or Note.",
         does="Errors mean something is wrong, such as a cassette too big for the vector. Warnings mean something "
              "needs your attention, such as no sequence pasted yet. Notes are information, such as the cassette size.",
         why="This is the safety net. Read it every time before you export."),
    Step("buttons", 1, "Export and copy buttons", target="dbtn:0", tab="design", strategy=None,
         what="Export files..., Copy GenBank, Copy FASTA.",
         does="Export files... asks for a folder and writes four files: GenBank (.gb), FASTA (.fasta), an SVG map and a "
              "text summary. The Copy buttons put GenBank or FASTA on the clipboard so you can paste into other "
              "software.",
         why="GenBank carries the annotations (every element is labeled), so tools such as SnapGene or Benchling show "
             "your design properly. FASTA is the bare sequence."),
    Step("aneubtn", 1, "Aneuploidy analysis button", target="dbtn:3", tab="design", strategy=None,
         what="Opens a second window for copy-number data from a tumor.",
         does="It counts which chromosome arms are gained or lost, flags immune-relevant findings, and suggests "
              "designs. You can send a suggestion straight to the designer.",
         why="It starts a design from the biology of a tumor instead of guesswork. You will use it in Part 2."),
    # ---- options tab
    Step("opt-setting", 1, "Delivery setting", target="opt:1", tab="options", strategy=None,
         what="A drop-down on the Vector options tab: Not specified, In vivo or Ex vivo.",
         does="In vivo (injected into the patient) favors AAV. Ex vivo (cells modified in a lab and returned) favors "
              "lentivirus. Not specified leaves the two level.",
         why="The same gene can need a different vector depending on how it is delivered, so the ranking needs to "
             "know."),
    Step("opt-mods", 1, "Apply suggested modifications", target="opt:2", tab="options", strategy=None,
         what="A check box, on by default.",
         does="When on, each prebuilt option is improved where the part library allows: for example moving a marker to "
              "P2A, using KanR, or the short WPRE when an AAV cassette is nearly full. Every change is listed.",
         why="Turn it off to see each option as first generated, which shows how much the changes help."),
    Step("opt-gallery", 1, "Option gallery", target="gallery", tab="options", strategy=None,
         what="A strip of small maps, one for each prebuilt option.",
         does="Click a small map to open that complete vector in a larger window.",
         why="Seeing the layouts side by side makes the size differences obvious."),
    Step("opt-list", 1, "Ranked list", target="opt:list", tab="options", strategy=None,
         what="A table of options ordered best first, with Applicability (out of 100), Cassette size, Capacity and "
              "number of Changes.",
         does="Click a row to see why it ranks where it does. Applicability adds five criteria: packaging capacity (30), "
              "therapeutic setting (25), expression pattern (20), insert vs vector genome (15) and vector safety (10). "
              "An option that does not fit scores 0.",
         why="The score is a way to compare layouts against each other using stated rules. It does not predict how well "
             "a therapy will work."),
    Step("opt-why", 1, "Why this ranking", target="opt:detail", tab="options", detail=0, strategy=None,
         what="The first tab under the list.",
         does="Explains why the selected option was generated, each criterion with its points and reason, and how it "
              "compares with every other option, for example 'Above #4: therapeutic setting +13'. Every sentence "
              "comes from the real score differences.",
         why="So you can check the reasoning instead of trusting a number."),
    Step("opt-mods-tab", 1, "Modifications tab", target="opt:detail", tab="options", detail=1, strategy=None,
         what="The second tab under the list.",
         does="Lists each change made to the option (what changed, why, and what it costs) and also the changes "
              "considered but not applied, with the reason.",
         why="You see the trade-offs. Not every change is free: a shorter WPRE saves space but costs expression."),
    Step("opt-buttons", 1, "Option buttons", target="opt:btn", tab="options", strategy=None,
         what="Open the prebuilt vector, Use this option in the designer, Copy explanation, Save all options...",
         does="Open shows the full prebuilt vector with a large map. Use this option copies its settings to the "
              "left side and shows the Design tab. Copy explanation puts the reasoning on the clipboard. Save all "
              "options writes a text report of the whole ranking.",
         why="Use this option is how a ranked suggestion becomes your working design."),
    Step("tour-done", 1, "End of the tour", target="", tab="design", strategy=None,
         what="That is every control in the main window.",
         does="Next, in Part 2, you build a real example: a replacement TP53 gene therapy for a practice tumor with a "
              "lost 17p arm. This time the coach will tell you what to click, and Next unlocks when you have done it. "
              "You can use Skip on any step if you get stuck.",
         why="Doing it once yourself is how this sticks.",
         ),
]

# ----------------------------------------------------------------------------- Part 2: build your own
BUILD: List[Step] = [
    Step("b-start", 2, "Build an example gene therapy", target="", tab="design", strategy=None, setup=reset_designer,
         what="The designer was reset to a clean start. The example: a replacement copy of the tumor suppressor TP53, "
              "for a practice tumor (made up, from CVD's built-in example) that has lost chromosome arm 17p, where "
              "TP53 lives.",
         does="You will: (1) analyze the tumor, (2) let the analysis set up the design, (3) choose the vector, "
              "(4) compare ranked options, (5) read the reasoning and modifications, (6) name it and (7) export it.",
         why="This is the same path you would follow with a real tumor file. The only made-up part is the data."),
    Step("b-open", 2, "1. Open the aneuploidy analysis", target="dbtn:3", tab="design", strategy=None,
         what="The Aneuploidy analysis button.",
         does="Opens the analysis window.",
         why="Starting from the tumor shows why a design is suggested.",
         task="Click 'Aneuploidy analysis...' (or use the Analysis menu).", check=opened_aneuploidy),
    Step("b-file", 2, "Segment file", target="an:row:1", strategy=None,
         what="The path box for a copy-number segment file, plus Browse... and Save example file... buttons. A segment "
              "file lists stretches of the genome and how many copies the tumor has of each.",
         does="Browse... picks your own file. Save example file... writes CVD's built-in made-up tumor so you can "
              "practice.",
         why="You can start from any lab's segment file, as long as it has chromosome, start, end and a value.",
         task="Press the coach button below to write the practice file and fill in its path for you "
              "(or use Save example file... then Browse... yourself).",
         action=write_practice_file, action_label="Fill in the practice file for me", check=filled_path),
    Step("b-build", 2, "Genome build", target="an:opts:1", strategy=None,
         what="A drop-down: hg38 or hg19.",
         does="Tells CVD which version of the human genome your coordinates use, so it knows where each chromosome arm "
              "begins and ends.",
         why="Coordinates from the wrong build put arms in the wrong place. Newer data is usually hg38."),
    Step("b-values", 2, "Values", target="an:opts:3", strategy=None,
         what="A drop-down: auto, cn or log2.",
         does="Says whether the numbers are copy number (cn) or log2 ratios. Auto guesses from the values.",
         why="The two scales mean different things, so CVD has to read them correctly."),
    Step("b-ploidy", 2, "Ploidy", target="an:opts:5", strategy=None,
         what="An optional number.",
         does="The normal copy number to compare against, used with copy-number data. Empty means the genome median.",
         why="A tumor that is mostly tetraploid has a baseline of 4, not 2. Telling CVD stops it calling everything a "
             "gain."),
    Step("b-sample", 2, "Sample", target="an:opts:7", strategy=None,
         what="An optional name.",
         does="Chooses one sample when a file holds several.",
         why="Many public files contain dozens of tumors. This picks yours."),
    Step("b-thresh", 2, "Gain at / Loss at", target="an:opts:9", strategy=None,
         what="Two numbers, 0.2 and -0.2 by default.",
         does="The log2 ratio at which a segment counts as a gain or a loss.",
         why="Stricter thresholds call fewer events. The defaults are a common starting point."),
    Step("b-center", 2, "Centre log2 on median", target="an:opts:12", strategy=None,
         what="A check box, on by default.",
         does="Shifts log2 ratios so their median is zero.",
         why="Many files have a small offset. Centering removes it so normal regions read as 0."),
    Step("b-analyze", 2, "2. Run the analysis", target="an:opts:13", strategy=None,
         what="The Analyze button.",
         does="Calls each chromosome arm gained or lost when at least 80% of it changed (Taylor 2018), counts them, "
              "and lists immune-relevant findings and suggested designs.",
         why="The arm-level score is a standard measure of how disturbed a tumor genome is.",
         task="Click Analyze.", check=analyzed),
    Step("b-summary", 2, "The summary and arm table", target="an:arms", strategy=None,
         what="A summary line above a table with one row per chromosome arm.",
         does="Each row shows how much of the arm is covered, its mean log2, the fraction gained or lost, and the "
              "call: gain, loss, partial, neutral, no data or not scored. Blue rows are gains and red rows are losses. Find 17p: it "
              "should be a loss.",
         why="This is the evidence behind the suggestions. Never design from a suggestion without looking at it."),
    Step("b-recs", 2, "3. Suggested designs", target="an:recs", strategy=None,
         what="A list of designs the arm calls point to.",
         does="Each is a rule linking a gained or lost arm to a gene, such as 17p loss to TP53. The grey note under "
              "the list explains the reason for the one you select.",
         why="The rules follow known gene locations and published associations. They are suggestions, not "
             "predictions: arm loss does not prove the gene is inactive.",
         task="Select 'Replace TP53' in the list.", check=picked_tp53_suggestion),
    Step("b-use", 2, "Send it to the designer", target="an:bar:0", strategy=None,
         what="The button 'Use selected in vector designer'.",
         does="Sets the strategy, gene and promoter in the main window, and records the reason so it appears in the "
              "design summary.",
         why="Now the design carries its own justification.",
         task="Click 'Use selected in vector designer'.", check=used_suggestion),
    Step("b-check-set", 2, "See what changed", target="strat", tab="design", strategy=None,
         what="Back in the main window, the strategy is now Tumor suppressor replacement and the gene is TP53.",
         does=lambda ctx: design_summary(ctx),
         why="The analysis filled these in for you. You can still change anything by hand; changing the strategy by "
             "hand clears the stored reason."),
    Step("b-vector", 2, "4. Choose the vector", target="vec", tab="design", strategy=None,
         what="The vector type choice.",
         does="TP53 is a replacement therapy delivered by injection, so AAV is the usual choice.",
         why="The 1,182 bp TP53 cassette fits comfortably in AAV's roughly 4.7 kb.",
         task="Choose AAV.", check=chose_aav),
    Step("b-map", 2, "Read your design", target="tree", tab="design", strategy=None,
         what="The map, table and checks now describe your AAV design.",
         does=lambda ctx: design_summary(ctx) + " Look for the two ITRs at the ends of the packaged part, the "
                          "promoter, the TP53 element and the polyA signal. The check box lists the capacity "
                          "message.",
         why="Everything between the ITRs is packaged into the virus. The plasmid backbone (origin and antibiotic "
             "gene) only exists to grow the DNA in bacteria."),
    Step("b-optab", 2, "5. Compare ranked options", target="tabs", tab="design", strategy=None,
         what="The Vector options tab.",
         does="CVD builds a complete vector for each reasonable layout and ranks them for your insert.",
         why="It shows the alternatives you might not have thought of.",
         task="Click the 'Vector options' tab.", check=on_options_tab),
    Step("b-setting", 2, "Tell it how it is delivered", target="opt:1", tab="options", strategy=None,
         what="The Delivery setting drop-down.",
         does="Choose In vivo: the vector is injected into the patient.",
         why="This is the criterion worth 25 points, so it changes the ranking.",
         task="Set Delivery setting to In vivo.", check=setting_in_vivo),
    Step("b-pick", 2, "Pick an option to study", target="opt:list", tab="options", strategy=None,
         what="The ranked list. The top rows should be AAV layouts, because you chose In vivo.",
         does="Each row is a complete, checked design, not just a name. To see how the reasoning reads, study the "
              "second-ranked option: it shows why it sits just below the first.",
         why="Comparing neighbours is the best way to learn what the score rewards.",
         task="Click the second option in the list (rank 2).", check=picked_second_option),
    Step("b-why", 2, "Read the reasoning", target="opt:detail", tab="options", detail=0, strategy=None,
         what="The 'Why this ranking' tab.",
         does=lambda ctx: option_summary(ctx) + " Scroll the text: it shows each criterion with points and a reason, "
                          "then how this option compares with every other one, including the option ranked "
                          "above it.",
         why="Every comparison line is built from the real score differences."),
    Step("b-mods", 2, "Read the modifications", target="opt:detail", tab="options", detail=1, strategy=None,
         what="The 'Modifications' tab.",
         does=lambda ctx: mods_summary(ctx),
         why="You decide whether each trade-off is acceptable. Changes you do not like can be undone by clearing "
             "'Apply suggested modifications'."),
    Step("b-open-pre", 2, "Open the prebuilt vector", target="opt:btn:0", tab="options", strategy=None,
         what="The 'Open the prebuilt vector' button.",
         does="Opens a window with the full vector: a large map, every element, and the changes made to it.",
         why="It lets you inspect the option before committing to it.",
         task="Click 'Open the prebuilt vector' (close the window it opens when you have looked).",
         check=opened_prebuilt),
    Step("b-apply", 2, "6. Use the option", target="opt:btn:1", tab="options", strategy=None,
         what="The 'Use this option in the designer' button.",
         does="Copies the option's vector, promoter, marker, polyA, WPRE and other settings into the left side and "
              "switches to the Design tab. The reason for the choice is stored with the design.",
         why="From here you can still adjust any control, for example paste a real TP53 sequence.",
         task="Select option 1 (the top-ranked one) in the list, then click 'Use this option in the designer'.",
         check=applied_top_option),
    Step("b-name", 2, "Name your vector", target="name", tab="design", strategy=None,
         what="The Vector name box.",
         does="Type a name. Suggestion: %s." % PRACTICE_NAME,
         why="The name is used for the files you are about to export.",
         task="Type a name in the Vector name box.", check=named_vector),
    Step("b-final", 2, "Final check", target="msgs", tab="design", strategy=None,
         what="The design checks.",
         does=lambda ctx: design_summary(ctx) + " Read the checks: the placeholder warning is expected, because "
                          "you did not paste a TP53 sequence. There should be no errors.",
         why="Never export a design with an unread error."),
    Step("b-export", 2, "7. Export", target="dbtn:0", tab="design", strategy=None,
         what="The 'Export files...' button.",
         does=lambda ctx: export_summary(ctx),
         why="These files go to a cloning service, into SnapGene or Benchling, or into your records.",
         task="Click 'Export files...' and choose a folder.", check=exported),
    Step("b-done", 2, "You built a gene therapy design", target="", tab="design", strategy=None,
         what="You went from a tumor to an exported vector design using the real program.",
         does="To make this real: replace each N placeholder with a verified sequence (double-click a row in the "
              "table, or paste the TP53 sequence in the insert box), confirm with mutation and expression data that "
              "TP53 is really lost in this tumor, and get institutional biosafety approval before making any virus.",
         why="CVD is a design and planning tool. A medicine needs manufacturing, safety data and regulatory "
             "approval. Close this coach any time; the CVD window stays open for your own work."),
]

STEPS: List[Step] = TOUR + BUILD
