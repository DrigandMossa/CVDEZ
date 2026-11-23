"""The window tutorial, driven through stand-in widgets (no display or tkinter needed).

The real CVD window (cvd.gui.app) is built on top of fakes, wrapped by the tutorial classes, and a pretend learner
does every hands-on step through the same methods the buttons call.  This checks the logic that matters (what each
step says, when Next unlocks, that the example really ends in exported files).  It cannot show how the outline
looks on screen; that needs a real display.
"""
import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Var:
    def __init__(self, value=None):
        self.value, self.callbacks = value, []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value
        for cb in self.callbacks:
            cb("n", "", "write")

    def trace_add(self, mode, callback):
        self.callbacks.append(callback)


class FakeText:
    def __init__(self, *a, **k):
        self.content, self.state, self._m = "", None, mock.MagicMock()

    def __getattr__(self, name):
        return getattr(self._m, name)

    def get(self, *a):
        return self.content

    def configure(self, **k):
        if "state" in k:
            self.state = k["state"]

    def insert(self, index, text, *tags):
        if tags:
            assert self.state == "normal", "inserting into a read-only Text"
        self.content = self.content + text if index == "end" else text

    def delete(self, *a):
        self.content = ""


class FakeTree:
    def __init__(self, *a, **k):
        self.rows, self.order, self.sel = {}, [], ()

    def __getattr__(self, name):
        return mock.MagicMock()

    def get_children(self):
        return tuple(self.order)

    def delete(self, *ids):
        self.rows, self.order, self.sel = {}, [], ()

    def insert(self, parent, where, iid=None, text="", values=(), tags=(), **kw):
        iid = iid if iid is not None else str(len(self.order))
        self.rows[iid] = (text, values, tags)
        self.order.append(iid)
        return iid

    def exists(self, iid):
        return iid in self.rows

    def selection(self):
        return self.sel

    def selection_set(self, iid):
        self.sel = (iid,)

    def focus(self, iid):
        pass


class FakeNotebook:
    def __init__(self):
        self.current = None

    def select(self, tab=None):
        if tab is not None:
            self.current = str(tab)
        return self.current


class Harness(unittest.TestCase):
    def setUp(self):
        tk = mock.MagicMock()
        tk.StringVar = tk.BooleanVar = Var
        tk.TclError = type("TclError", (Exception,), {})
        tk.Text = FakeText
        ttk = mock.MagicMock()
        ttk.Treeview.side_effect = FakeTree
        ttk.Label.side_effect = lambda *a, **k: mock.MagicMock()
        tk.ttk, tk.font = ttk, mock.MagicMock()
        modules = {"tkinter": tk, "tkinter.font": tk.font, "tkinter.ttk": ttk,
                   "tkinter.filedialog": tk.filedialog, "tkinter.messagebox": tk.messagebox}
        self.names = ("cvd.gui.app", "cvd.gui.aneuploidy", "cvdez.app", "cvdez.coach")
        for n in self.names:
            sys.modules.pop(n, None)
        patcher = mock.patch.dict(sys.modules, modules)
        patcher.start()
        self.addCleanup(self._restore, patcher)
        self.tk = tk
        self.cvd_app = importlib.import_module("cvd.gui.app")
        self.cvd_app.messagebox = mock.MagicMock()
        self.cvd_app.filedialog = mock.MagicMock()
        self.aneu_mod = importlib.import_module("cvd.gui.aneuploidy")
        self.aneu_mod.messagebox = mock.MagicMock()
        self.aneu_mod.filedialog = mock.MagicMock()
        self.tutapp = importlib.import_module("cvdez.app")
        self.coach_mod = importlib.import_module("cvdez.coach")
        self.root = mock.MagicMock()
        self.root.after.side_effect = lambda ms, fn=None: 1
        self.root.winfo_screenheight.return_value = 1080
        self.root.winfo_screenwidth.return_value = 1920
        self.out = tempfile.mkdtemp()
        self.app = self.tutapp.TutorialApp(self.root, self.out)
        self.app.tabs = FakeNotebook()
        self.app.refresh()
        from cvdez.tutorial import Tutorial
        self.t = Tutorial(self.app, self.out)

    def _restore(self, patcher):
        patcher.stop()
        for n in self.names:
            sys.modules.pop(n, None)


class Content(Harness):
    def test_keys_unique_and_both_parts_present(self):
        from cvdez.steps import STEPS
        keys = [s.key for s in STEPS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual({s.part for s in STEPS}, {1, 2})
        self.assertGreater(len([s for s in STEPS if s.part == 1]), 30)

    def test_every_target_has_a_resolver(self):
        from cvdez.steps import STEPS
        resolvers = self.coach_mod.build_resolvers(self.app)
        for s in STEPS:
            if s.target:
                self.assertIn(s.target, resolvers, "step %s points at unknown target %r" % (s.key, s.target))

    def test_every_step_has_text_that_renders(self):
        from cvdez.steps import STEPS
        for i, s in enumerate(STEPS):
            self.t.index = i
            secs = self.t.sections()
            heads = [h for h, _ in secs]
            self.assertIn("What it is", heads, s.key)
            self.assertIn("What it does", heads, s.key)
            if s.part == 1 and s.key not in ("welcome", "menu", "tour-done"):
                self.assertIn("Why it is there", heads, s.key)
            if s.check is not None:
                self.assertIn("Your turn", heads, s.key)

    def test_the_tour_names_every_left_panel_control(self):
        from cvdez.steps import TOUR
        text = " ".join(s.title.lower() for s in TOUR)
        for word in ("vector type", "strategy", "gene", "variant", "insert", "load file", "guide", "car domains",
                     "promoter", "tag", "reporter", "linked", "polyadenylation", "bacterial", "wpre", "kozak",
                     "short wpre", "vector name", "delivery setting", "modifications", "gallery", "ranked"):
            self.assertIn(word, text, "tour has no step for %r" % word)

    def test_claims_about_the_engine_match_the_engine(self):
        from cvd.parts.elements import PROMOTERS, POLYA, WPRE_SHORT_LEN
        from cvd.ranking.tables import CAPACITY
        from cvdez.steps import STEPS
        blob = " ".join(s.does if isinstance(s.does, str) else "" for s in STEPS)
        self.assertEqual(CAPACITY["aav"][0], 4700)
        self.assertEqual(CAPACITY["lenti"][0], 8000)
        self.assertEqual(PROMOTERS["EFS"], 212)
        self.assertEqual((POLYA["SV40"], POLYA["bGH"], WPRE_SHORT_LEN), (122, 225, 247))
        for fact in ("212 bp", "122 bp", "225 bp", "247 bp", "589 bp", "342 bp"):
            self.assertIn(fact, blob)


class Flow(Harness):
    def test_tour_walks_through_without_errors_and_switches_strategies_for_hidden_boxes(self):
        seen = {}
        while self.t.step.part == 1:
            seen[self.t.step.key] = self.app.var["strategy"].get()
            self.assertTrue(self.t.done(), self.t.step.key)
            self.assertTrue(self.t.next())
        self.assertEqual(seen["guide"], "Oncogene knockdown or editing")
        self.assertEqual(seen["car"], "CAR T-cell therapy")
        self.assertEqual(seen["promoter"], "Tumor suppressor replacement")

    def test_hands_on_steps_are_locked_until_done_and_skippable(self):
        self.t.jump_to_part(2)
        while self.t.step.check is None:
            self.assertTrue(self.t.next())
        self.assertFalse(self.t.done())
        self.assertFalse(self.t.next())
        key = self.t.step.key
        self.assertTrue(self.t.skip())
        self.assertIn(key, self.t.skipped)

    def test_start_of_part_two_resets_the_designer(self):
        self.app.var["gene"].set("PTEN")
        self.app.var["vector"].set("plasmid")
        self.app.var["name"].set("junk")
        self.t.jump_to_part(2)
        self.assertEqual(self.app.var["vector"].get(), "lenti")
        self.assertEqual(self.app.var["gene"].get(), "TP53")
        self.assertEqual(self.app.var["name"].get(), "")

    def test_a_learner_can_build_and_export_the_example(self):
        import glob
        t, app = self.t, self.app
        t.jump_to_part(2)
        exp = tempfile.mkdtemp()
        done_keys = []

        def learner(step):
            """Do what the step's task asks, through the same methods the buttons call."""
            k = step.key
            if k == "b-open":
                app.open_aneuploidy()
            elif k == "b-file":
                step.action(t)
            elif k == "b-analyze":
                app.aneu.run()
            elif k == "b-recs":
                idx = next(i for i, r in enumerate(app.aneu.recs) if r.gene == "TP53")
                app.aneu.rec_tree.selection_set(str(idx))
                app.aneu.on_select()
            elif k == "b-use":
                app.aneu.use_selected()
            elif k == "b-vector":
                app.var["vector"].set("aav")
                app.on_vector()
            elif k == "b-optab":
                app.tabs.select(app.options_tab)
            elif k == "b-setting":
                app.var["setting"].set("In vivo")
                app.refresh()
            elif k == "b-pick":
                app.opt_tree.selection_set(app.ranking.options[1].key)
                app.on_option_select()
            elif k == "b-open-pre":
                app.expand_current()
            elif k == "b-apply":
                app.opt_tree.selection_set(app.ranking.options[0].key)
                app.on_option_select()
                app.use_option()
            elif k == "b-name":
                app.var["name"].set("CVDEZ_TP53_AAV")
                app.refresh()
            elif k == "b-export":
                self.cvd_app.filedialog.askdirectory.return_value = exp
                app.export()
            else:
                self.fail("no learner action for hands-on step %s" % k)

        guard = 0
        while True:
            guard += 1
            self.assertLess(guard, 80)
            if t.step.check is not None:
                self.assertFalse(t.done(), "%s is done before the learner acts" % t.step.key)
                learner(t.step)
                self.assertTrue(t.done(), "%s is not done after the learner acts" % t.step.key)
                done_keys.append(t.step.key)
            if t.index == t.total - 1:
                break
            self.assertTrue(t.next(), t.step.key)
        self.assertEqual(len(done_keys), len([s for s in t.steps if s.check]))
        self.assertEqual(app.var["gene"].get(), "TP53")
        self.assertEqual(app.var["vector"].get(), "aav")
        self.assertEqual(app.design.name, "CVDEZ_TP53_AAV")
        files = sorted(os.path.splitext(f)[1] for f in os.listdir(exp))
        self.assertEqual(files, [".fasta", ".gb", ".svg", ".txt"])
        self.assertTrue(glob.glob(os.path.join(exp, "CVDEZ_TP53_AAV.gb")))
        self.assertEqual(t.skipped, set())

    def test_live_text_uses_the_real_design(self):
        from cvdez.steps import design_summary, export_summary
        self.assertIn(self.app.design.name, design_summary(self.t))
        self.assertIn(format(self.app.design.total, ","), design_summary(self.t))
        self.assertIn(self.out, export_summary(self.t))

    def test_the_example_files_describe_the_example_gene(self):
        t, app = self.t, self.app
        t.jump_to_part(2)
        app.open_aneuploidy()
        t.steps[t.first_index_of_part(2) + 2].action(t)
        app.aneu.run()
        self.assertTrue(any(r.gene == "TP53" and r.strategy == "rep" for r in app.aneu.recs))
        self.assertIn("17p", app.aneu.result.arms and " ".join(a.arm for a in app.aneu.result.arms
                                                                 if a.call == "loss"))


class CoachWindow(Harness):
    def make(self):
        return self.coach_mod.Coach(self.app, self.t)

    def test_builds_and_shows_every_step(self):
        c = self.make()
        for _ in range(self.t.total - 1):
            c.update_state()
            self.assertTrue(c.text.content)
            if self.t.can_next():
                c.next()
            else:
                self.t.skip()
                c.show()
        c.close()

    def test_text_for_a_step_has_headings_and_the_task(self):
        c = self.make()
        self.t.jump_to_part(2)
        while self.t.step.key != "b-open":
            self.t.next()
        c.show()
        self.assertIn("What it is", c.text.content)
        self.assertIn("Your turn", c.text.content)
        self.assertIn("Aneuploidy analysis", c.text.content)

    def test_next_button_state_follows_the_check(self):
        c = self.make()
        self.t.jump_to_part(2)
        while self.t.step.key != "b-open":
            self.t.next()
        c.show()
        c.next_btn.configure.reset_mock()
        c.update_state()
        self.assertEqual(c.next_btn.configure.call_args.kwargs["state"], "disabled")
        self.app.open_aneuploidy()
        c.update_state()
        self.assertEqual(c.next_btn.configure.call_args.kwargs["state"], "normal")

    def test_a_missing_widget_means_no_outline_not_a_crash(self):
        c = self.make()
        c.resolvers["vec"] = mock.MagicMock(side_effect=IndexError)
        self.t.index = [s.key for s in self.t.steps].index("vector")
        c.point()


if __name__ == "__main__":
    unittest.main()
