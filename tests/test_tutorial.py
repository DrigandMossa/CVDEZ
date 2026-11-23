import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cvdez.cli import main                      # noqa: E402
from cvdez.glossary import KIND, explain_kind    # noqa: E402
from cvdez.lessons import LESSONS, TOY_ORF       # noqa: E402
from cvdez.ui import Console                     # noqa: E402


def run(argv, stdin=None):
    out = io.StringIO()
    old = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out):
            status = main(argv)
    finally:
        sys.stdin = old
    return status, out.getvalue()


class AutoRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.status, cls.text = run(["--console", "--auto", "--out", cls.tmp])

    def test_finishes(self):
        self.assertEqual(self.status, 0)

    def test_every_lesson_shown_in_order(self):
        last = -1
        for i in range(1, len(LESSONS) + 1):
            pos = self.text.find("Lesson %d of %d" % (i, len(LESSONS)))
            self.assertGreater(pos, last, "lesson %d missing or out of order" % i)
            last = pos

    def test_builds_tp53_example(self):
        self.assertIn("Replace TP53", self.text)
        self.assertIn("TP53", self.text)
        self.assertIn("5,204 bp", self.text)

    def test_writes_all_files(self):
        design = os.path.join(self.tmp, "design")
        exts = sorted(os.path.splitext(f)[1] for f in os.listdir(design))
        self.assertEqual(exts, [".fasta", ".gb", ".svg", ".txt"])
        self.assertTrue(any(f.endswith("_aneuploidy.txt") for f in os.listdir(self.tmp)))
        self.assertTrue(any(f.endswith("_vector_options.txt") for f in os.listdir(self.tmp)))

    def test_shows_modifications(self):
        self.assertIn("kanamycin", self.text)

    def test_one_command_repeat_is_valid(self):
        line = [l for l in self.text.splitlines() if "python -m cvd --strategy rep" in l and "--use-option" in l]
        self.assertTrue(line)


class Interactive(unittest.TestCase):
    def test_choices_from_stdin(self):
        tmp = tempfile.mkdtemp()
        # Enter, Enter (the two opening pauses), then 2 = the real TCGA tumor, then Enter for every other prompt.
        status, text = run(["--console", "--out", tmp], "\n\n2\n" + "\n" * 40)
        self.assertEqual(status, 0)
        self.assertIn("TCGA-W5-AA2X-01", text)

    def test_quit_is_clean(self):
        status, text = run(["--console", "--out", tempfile.mkdtemp()], "q\n")
        self.assertEqual(status, 0)
        self.assertIn("Leaving the tutorial", text)

    def test_end_of_input_takes_defaults(self):
        status, text = run(["--console", "--out", tempfile.mkdtemp()], "")
        self.assertEqual(status, 0)
        self.assertIn("Lesson 10 of 10", text)

    def test_bad_number_reprompts(self):
        ui = Console(auto=False, inp=io.StringIO("9\nx\n2\n"), out=io.StringIO())
        self.assertEqual(ui.choose("pick", ["a", "b", "c"]), 2)


class Options(unittest.TestCase):
    def test_list(self):
        status, text = run(["--list"])
        self.assertEqual(status, 0)
        self.assertIn("Window tutorial", text)
        self.assertIn("Text tutorial", text)

    def test_start_at_lesson(self):
        status, text = run(["--auto", "--lesson", "9", "--out", tempfile.mkdtemp()])
        self.assertEqual(status, 0)
        self.assertNotIn("Lesson 1 of", text)
        self.assertIn("Lesson 9 of 10", text)
        self.assertIn("Lesson 10 of 10", text)

    def test_bad_lesson(self):
        status, _ = run(["--auto", "--lesson", "99"])
        self.assertEqual(status, 2)

    def test_real_data_path(self):
        # Pick the TCGA tumor, then whatever is suggested, in auto order via stdin.
        status, text = run(["--lesson", "3", "--out", tempfile.mkdtemp()], "2\n" + "\n" * 40)
        self.assertEqual(status, 0)
        self.assertIn("TCGA-W5-AA2X-01", text)


class Teaching(unittest.TestCase):
    def test_glossary_covers_every_kind_the_builder_makes(self):
        from cvd.design.builder import build_design
        from cvd.model import Config
        kinds = set()
        for cfg in (Config(strategy="rep", gene="TP53", marker="EGFP"), Config(vector="aav", gene="TP53"),
                    Config(strategy="car", gene="CD19"), Config(strategy="guide", gene="KRAS", target="GCTGGTGGCGTAGGCAAGAGT")):
            kinds |= {f.kind for f in build_design(cfg).features}
        for k in kinds:
            self.assertIn(k, KIND, "no plain-language text for feature kind %r" % k)

    def test_unknown_kind_has_fallback(self):
        self.assertTrue(explain_kind("zzz")[1])

    def test_toy_orf_triggers_the_polya_warning(self):
        from cvd.design.builder import build_design
        from cvd.model import Config
        d = build_design(Config(strategy="rep", gene="Toy", sequence=TOY_ORF))
        self.assertTrue(any("polyadenylation" in t for _, t in d.messages))


if __name__ == "__main__":
    unittest.main()
