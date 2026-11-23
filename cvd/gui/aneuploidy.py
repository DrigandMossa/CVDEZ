"""Aneuploidy window: load segments, review arm calls, push a suggestion to the designer."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from ..cnv.advice import basis_text, recommend
from ..cnv.analysis import analyze_aneuploidy, aneuploidy_level
from ..cnv.report import aneuploidy_report, example_cnv_text
from ..cnv.segments import parse_segments
from ..model import AneuploidyResult, Recommendation
from ..parts.genome import BUILDS, N_SCORED_ARMS
from ..parts.strategies import STRATEGIES


class AneuploidyWindow:
    """Load a copy-number segment file, review the arm calls, and send a suggestion to the designer."""

    def __init__(self, app: "VectorDesignerApp") -> None:
        self.app = app
        self.result: Optional[AneuploidyResult] = None
        self.recs: List[Recommendation] = []
        top = self.top = tk.Toplevel(app.root)
        top.title("Aneuploidy analysis")
        top.geometry("1020x780")
        top.minsize(880, 620)
        defaults = dict(path="", build="hg38", vtype="auto", ploidy="", sample="", gain="0.2", loss="-0.2")
        self.v = {k: tk.StringVar(value=val) for k, val in defaults.items()}
        self.center = tk.BooleanVar(value=True)
        top.columnconfigure(0, weight=1)
        top.rowconfigure(3, weight=2)
        top.rowconfigure(5, weight=1)

        row = ttk.Frame(top, padding=(12, 10, 12, 0))
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(1, weight=1)
        ttk.Label(row, text="Copy-number segment file").grid(row=0, column=0, sticky="w")
        ttk.Entry(row, textvariable=self.v["path"]).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(row, text="Browse...", command=self.browse).grid(row=0, column=2)
        ttk.Button(row, text="Save example file...", command=self.save_example).grid(row=0, column=3, padx=(6, 0))

        opts = ttk.Frame(top, padding=(12, 8, 12, 0))
        opts.grid(row=1, column=0, sticky="ew")
        col = 0
        for label, key, width, values in (("Genome build", "build", 7, list(BUILDS)),
                                          ("Values", "vtype", 6, ["auto", "cn", "log2"]),
                                          ("Ploidy", "ploidy", 6, None), ("Sample", "sample", 12, None),
                                          ("Gain at", "gain", 6, None), ("Loss at", "loss", 6, None)):
            ttk.Label(opts, text=label).grid(row=0, column=col, padx=(0, 4))
            if values:
                widget = ttk.Combobox(opts, textvariable=self.v[key], values=values, width=width, state="readonly")
            else:
                widget = ttk.Entry(opts, textvariable=self.v[key], width=width)
            widget.grid(row=0, column=col + 1, padx=(0, 12))
            col += 2
        ttk.Checkbutton(opts, text="Centre log2 on median", variable=self.center).grid(row=0, column=col, padx=(0, 12))
        ttk.Button(opts, text="Analyze", command=self.run).grid(row=0, column=col + 1)

        self.summary = ttk.Label(top, wraplength=980, justify="left", padding=(12, 8))
        self.summary.grid(row=2, column=0, sticky="ew")

        arms = ttk.Frame(top, padding=(12, 0))
        arms.grid(row=3, column=0, sticky="nsew")
        arms.columnconfigure(0, weight=1)
        arms.rowconfigure(0, weight=1)
        self.arm_tree = ttk.Treeview(arms, columns=("cov", "mean", "gain", "loss", "call"), height=11, selectmode="browse")
        for name, text, width in (("#0", "Arm", 80), ("cov", "Covered", 80), ("mean", "Mean log2", 90),
                                  ("gain", "Gained", 80), ("loss", "Lost", 80), ("call", "Call", 110)):
            self.arm_tree.heading(name, text=text)
            self.arm_tree.column(name, width=width, anchor="w")
        self.arm_tree.tag_configure("gain", foreground="#0b5cad")
        self.arm_tree.tag_configure("loss", foreground="#b3261e")
        asb = ttk.Scrollbar(arms, orient="vertical", command=self.arm_tree.yview)
        self.arm_tree.configure(yscrollcommand=asb.set)
        self.arm_tree.grid(row=0, column=0, sticky="nsew")
        asb.grid(row=0, column=1, sticky="ns")

        ttk.Label(top, text="Suggested designs", font=self.app.bold, padding=(12, 8, 12, 2)).grid(row=4, column=0, sticky="w")
        recs = ttk.Frame(top, padding=(12, 0))
        recs.grid(row=5, column=0, sticky="nsew")
        recs.columnconfigure(0, weight=1)
        recs.rowconfigure(0, weight=1)
        self.rec_tree = ttk.Treeview(recs, columns=("kind",), height=7, selectmode="browse")
        self.rec_tree.heading("#0", text="Design")
        self.rec_tree.heading("kind", text="Strategy")
        self.rec_tree.column("#0", width=480, anchor="w")
        self.rec_tree.column("kind", width=300, anchor="w")
        self.rec_tree.bind("<<TreeviewSelect>>", self.on_select)
        rsb = ttk.Scrollbar(recs, orient="vertical", command=self.rec_tree.yview)
        self.rec_tree.configure(yscrollcommand=rsb.set)
        self.rec_tree.grid(row=0, column=0, sticky="nsew")
        rsb.grid(row=0, column=1, sticky="ns")

        self.reason = ttk.Label(top, wraplength=980, justify="left", padding=(12, 6), foreground="#587083")
        self.reason.grid(row=6, column=0, sticky="ew")
        bar = ttk.Frame(top, padding=(12, 0, 12, 10))
        bar.grid(row=7, column=0, sticky="ew")
        ttk.Button(bar, text="Use selected in vector designer", command=self.use_selected).pack(side="left")
        ttk.Button(bar, text="Save report...", command=self.save_report).pack(side="left", padx=6)
        ttk.Label(bar, foreground="#587083", text="The vector cannot sense aneuploidy. Selectivity comes from "
                  "delivery and the promoter.").pack(side="right")

    def browse(self) -> None:
        path = filedialog.askopenfilename(title="Open a copy-number segment file", filetypes=[
            ("Segment files", "*.seg *.tsv *.txt *.csv"), ("All files", "*.*")])
        if path:
            self.v["path"].set(path)

    def save_example(self) -> None:
        path = filedialog.asksaveasfilename(title="Save the synthetic example file", defaultextension=".tsv",
                                            initialfile="example_segments.tsv")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(example_cnv_text(self.v["build"].get() if self.v["build"].get() in BUILDS else "hg38"))
        except OSError as exc:
            messagebox.showerror("Could not write the file", str(exc))
            return
        self.v["path"].set(path)

    def run(self) -> None:
        path = self.v["path"].get().strip()
        if not path:
            messagebox.showinfo("Choose a file", "Choose a copy-number segment file first, or save the example file "
                                "to try the analysis.")
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            ploidy = float(self.v["ploidy"].get()) if self.v["ploidy"].get().strip() else None
            gain, loss = float(self.v["gain"].get()), float(self.v["loss"].get())
            sample = self.v["sample"].get().strip() or None
            segments, vtype, notes, sample_name = parse_segments(text, self.v["vtype"].get(), sample)
            result = analyze_aneuploidy(segments, self.v["build"].get(), vtype, ploidy, self.center.get(),
                                        gain, loss, sample_name, notes)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Could not analyze the file", str(exc))
            return
        self.result, self.recs = result, recommend(result)
        self.show()

    def show(self) -> None:
        res = self.result
        whole = "; whole chromosomes: " + ", ".join(res.whole_chromosomes) if res.whole_chromosomes else ""
        self.summary.configure(text="Aneuploidy score %d of %d (%d gains, %d losses; %s, for orientation only). "
                                    "%.0f%% of the genome is gained or lost%s. %s" % (
                                        res.score, N_SCORED_ARMS, res.gains, res.losses, aneuploidy_level(res.score),
                                        res.fga, whole, " ".join(res.notes)))
        self.arm_tree.delete(*self.arm_tree.get_children())
        for a in res.arms:
            self.arm_tree.insert("", "end", text=a.arm, tags=(a.call.replace(" ", "_"),),
                                 values=("%.0f%%" % (a.coverage * 100), "%+.2f" % a.mean_lr,
                                         "%.0f%%" % (a.frac_gain * 100), "%.0f%%" % (a.frac_loss * 100), a.call))
        self.rec_tree.delete(*self.rec_tree.get_children())
        for i, r in enumerate(self.recs):
            self.rec_tree.insert("", "end", iid=str(i), text="%d. %s: %s" % (i + 1, r.title, r.gene),
                                 values=(STRATEGIES[r.strategy]["name"],))
        self.reason.configure(text="Select a suggestion to read why it was made.")

    def on_select(self, _event=None) -> None:
        selected = self.rec_tree.selection()
        if selected:
            self.reason.configure(text=self.recs[int(selected[0])].reason)

    def use_selected(self) -> None:
        selected = self.rec_tree.selection()
        if self.result is None or not selected:
            messagebox.showinfo("Choose a suggestion", "Run the analysis and select a suggestion first.")
            return
        rec = self.recs[int(selected[0])]
        self.app.apply_recommendation(rec, basis_text(self.result, rec))
        self.top.destroy()

    def save_report(self) -> None:
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(title="Save the report", defaultextension=".txt",
                                            initialfile="aneuploidy_report.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(aneuploidy_report(self.result, self.recs))
        except OSError as exc:
            messagebox.showerror("Could not write the file", str(exc))
