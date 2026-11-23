"""Main window: options on the left; design and ranked vector options on the right."""

import dataclasses
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional, Tuple

from ..design.builder import build_design
from ..export.fasta import to_fasta
from ..export.files import write_outputs
from ..export.genbank import to_genbank
from ..model import Config, Design, Feature, Recommendation
from ..parts.elements import (BUILT_IN_IDS, COSTIM, HINGES, KINDS, LINKS, MARKERS, POLYA,
                              PROMOTERS, RESISTANCE, TAGS)
from ..parts.strategies import STRATEGIES
from ..ranking import (RankingResult, SETTING_CHOICES, VECTOR_SHORT, VectorOption, basis_for_option,
                       explain_option, explain_option_parts, fit_text, modification_parts,
                       options_report, parse_setting, rank_vector_options, ranking_summary)
from ..seqops import clean_sequence
from ..version import __version__
from .aneuploidy import AneuploidyWindow


def element_note(f: Feature, has_insert: bool, has_target: bool) -> str:
    """Short description of where an element's sequence comes from."""
    if f.custom:
        return "your sequence"
    if f.id == "goi":
        return "your sequence" if has_insert else "placeholder (N)"
    if f.id == "guide":
        return "your sequence" if has_target else "placeholder (N)"
    if f.id in BUILT_IN_IDS:
        return "built in"
    return "placeholder (N), double-click to paste"


def draw_ring(canvas, d: Design, cx: float, cy: float, radius: float, band: float, tags: Tuple[str, ...] = ()):
    """Draw a circular map of a design and return [(feature, canvas item)]. Used for the big map and thumbnails."""
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    canvas.create_oval(*box, outline="#d3dde5", width=band + 4, tags=tags)
    items = []
    for f in d.features:
        start = 360.0 * (f.start - 1) / d.total
        extent = max(360.0 * f.length / d.total, 1.5)
        item = canvas.create_arc(*box, start=90 - start, extent=-extent, style="arc", outline=KINDS[f.kind][0],
                                 width=band, tags=tags)
        items.append((f, item))
    return items


class VectorDesignerApp:
    """Main window: options on the left; live map, element table and checks on the right."""

    MAP_SIZE = 360
    LEVELS = {"error": ("Error", "#b3261e"),
              "warn": ("Warning", "#a55a00"),
              "info": ("Note", "#587083")}
    BIOSAFETY = ("Research design tool. Producing virus requires institutional biosafety approval, and clinical "
                 "gene therapy products need GMP manufacturing, preclinical safety data and regulatory authorization.")

    def __init__(self, root) -> None:
        self.root = root
        root.title("Cancer Gene Therapy Vector Designer")
        root.geometry("1220x780")
        root.minsize(1000, 640)
        if sys.platform.startswith("linux"):
            try:
                ttk.Style().theme_use("clam")
            except tk.TclError:
                pass
        self.bold = tkfont.nametofont("TkDefaultFont").copy()
        self.bold.configure(weight="bold")
        self.mono = tkfont.nametofont("TkFixedFont")
        self.overrides: Dict[str, str] = {}
        self.design: Optional[Design] = None
        self.pending = None
        self.arcs: Dict[str, int] = {}
        self.swatches: Dict[str, object] = {}
        self.summary_line = ""
        self.has_insert = False
        self.has_target = False
        self.basis = ""
        self.option_basis = ""
        self.ranking: Optional[RankingResult] = None
        self.status = tk.StringVar(value="")
        self._make_vars()
        self._make_menu()
        self._make_left()
        self._make_right()
        ttk.Label(root, textvariable=self.status, anchor="w", padding=(12, 4)).grid(
            row=1, column=0, columnspan=2, sticky="ew")
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        self.on_strategy()

    # ---- state ---------------------------------------------------------
    def _make_vars(self) -> None:
        first = STRATEGIES["rep"]
        names = dict(vector="lenti", strategy=first["name"], gene="", variant="", promoter=first["promoter"],
                     tag="none", marker=first["marker"], link="P2A", polya="SV40", resistance="AmpR",
                     hinge="CD8a hinge/TM", costim="4-1BB", guide_type="shRNA", target="", name="",
                     setting=SETTING_CHOICES[0])
        self.var = {k: tk.StringVar(value=v) for k, v in names.items()}
        self.wpre = tk.BooleanVar(value=True)
        self.wpre_short = tk.BooleanVar(value=False)
        self.optimize = tk.BooleanVar(value=True)
        self.kozak = tk.BooleanVar(value=True)
        for var in list(self.var.values()) + [self.wpre, self.wpre_short, self.optimize, self.kozak]:
            var.trace_add("write", self.schedule)

    def strategy_key(self) -> str:
        by_name = {S["name"]: k for k, S in STRATEGIES.items()}
        return by_name.get(self.var["strategy"].get(), "rep")

    def make_config(self) -> Config:
        v = self.var
        return Config(vector=v["vector"].get(), strategy=self.strategy_key(), gene=v["gene"].get(),
                      variant=v["variant"].get(), sequence=self.insert_box.get("1.0", "end"),
                      promoter=v["promoter"].get(), marker=v["marker"].get(), link=v["link"].get(),
                      tag=v["tag"].get(), polya=v["polya"].get(), resistance=v["resistance"].get(),
                      wpre=self.wpre.get(), wpre_short=self.wpre_short.get(), kozak=self.kozak.get(), hinge=v["hinge"].get(),
                      costim=v["costim"].get(), guide_type=v["guide_type"].get(),
                      target=v["target"].get(), name=v["name"].get(), overrides={},
                      basis="\n".join(x for x in (self.basis, self.option_basis) if x))

    # ---- widgets -------------------------------------------------------
    def _make_menu(self) -> None:
        bar = tk.Menu(self.root)
        file_menu = tk.Menu(bar, tearoff=0)
        file_menu.add_command(label="Export all files...", command=self.export)
        file_menu.add_command(label="Copy GenBank", command=lambda: self.copy_text("genbank"))
        file_menu.add_command(label="Copy FASTA", command=lambda: self.copy_text("fasta"))
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.destroy)
        bar.add_cascade(label="File", menu=file_menu)
        analysis_menu = tk.Menu(bar, tearoff=0)
        analysis_menu.add_command(label="Aneuploidy analysis...", command=self.open_aneuploidy)
        bar.add_cascade(label="Analysis", menu=analysis_menu)
        help_menu = tk.Menu(bar, tearoff=0)
        help_menu.add_command(label="About", command=self.about)
        bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=bar)

    def _wheel(self, canvas, area) -> None:
        """Mouse-wheel scrolling for the option panel while the pointer is over it."""
        def scroll(event):
            if isinstance(event.widget, tk.Text):
                return
            if getattr(event, "num", 0) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", 0) == 5:
                canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

        def enter(_event):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                canvas.bind_all(seq, scroll)

        def leave(_event):
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                canvas.unbind_all(seq)

        area.bind("<Enter>", enter)
        area.bind("<Leave>", leave)

    def _section(self, parent, row: int, title: str):
        box = ttk.LabelFrame(parent, text=title, padding=(8, 4))
        box.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=1)
        return box

    def _field(self, parent, row: int, col: int, text: str, var, values=None, readonly: bool = True, span: int = 1):
        """A label above a drop-down (or a text entry when values is None)."""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=col, columnspan=span, sticky="ew", padx=3, pady=2)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=text).grid(row=0, column=0, sticky="w")
        if values is None:
            widget = ttk.Entry(frame, textvariable=var)
        else:
            widget = ttk.Combobox(frame, textvariable=var, values=list(values),
                                  state="readonly" if readonly else "normal")
        widget.grid(row=1, column=0, sticky="ew")
        return frame, widget

    def _make_left(self) -> None:
        outer = ttk.Frame(self.root)
        outer.grid(row=0, column=0, sticky="ns")
        canvas = tk.Canvas(outer, width=410, highlightthickness=0)
        bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        form = ttk.Frame(canvas, padding=(12, 10))
        window = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
        self._wheel(canvas, outer)
        form.columnconfigure(0, weight=1)

        box = self._section(form, 0, "Vector type")
        for i, (value, label) in enumerate((("lenti", "Lentivirus"), ("aav", "AAV"), ("plasmid", "Plasmid"))):
            ttk.Radiobutton(box, text=label, value=value, variable=self.var["vector"],
                            command=self.on_vector).grid(row=0, column=i, padx=4, sticky="w")
            box.columnconfigure(i, weight=1)

        box = self._section(form, 1, "Therapeutic strategy")
        _, combo = self._field(box, 0, 0, "Strategy", self.var["strategy"], [s["name"] for s in STRATEGIES.values()], span=2)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.on_strategy_chosen())
        self.tip = ttk.Label(box, wraplength=360, foreground="#587083", justify="left")
        self.tip.grid(row=1, column=0, columnspan=2, sticky="w", padx=3, pady=(0, 4))
        _, self.gene_box = self._field(box, 2, 0, "Gene (choose or type a name)", self.var["gene"], [], readonly=False)
        self._field(box, 2, 1, "Variant label (optional)", self.var["variant"])

        self.insert_frame = self._section(form, 2, "Insert sequence")
        self.insert_label = ttk.Label(self.insert_frame, wraplength=360, justify="left")
        self.insert_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=3)
        self.insert_box = tk.Text(self.insert_frame, height=7, width=44, wrap="char", undo=True, font=self.mono)
        self.insert_box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=3, pady=3)
        for seq in ("<KeyRelease>", "<<Paste>>", "<<Cut>>"):
            self.insert_box.bind(seq, self.schedule)
        ttk.Button(self.insert_frame, text="Load file...", command=self.load_insert).grid(row=2, column=0, sticky="w", padx=3)
        ttk.Button(self.insert_frame, text="Clear", command=self.clear_insert).grid(row=2, column=1, sticky="e", padx=3)

        self.guide_frame = self._section(form, 3, "Guide RNA")
        for i, label in enumerate(("shRNA", "sgRNA")):
            ttk.Radiobutton(self.guide_frame, text=label, value=label,
                            variable=self.var["guide_type"]).grid(row=0, column=i, padx=4, sticky="w")
        ttk.Label(self.guide_frame, wraplength=360, justify="left",
                  text="Target: shRNA sense strand (19 to 25 nt) or sgRNA protospacer (20 nt, no PAM)."
                  ).grid(row=1, column=0, columnspan=2, sticky="w", padx=3)
        self.target_entry = ttk.Entry(self.guide_frame, textvariable=self.var["target"], font=self.mono)
        self.target_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=3, pady=3)

        self.car_frame = self._section(form, 4, "CAR domains")
        self._field(self.car_frame, 0, 0, "Hinge / transmembrane", self.var["hinge"], list(HINGES))
        self._field(self.car_frame, 0, 1, "Costimulatory domain", self.var["costim"], list(COSTIM))

        box = self._section(form, 5, "Expression")
        self.prom_row, _ = self._field(box, 0, 0, "Promoter", self.var["promoter"], list(PROMOTERS))
        self.tag_row, _ = self._field(box, 0, 1, "C-terminal tag", self.var["tag"], list(TAGS))
        self._field(box, 1, 0, "Reporter / selection", self.var["marker"], list(MARKERS))
        self.link_row, _ = self._field(box, 1, 1, "Linked by", self.var["link"], list(LINKS))
        self._field(box, 2, 0, "Polyadenylation", self.var["polya"], list(POLYA))
        self._field(box, 2, 1, "Bacterial selection", self.var["resistance"], list(RESISTANCE))
        ttk.Checkbutton(box, text="Include WPRE", variable=self.wpre).grid(row=3, column=0, sticky="w", padx=3, pady=2)
        self.kozak_check = ttk.Checkbutton(box, text="Add Kozak (GCCACC)", variable=self.kozak)
        self.kozak_check.grid(row=3, column=1, sticky="w", padx=3, pady=2)
        ttk.Checkbutton(box, text="Short WPRE (247 bp, for AAV)", variable=self.wpre_short
                        ).grid(row=4, column=0, columnspan=2, sticky="w", padx=3, pady=2)

        box = self._section(form, 6, "Vector name")
        self._field(box, 0, 0, "Leave empty for a generated name", self.var["name"], span=2)

        ttk.Label(form, text=self.BIOSAFETY, wraplength=370, foreground="#587083", justify="left"
                  ).grid(row=7, column=0, sticky="w", pady=(0, 6))

    def _make_right(self) -> None:
        outer = ttk.Frame(self.root, padding=(0, 10, 12, 0))
        outer.grid(row=0, column=1, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        self.tabs = ttk.Notebook(outer)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        right = self.design_tab = ttk.Frame(self.tabs, padding=(0, 8, 0, 0))
        self.options_tab = ttk.Frame(self.tabs, padding=(10, 8, 10, 8))
        self.tabs.add(right, text="Design")
        self.tabs.add(self.options_tab, text="Vector options")
        right.columnconfigure(1, weight=1)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(1, weight=2)
        self.canvas = tk.Canvas(right, width=self.MAP_SIZE, height=self.MAP_SIZE, background="white",
                                highlightthickness=1, highlightbackground="#d3dde5")
        self.canvas.grid(row=0, column=0, sticky="n", padx=(0, 12))

        table = ttk.Frame(right)
        table.grid(row=0, column=1, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=("pos", "bp", "note"), height=14, selectmode="browse")
        for col, text, width, anchor in (("#0", "Element", 190, "w"), ("pos", "Position", 105, "w"),
                                         ("bp", "bp", 55, "e"), ("note", "Sequence", 210, "w")):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col == "note"))
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self.on_row_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        notes = ttk.Frame(right)
        notes.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        notes.columnconfigure(0, weight=1)
        notes.rowconfigure(0, weight=1)
        self.msg_box = tk.Text(notes, height=9, wrap="word", state="disabled", relief="flat", padx=6, pady=4)
        msb = ttk.Scrollbar(notes, orient="vertical", command=self.msg_box.yview)
        self.msg_box.configure(yscrollcommand=msb.set)
        self.msg_box.grid(row=0, column=0, sticky="nsew")
        msb.grid(row=0, column=1, sticky="ns")
        for level, (_label, color) in self.LEVELS.items():
            self.msg_box.tag_configure(level, foreground=color)
            self.msg_box.tag_configure(level + "_label", foreground=color, font=self.bold)

        buttons = ttk.Frame(right)
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Button(buttons, text="Export files...", command=self.export).pack(side="left")
        ttk.Button(buttons, text="Copy GenBank", command=lambda: self.copy_text("genbank")).pack(side="left", padx=6)
        ttk.Button(buttons, text="Copy FASTA", command=lambda: self.copy_text("fasta")).pack(side="left")
        ttk.Button(buttons, text="Aneuploidy analysis...", command=self.open_aneuploidy).pack(side="left", padx=6)
        ttk.Label(buttons, text="Double-click a table row to paste a verified sequence for that element.",
                  foreground="#587083").pack(side="right")
        self._make_options_tab(self.options_tab)

    THUMB_W, THUMB_H = 150, 132

    def _make_options_tab(self, tab) -> None:
        """Ranked, prebuilt vector options for the current insert, with the reasoning and modifications for each."""
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=2)
        tab.rowconfigure(5, weight=3)
        top = ttk.Frame(tab)
        top.grid(row=0, column=0, sticky="ew")
        ttk.Label(top, text="Delivery setting").pack(side="left")
        ttk.Combobox(top, textvariable=self.var["setting"], values=SETTING_CHOICES, state="readonly",
                     width=14).pack(side="left", padx=6)
        ttk.Checkbutton(top, text="Apply suggested modifications", variable=self.optimize).pack(side="left", padx=10)
        ttk.Label(top, foreground="#587083", text="Each option is a complete prebuilt vector.").pack(side="left")
        self.insert_info = ttk.Label(tab, wraplength=700, justify="left", padding=(0, 8, 0, 6))
        self.insert_info.grid(row=1, column=0, sticky="ew")

        strip = ttk.Frame(tab)
        strip.grid(row=2, column=0, sticky="ew")
        strip.columnconfigure(0, weight=1)
        self.gallery = tk.Canvas(strip, height=self.THUMB_H, background="white", highlightthickness=1,
                                 highlightbackground="#d3dde5")
        gsb = ttk.Scrollbar(strip, orient="horizontal", command=self.gallery.xview)
        self.gallery.configure(xscrollcommand=gsb.set)
        self.gallery.grid(row=0, column=0, sticky="ew")
        gsb.grid(row=1, column=0, sticky="ew")
        ttk.Label(tab, foreground="#587083", text="Click a small map to open the full prebuilt vector."
                  ).grid(row=3, column=0, sticky="w", pady=(2, 4))

        listing = ttk.Frame(tab)
        listing.grid(row=4, column=0, sticky="nsew")
        listing.columnconfigure(0, weight=1)
        listing.rowconfigure(0, weight=1)
        self.opt_tree = ttk.Treeview(listing, columns=("score", "size", "fit", "mods"), height=5, selectmode="browse")
        for col, text, width, anchor in (("#0", "Option (click one to see the reasoning)", 330, "w"),
                                         ("score", "Applicability", 90, "e"), ("size", "Cassette", 80, "e"),
                                         ("fit", "Capacity", 110, "w"), ("mods", "Changes", 60, "e")):
            self.opt_tree.heading(col, text=text)
            self.opt_tree.column(col, width=width, anchor=anchor, stretch=(col == "#0"))
        self.opt_tree.tag_configure("nofit", foreground="#b3261e")
        osb = ttk.Scrollbar(listing, orient="vertical", command=self.opt_tree.yview)
        self.opt_tree.configure(yscrollcommand=osb.set)
        self.opt_tree.grid(row=0, column=0, sticky="nsew")
        osb.grid(row=0, column=1, sticky="ns")
        self.opt_tree.bind("<<TreeviewSelect>>", self.on_option_select)

        self.detail = ttk.Notebook(tab)
        self.detail.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
        self.why_box = self._reason_box(self.detail, "Why this ranking")
        self.mod_box = self._reason_box(self.detail, "Modifications")
        self.mods_frame = self._last_reason_frame

        buttons = ttk.Frame(tab)
        buttons.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Open the prebuilt vector", command=self.expand_current).pack(side="left")
        ttk.Button(buttons, text="Use this option in the designer", command=self.use_option).pack(side="left", padx=6)
        ttk.Button(buttons, text="Copy explanation", command=self.copy_option).pack(side="left")
        ttk.Button(buttons, text="Save all options...", command=self.save_options).pack(side="left", padx=6)

    def _reason_box(self, notebook, title: str):
        """A read-only, scrollable, tagged Text on its own notebook tab."""
        frame = ttk.Frame(notebook, padding=(4, 4, 4, 4))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        notebook.add(frame, text=title)
        box = tk.Text(frame, height=12, wrap="word", state="disabled", relief="flat", padx=8, pady=6)
        sb = ttk.Scrollbar(frame, orient="vertical", command=box.yview)
        box.configure(yscrollcommand=sb.set)
        box.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        for tag, style in (("title", dict(font=self.bold, spacing3=4)),
                           ("head", dict(font=self.bold, spacing1=10, spacing3=2)),
                           ("good", dict(foreground="#0b6b3a", font=self.bold, spacing1=6)),
                           ("bad", dict(foreground="#b3261e")), ("mute", dict(foreground="#587083"))):
            box.tag_configure(tag, **style)
        self._last_reason_frame = frame
        return box

    @staticmethod
    def _fill_box(box, parts) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        for tag, text in parts:
            box.insert("end", text + "\n", (tag,))
        box.configure(state="disabled")
        box.yview_moveto(0)

    def update_options(self, cfg: Config) -> None:
        """Re-rank the vector options for the current insert and list them."""
        try:
            self.ranking = rank_vector_options(cfg, parse_setting(self.var["setting"].get()), self.optimize.get())
        except ValueError as exc:
            self.ranking = None
            self.opt_tree.delete(*self.opt_tree.get_children())
            self.gallery.delete("all")
            self.insert_info.configure(text="Could not rank options: %s" % exc)
            return
        res = self.ranking
        previous = self.opt_tree.selection()
        self.opt_tree.delete(*self.opt_tree.get_children())
        for o in res.options:
            self.opt_tree.insert("", "end", iid=o.key, text="%d. %s" % (o.rank, o.title),
                                 values=(o.applicability, "%s bp" % format(o.cassette, ","), fit_text(o),
                                         len(o.applied_mods)),
                                 tags=("nofit",) if not o.feasible else ())
        self.insert_info.configure(text=ranking_summary(res))
        self.draw_gallery()
        keep = previous[0] if previous and self.opt_tree.exists(previous[0]) else res.options[0].key
        self.opt_tree.selection_set(keep)
        self.opt_tree.focus(keep)
        self.show_option(keep)

    def draw_gallery(self) -> None:
        """One small map per prebuilt option; clicking a map opens the full vector."""
        g, w, h = self.gallery, self.THUMB_W, self.THUMB_H
        g.delete("all")
        for i, o in enumerate(self.ranking.options):
            cx, tag = i * w + w / 2, "cell%d" % i
            g.create_rectangle(i * w + 3, 3, (i + 1) * w - 3, h - 3, fill="white", outline="#d3dde5",
                               tags=(tag, "frame:" + o.key))
            draw_ring(g, o.design, cx, 50, 34, 9, tags=(tag,))
            g.create_text(cx, 50, text="#%d" % o.rank, font=self.bold, fill="#14202b", tags=(tag,))
            promoter = o.config.promoter or "U6"
            g.create_text(cx, 100, text="%s, %s" % (VECTOR_SHORT[o.vector], promoter), fill="#14202b", tags=(tag,))
            changes = len(o.applied_mods)
            g.create_text(cx, 116, text="%d/100, %d change%s" % (o.applicability, changes, "" if changes == 1 else "s"),
                          fill="#587083" if o.feasible else "#b3261e", tags=(tag,))
            g.tag_bind(tag, "<Button-1>", lambda _e, k=o.key: self.on_thumb_click(k))
        g.configure(scrollregion=(0, 0, len(self.ranking.options) * w, h))

    def highlight_thumb(self, key: str) -> None:
        for o in self.ranking.options:
            self.gallery.itemconfigure("frame:" + o.key, outline="#1f6fd0" if o.key == key else "#d3dde5",
                                       width=3 if o.key == key else 1)

    def on_thumb_click(self, key: str) -> None:
        if self.ranking is None or not self.opt_tree.exists(key):
            return
        self.opt_tree.selection_set(key)
        self.opt_tree.focus(key)
        self.show_option(key)
        self.expand_option(key)

    def on_option_select(self, _event=None) -> None:
        selected = self.opt_tree.selection()
        if selected:
            self.show_option(selected[0])

    def current_option(self) -> Optional[VectorOption]:
        selected = self.opt_tree.selection()
        if self.ranking is None or not selected:
            return None
        return next((o for o in self.ranking.options if o.key == selected[0]), None)

    def show_option(self, key: str) -> None:
        """Write the reasoning and the modifications for one option into their tabs."""
        res = self.ranking
        if res is None:
            return
        index = next((i for i, o in enumerate(res.options) if o.key == key), None)
        if index is None:
            return
        self._fill_box(self.why_box, explain_option_parts(res, index))
        self._fill_box(self.mod_box, modification_parts(res, index))
        count = len(res.options[index].applied_mods)
        self.detail.tab(self.mods_frame, text="Modifications (%d)" % count)
        self.highlight_thumb(key)

    def expand_current(self) -> None:
        option = self.current_option()
        if option is None:
            messagebox.showinfo("Choose an option", "Select a vector option in the list first.")
            return
        self.expand_option(option.key)

    def expand_option(self, key: str) -> None:
        """The full prebuilt vector for one option: large map, every element, and the changes made to it."""
        option = next((o for o in self.ranking.options if o.key == key), None)
        if option is None:
            return
        d = option.design
        top = tk.Toplevel(self.root)
        top.title("Prebuilt vector %d: %s" % (option.rank, d.name))
        top.transient(self.root)
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)
        size = 440
        canvas = tk.Canvas(top, width=size, height=size, background="white", highlightthickness=0)
        canvas.grid(row=0, column=0, padx=10, pady=10)
        info = ttk.Label(top, padding=(10, 0, 10, 4), wraplength=440, justify="left")
        info.grid(row=1, column=0, sticky="w")
        arcs: Dict[str, object] = {}
        for f, item in draw_ring(canvas, d, size / 2, size / 2, 170, 30):
            arcs[f.id] = item
            canvas.tag_bind(item, "<Enter>", lambda _e, f=f: info.configure(
                text="%s   %d..%d   %d bp" % (f.name, f.start, f.end, f.length)))
            canvas.tag_bind(item, "<Leave>", lambda _e: info.configure(text=self.expanded_summary(option)))
        canvas.create_line(size / 2, 14, size / 2, 32, fill="#14202b", width=2)
        canvas.create_text(size / 2, size / 2 - 16, text=d.name, width=230, justify="center", font=self.bold,
                           fill="#14202b")
        canvas.create_text(size / 2, size / 2 + 22, text="%s bp" % format(d.total, ","), fill="#587083")
        info.configure(text=self.expanded_summary(option))

        right = ttk.Frame(top, padding=(0, 10, 10, 4))
        right.grid(row=0, column=1, rowspan=2, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        tree = ttk.Treeview(right, columns=("pos", "len"), height=14, selectmode="browse")
        tree.heading("#0", text="Element")
        tree.heading("pos", text="Position")
        tree.heading("len", text="bp")
        tree.column("#0", width=200)
        tree.column("pos", width=110, anchor="e")
        tree.column("len", width=60, anchor="e")
        for f in d.features:
            tree.insert("", "end", iid=f.id, text=f.name, image=self.swatch(f.kind),
                        values=("%d..%d" % (f.start, f.end), f.length))

        def highlight(_event=None) -> None:
            for item in arcs.values():
                canvas.itemconfigure(item, width=30)
            picked = tree.selection()
            if picked and picked[0] in arcs:
                canvas.itemconfigure(arcs[picked[0]], width=46)
        tree.bind("<<TreeviewSelect>>", highlight)
        tree.grid(row=0, column=0, sticky="nsew")
        buttons = ttk.Frame(right)
        buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        def use_it() -> None:
            top.destroy()
            self.opt_tree.selection_set(option.key)
            self.use_option()
        ttk.Button(buttons, text="Use this option in the designer", command=use_it).pack(side="left")
        ttk.Button(buttons, text="Close", command=top.destroy).pack(side="right")

    @staticmethod
    def expanded_summary(option: VectorOption) -> str:
        done = option.applied_mods
        return "%s. Cassette %s bp (%s). %s" % (
            option.title, format(option.cassette, ","), fit_text(option),
            "%d modification%s applied; see the Modifications tab." % (len(done), "" if len(done) == 1 else "s")
            if done else "No modification was needed.")

    def use_option(self) -> None:
        option = self.current_option()
        if option is None:
            messagebox.showinfo("Choose an option", "Select a vector option in the list first.")
            return
        if not option.feasible and not messagebox.askyesno(
                "Option does not fit", "This option's cassette is larger than its vector can package. Use it anyway?"):
            return
        self.apply_option(option)

    def apply_option(self, option: VectorOption) -> None:
        """Set the designer to a prebuilt option, with its modifications, and show the design."""
        oc = option.config
        self.var["vector"].set(option.vector)
        self.on_vector()
        for name, value in (("promoter", oc.promoter), ("marker", oc.marker), ("link", oc.link), ("tag", oc.tag),
                            ("polya", oc.polya), ("resistance", oc.resistance)):
            if value is not None:
                self.var[name].set(value)
        if oc.wpre is not None:
            self.wpre.set(oc.wpre)
        self.wpre_short.set(oc.wpre_short)
        self.kozak.set(oc.kozak)
        self.option_basis = basis_for_option(self.ranking, option)
        self.schedule()
        self.set_status("Designer set to option %d: %s (%d modification%s)." % (
            option.rank, option.title, len(option.applied_mods), "" if len(option.applied_mods) == 1 else "s"))
        self.tabs.select(self.design_tab)

    def copy_option(self) -> None:
        option = self.current_option()
        if option is None:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(explain_option(self.ranking, self.ranking.options.index(option)))
        self.set_status("Copied the explanation and modifications for option %d to the clipboard." % option.rank)

    def save_options(self) -> None:
        if self.ranking is None:
            return
        path = filedialog.asksaveasfilename(title="Save all vector options", defaultextension=".txt",
                                            initialfile="vector_options.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(options_report(self.ranking))
        except OSError as exc:
            messagebox.showerror("Could not write the file", str(exc))
            return
        self.set_status("Saved the options report to %s" % path)

    def on_vector(self) -> None:
        self.option_basis = ""            # a manual change means the ranked option no longer describes the design
        vec = self.var["vector"].get()
        self.wpre.set(vec != "plasmid")
        self.var["polya"].set("bGH" if vec == "plasmid" else "SV40")

    def on_strategy(self) -> None:
        S = STRATEGIES[self.strategy_key()]
        self.gene_box["values"] = list(S["genes"])
        self.var["gene"].set(S["genes"][0])
        self.var["promoter"].set(S["promoter"])
        self.var["marker"].set(S["marker"])
        self.tip.configure(text=S["tip"])
        self.schedule()

    def schedule(self, *_args) -> None:
        """Re-draw shortly after the last change, so typing and pasting stay responsive."""
        if self.pending is not None:
            self.root.after_cancel(self.pending)
        self.pending = self.root.after(200, self.refresh)

    @staticmethod
    def _show(widget, visible: bool) -> None:
        widget.grid() if visible else widget.grid_remove()

    def update_layout(self) -> None:
        key = self.strategy_key()
        guide, car = key == "guide", key == "car"
        self._show(self.insert_frame, not guide)
        self._show(self.guide_frame, guide)
        self._show(self.car_frame, car)
        self._show(self.prom_row, not guide)
        self._show(self.tag_row, not guide and not car)
        self._show(self.link_row, not guide and self.var["marker"].get() != "none")
        self._show(self.kozak_check, not guide)
        self.insert_label.configure(
            text="scFv sequence (VH-linker-VL, no ATG or stop). Paste DNA or FASTA." if car
            else "ORF sequence (starts with ATG, no stop codon). Paste DNA or FASTA from NCBI or CCDS. "
                 "Leave empty to use a typical-length placeholder.")

    def refresh(self) -> None:
        self.pending = None
        self.update_layout()
        cfg = self.make_config()
        try:
            base = build_design(dataclasses.replace(cfg, overrides={}))
            ids = {f.id for f in base.features} - BUILT_IN_IDS
            cfg.overrides = {k: v for k, v in self.overrides.items() if k in ids}
            self.design = build_design(cfg)
        except ValueError as exc:
            self.set_status("Error: %s" % exc)
            return
        d = self.design
        self.summary_line = "%s  |  %s bp  |  %d elements" % (d.name, format(d.total, ","), len(d.features))
        self.has_insert = bool(clean_sequence(cfg.sequence)[0])
        self.has_target = bool(clean_sequence(cfg.target)[0])
        self.set_status(self.summary_line)
        self.draw_map()
        self.fill_tree()
        self.fill_messages()
        self.update_options(cfg)

    def set_status(self, text: str) -> None:
        self.status.set(text)

    def draw_map(self) -> None:
        c, d, size = self.canvas, self.design, self.MAP_SIZE
        c.delete("all")
        self.arcs = {}
        for f, item in draw_ring(c, d, size / 2, size / 2, 140, 26):
            self.arcs[f.id] = item
            c.tag_bind(item, "<Enter>", lambda _e, f=f: self.set_status(
                "%s   %d..%d   %d bp" % (f.name, f.start, f.end, f.length)))
            c.tag_bind(item, "<Leave>", lambda _e: self.set_status(self.summary_line))
        c.create_line(size / 2, 14, size / 2, 30, fill="#14202b", width=2)
        name = d.name if len(d.name) <= 40 else d.name[:39] + "..."
        c.create_text(size / 2, size / 2 - 10, text=name, width=200, justify="center", font=self.bold, fill="#14202b")
        c.create_text(size / 2, size / 2 + 28, text="%s bp" % format(d.total, ","), fill="#587083")

    def swatch(self, kind: str):
        if kind not in self.swatches:
            img = tk.PhotoImage(width=12, height=12)
            img.put(KINDS[kind][0], to=(0, 0, 12, 12))
            self.swatches[kind] = img
        return self.swatches[kind]

    def fill_tree(self) -> None:
        previous = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for f in self.design.features:
            self.tree.insert("", "end", iid=f.id, text=f.name, image=self.swatch(f.kind),
                             values=("%d..%d" % (f.start, f.end), f.length,
                                     element_note(f, self.has_insert, self.has_target)))
        if previous and self.tree.exists(previous[0]):
            self.tree.selection_set(previous[0])

    def fill_messages(self) -> None:
        box = self.msg_box
        box.configure(state="normal")
        box.delete("1.0", "end")
        for level, text in self.design.messages:
            box.insert("end", self.LEVELS[level][0] + ": ", (level + "_label",))
            box.insert("end", text + "\n", (level,))
        box.configure(state="disabled")

    def on_select(self, _event=None) -> None:
        for item in self.arcs.values():
            self.canvas.itemconfigure(item, width=26)
        selected = self.tree.selection()
        if selected and selected[0] in self.arcs:
            self.canvas.itemconfigure(self.arcs[selected[0]], width=40)

    def on_row_double_click(self, event) -> None:
        fid = self.tree.identify_row(event.y)
        if not fid:
            return
        if fid in ("goi", "guide"):
            (self.target_entry if fid == "guide" else self.insert_box).focus_set()
            self.set_status("Paste the sequence for this element in the box on the left.")
        elif fid in BUILT_IN_IDS:
            self.set_status("This element has a built-in sequence.")
        else:
            self.edit_element(fid)

    # ---- actions -------------------------------------------------------
    def edit_element(self, fid: str) -> None:
        feature = next(f for f in self.design.features if f.id == fid)
        top = tk.Toplevel(self.root)
        top.title("Sequence for " + feature.name)
        top.transient(self.root)
        top.grab_set()
        ttk.Label(top, wraplength=440, justify="left", padding=8,
                  text="Paste a verified sequence for %s (plain DNA or FASTA). Leave it empty to go back to "
                       "the N placeholder." % feature.name).pack(anchor="w")
        box = tk.Text(top, width=64, height=10, wrap="char", font=self.mono)
        box.pack(padx=8, fill="both", expand=True)
        box.insert("1.0", self.overrides.get(fid, ""))
        box.focus_set()

        def load():
            path = filedialog.askopenfilename(title="Open a sequence file", filetypes=[
                ("Sequence files", "*.fasta *.fa *.txt"), ("All files", "*.*")])
            if path:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    box.delete("1.0", "end")
                    box.insert("1.0", fh.read())

        def accept():
            seq, _bad = clean_sequence(box.get("1.0", "end"))
            if seq:
                self.overrides[fid] = seq
            else:
                self.overrides.pop(fid, None)
            top.destroy()
            self.schedule()

        row = ttk.Frame(top, padding=8)
        row.pack(fill="x")
        ttk.Button(row, text="Load file...", command=load).pack(side="left")
        ttk.Button(row, text="Cancel", command=top.destroy).pack(side="right")
        ttk.Button(row, text="Use sequence", command=accept).pack(side="right", padx=6)

    def load_insert(self) -> None:
        path = filedialog.askopenfilename(title="Open a sequence file", filetypes=[
            ("Sequence files", "*.fasta *.fa *.txt *.gb"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            messagebox.showerror("Could not open file", str(exc))
            return
        self.insert_box.delete("1.0", "end")
        self.insert_box.insert("1.0", text)
        self.schedule()

    def clear_insert(self) -> None:
        self.insert_box.delete("1.0", "end")
        self.schedule()

    def export(self) -> None:
        if self.design is None:
            return
        folder = filedialog.askdirectory(title="Choose a folder for the exported files")
        if not folder:
            return
        try:
            paths = write_outputs(self.design, folder)
        except OSError as exc:
            messagebox.showerror("Could not write files", str(exc))
            return
        messagebox.showinfo("Files written", "\n".join(paths))
        self.set_status("Exported %d files to %s" % (len(paths), folder))

    def copy_text(self, kind: str) -> None:
        if self.design is None:
            return
        text = to_genbank(self.design) if kind == "genbank" else to_fasta(self.design)
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("Copied %s to the clipboard." % ("GenBank" if kind == "genbank" else "FASTA"))

    def on_strategy_chosen(self) -> None:
        """The user picked a strategy by hand, so any earlier aneuploidy-based reason no longer applies."""
        self.basis = ""
        self.option_basis = ""
        self.on_strategy()

    def open_aneuploidy(self) -> None:
        AneuploidyWindow(self)

    def apply_recommendation(self, rec: Recommendation, basis: str) -> None:
        """Set the designer to a suggestion from the aneuploidy analysis."""
        self.var["strategy"].set(STRATEGIES[rec.strategy]["name"])
        self.on_strategy()
        self.var["gene"].set(rec.gene)
        if rec.promoter:
            self.var["promoter"].set(rec.promoter)
        self.basis = basis
        self.option_basis = ""
        self.schedule()
        self.set_status("Designer set from the aneuploidy analysis: %s (%s)." % (rec.title, rec.gene))
        self.root.lift()

    def about(self) -> None:
        messagebox.showinfo("About", "Cancer Gene Therapy Vector Designer %s\n\n%s\n\nLibrary lengths are typical "
                            "values. Elements shown as N need verified sequences before cloning."
                            % (__version__, self.BIOSAFETY))
