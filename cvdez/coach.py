"""The coach window and the outline that points at a control in the real CVD window.

The Tk code lives here and in launch().  Everything that decides WHAT to say lives in tutorial.py and steps.py.
"""

import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional

from .tutorial import Tutorial

OUTLINE = "#e8590c"
THICK = 4


def _child(widget, index: int):
    return widget.winfo_children()[index]


def build_resolvers(app) -> Dict[str, Callable[[], object]]:
    """Map a step's target key to the widget it should outline.  Every lookup is lazy, so a missing widget
    gives None (no outline) rather than an error."""
    form = app.insert_frame.master                       # the scrolling form on the left
    right = app.msg_box.master.master                    # the Design tab's frame
    top_row = lambda: app.options_tab.grid_slaves(row=0)[0]     # noqa: E731
    btn_row = lambda: app.options_tab.grid_slaves(row=6)[0]     # noqa: E731
    expr = lambda: form.grid_slaves(row=5)[0]                   # noqa: E731
    aneu = lambda: app.aneu.top                                  # noqa: E731
    an_kids = lambda: aneu().winfo_children()                    # noqa: E731
    R: Dict[str, Callable[[], object]] = {
        "vec": lambda: form.grid_slaves(row=0)[0],
        "strat": lambda: form.grid_slaves(row=1)[0],
        "insert": lambda: app.insert_frame,
        "guide": lambda: app.guide_frame,
        "car": lambda: app.car_frame,
        "name": lambda: form.grid_slaves(row=6)[0],
        "tabs": lambda: app.tabs,
        "map": lambda: app.canvas,
        "tree": lambda: app.tree,
        "msgs": lambda: app.msg_box,
        "gallery": lambda: app.gallery,
        "opt:list": lambda: app.opt_tree,
        "opt:detail": lambda: app.detail,
        "opt:btn": btn_row,
        "an:arms": lambda: an_kids()[3],
        "an:recs": lambda: an_kids()[5],
    }
    for i in range(4):
        R["strat:%d" % i] = lambda i=i: _strat_child(form, i)
    for i in (1, 2):
        R["insert:%d" % i] = lambda i=i: _child(app.insert_frame, i)
    for i in range(9):
        R["expr:%d" % i] = lambda i=i: _child(expr(), i)
    for i in range(4):
        R["dbtn:%d" % i] = lambda i=i: _child(right.grid_slaves(row=2)[0], i)
    for i in (1, 2):
        R["opt:%d" % i] = lambda i=i: _child(top_row(), i)
    for i in range(4):
        R["opt:btn:%d" % i] = lambda i=i: _child(btn_row(), i)
    # the aneuploidy window: row 0 = file row, row 1 = options row, row 7 = button bar
    R["an:row:1"] = lambda: _child(an_kids()[0], 1)
    for i in (1, 3, 5, 7, 9, 11, 12, 13):
        R["an:opts:%d" % i] = lambda i=i: _child(an_kids()[1], i)
    R["an:bar:0"] = lambda: _child(an_kids()[7], 0)
    return R


def _strat_child(form, i: int):
    """The Therapeutic strategy box holds: strategy field, note label, gene field, variant field."""
    return form.grid_slaves(row=1)[0].winfo_children()[i]


class Outline:
    """Four thin bars drawn around a widget.  They are children of the widget's own window, so the outline also
    works inside the aneuploidy window."""

    def __init__(self):
        self.bars = []
        self.parent = None

    def _make(self, parent) -> None:
        self.clear()
        self.parent = parent
        self.bars = [tk.Frame(parent, background=OUTLINE) for _ in range(4)]

    def clear(self) -> None:
        for b in self.bars:
            try:
                b.place_forget()
                b.destroy()
            except tk.TclError:
                pass
        self.bars = []

    def show(self, widget) -> None:
        if widget is None:
            self.clear()
            return
        try:
            top = widget.winfo_toplevel()
            if not widget.winfo_viewable():
                self.clear()
                return
            if top is not self.parent or not self.bars:
                self._make(top)
            x = widget.winfo_rootx() - top.winfo_rootx() - THICK
            y = widget.winfo_rooty() - top.winfo_rooty() - THICK
            w, h = widget.winfo_width() + 2 * THICK, widget.winfo_height() + 2 * THICK
            t = THICK
            for bar, (bx, by, bw, bh) in zip(self.bars, ((x, y, w, t), (x, y + h - t, w, t),
                                                         (x, y, t, h), (x + w - t, y, t, h))):
                bar.place(x=bx, y=by, width=bw, height=bh)
                bar.lift()
        except tk.TclError:
            self.clear()


class Coach:
    """A small always-on-top window with the explanation, the task and the Back / Next buttons."""

    def __init__(self, app, tutorial: Tutorial):
        self.app, self.t = app, tutorial
        self.resolvers = build_resolvers(app)
        self.outline = Outline()
        root = app.root
        self.win = win = tk.Toplevel(root)
        win.title("CVDEZ Coach")
        win.attributes("-topmost", True)
        win.geometry(self._geometry())
        win.minsize(640, 300)
        win.protocol("WM_DELETE_WINDOW", self.close)
        win.columnconfigure(0, weight=1)
        win.rowconfigure(2, weight=1)

        self.header = ttk.Label(win, padding=(12, 8, 12, 0), foreground="#587083")
        self.header.grid(row=0, column=0, sticky="ew")
        self.title = ttk.Label(win, padding=(12, 2, 12, 4), font=app.bold, wraplength=700)
        self.title.grid(row=1, column=0, sticky="ew")
        body = ttk.Frame(win, padding=(12, 0))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.text = tk.Text(body, wrap="word", height=9, relief="flat", padx=4, pady=4, state="disabled")
        sb = ttk.Scrollbar(body, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        self.text.tag_configure("h", font=app.bold, foreground="#0b5cad", spacing1=6)
        self.text.tag_configure("task", font=app.bold, foreground=OUTLINE, spacing1=6)

        self.status = ttk.Label(win, padding=(12, 4), font=app.bold)
        self.status.grid(row=3, column=0, sticky="ew")
        bar = ttk.Frame(win, padding=(12, 0, 12, 10))
        bar.grid(row=4, column=0, sticky="ew")
        self.back_btn = ttk.Button(bar, text="< Back", command=self.back)
        self.back_btn.pack(side="left")
        self.next_btn = ttk.Button(bar, text="Next >", command=self.next)
        self.next_btn.pack(side="left", padx=6)
        self.action_btn = ttk.Button(bar, text="", command=self.action)
        self.skip_btn = ttk.Button(bar, text="Skip this step", command=self.skip)
        self.part_btn = ttk.Button(bar, text="Skip the tour: go to Part 2", command=self.go_part2)
        ttk.Button(bar, text="Close coach", command=self.close).pack(side="right")
        self._poll_id = None
        self.show()
        self.poll()

    # ---- window placement ---------------------------------------------
    def _geometry(self) -> str:
        root = self.app.root
        root.update_idletasks()
        sh = root.winfo_screenheight()
        sw = root.winfo_screenwidth()
        w, h = min(820, sw - 40), 340
        return "%dx%d+%d+%d" % (w, h, max(0, (sw - w) // 2), max(0, sh - h - 60))

    # ---- showing a step -----------------------------------------------
    def show(self) -> None:
        t = self.t
        s = t.step
        if s.tab == "design":
            self.app.tabs.select(self.app.design_tab)
        elif s.tab == "options":
            self.app.tabs.select(self.app.options_tab)
        if s.detail is not None:
            try:
                self.app.detail.select(s.detail)
            except tk.TclError:
                pass
        self.header.configure(text=t.label())
        self.title.configure(text=s.title)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for heading, body in t.sections():
            if heading == "Your turn":
                self.text.insert("end", heading + "\n", "task")
                self.text.insert("end", body + "\n", "task")
            else:
                self.text.insert("end", heading + "\n", "h")
                self.text.insert("end", body + "\n")
        self.text.configure(state="disabled")
        self.text.yview_moveto(0)
        self.back_btn.configure(state="normal" if t.can_back() else "disabled")
        for b in (self.action_btn, self.skip_btn, self.part_btn):
            b.pack_forget()
        if s.action is not None:
            self.action_btn.configure(text=s.action_label or "Do it for me")
            self.action_btn.pack(side="left", padx=6)
        if s.check is not None:
            self.skip_btn.pack(side="left", padx=6)
        if s.part == 1 and t.index > 0:
            self.part_btn.pack(side="left", padx=6)
        self.update_state()
        self.root_after(60, self.point)

    def root_after(self, ms: int, fn) -> None:
        self.app.root.after(ms, fn)

    def point(self) -> None:
        """Outline the control for this step, scrolling the left panel to it when needed."""
        key = self.t.step.target
        widget = None
        if key:
            try:
                widget = self.resolvers[key]()
            except (KeyError, IndexError, AttributeError, tk.TclError):
                widget = None
        if widget is not None:
            self.scroll_into_view(widget)
            self.root_after(60, lambda: self.outline.show(widget))
        else:
            self.outline.clear()

    def scroll_into_view(self, widget) -> None:
        """If the widget is in the scrolling form on the left, scroll that form so it is visible."""
        form = self.app.insert_frame.master
        node = widget
        try:
            while node is not None and node.master is not form:
                node = node.master
            if node is None:
                return
            canvas = form.master
            height = max(1, form.winfo_height())
            canvas.yview_moveto(max(0.0, (node.winfo_y() - 20) / height))
        except (AttributeError, tk.TclError):
            return

    def update_state(self) -> None:
        t = self.t
        done = t.done()
        if t.needs_action():
            self.status.configure(text="Done. Press Next." if done else "Waiting for you to do the step above...",
                                  foreground="#1b7a3d" if done else OUTLINE)
        else:
            self.status.configure(text="", foreground="#587083")
        last = t.index == t.total - 1
        self.next_btn.configure(text="Finish" if last else "Next >",
                                state="normal" if (done if not last else True) else "disabled")

    def poll(self) -> None:
        """Re-check the step every third of a second, so Next unlocks the moment the learner has done the task."""
        try:
            self.update_state()
            self.point_if_moved()
            self._poll_id = self.app.root.after(300, self.poll)
        except tk.TclError:
            self._poll_id = None

    def point_if_moved(self) -> None:
        # The layout settles a moment after a step opens (hidden boxes appear, tabs switch), and windows can be
        # dragged or resized, so keep the outline on the control.
        key = self.t.step.target
        if key and key in self.resolvers:
            try:
                self.outline.show(self.resolvers[key]())
            except (IndexError, AttributeError, tk.TclError):
                self.outline.clear()

    # ---- buttons ------------------------------------------------------
    def next(self) -> None:
        if self.t.index == self.t.total - 1:
            self.close()
            return
        if self.t.next():
            self.show()

    def back(self) -> None:
        if self.t.back():
            self.show()

    def skip(self) -> None:
        if self.t.skip():
            self.show()

    def action(self) -> None:
        s = self.t.step
        if s.action is not None:
            try:
                s.action(self.t)
            except (OSError, AttributeError, tk.TclError) as exc:
                self.app.set_status("Could not do that: %s" % exc)
        self.update_state()

    def go_part2(self) -> None:
        self.t.jump_to_part(2)
        self.show()

    def close(self) -> None:
        if self._poll_id is not None:
            try:
                self.app.root.after_cancel(self._poll_id)
            except tk.TclError:
                pass
            self._poll_id = None
        self.outline.clear()
        try:
            self.win.destroy()
        except tk.TclError:
            pass


def launch(out: str, start_part: int = 1) -> int:
    """Open the real CVD window with the coach beside it.  Returns 2 if no window could be opened."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Error: could not open a window (%s)." % exc, file=sys.stderr)
        return 2
    from .app import TutorialApp
    app = TutorialApp(root, out)
    tutorial = Tutorial(app, out)
    if start_part == 2:
        tutorial.jump_to_part(2)
    else:
        tutorial.enter()
    Coach(app, tutorial)
    root.mainloop()
    return 0
