"""Console helpers: printing, pausing and asking questions.

In auto mode nothing is read from the keyboard: every question takes its default.
That makes the whole tutorial runnable in tests and in CI.
"""

import sys
import textwrap
from typing import List, Optional, TextIO

WIDTH = 78


class Console:
    def __init__(self, auto: bool = False, out: Optional[TextIO] = None, inp: Optional[TextIO] = None):
        self.auto = auto
        self.out = out or sys.stdout
        self.inp = inp or sys.stdin
        self.answers: List[str] = []       # every answer given, in order (used by tests)

    # -- output ---------------------------------------------------------
    def say(self, text: str = "", indent: int = 0) -> None:
        """Print a paragraph, wrapped. Blank lines separate paragraphs."""
        pad = " " * indent
        for para in text.split("\n\n"):
            lines = para.split("\n")
            if len(lines) > 1 and all(l.startswith(("  ", "-", "*")) or not l.strip() for l in lines):
                # a list or table: wrap each item on its own, with a hanging indent
                for l in lines:
                    lead = len(l) - len(l.lstrip())
                    print(textwrap.fill(l.strip(), WIDTH - indent, initial_indent=pad + " " * lead,
                                        subsequent_indent=pad + " " * (lead + 3)), file=self.out)
            else:
                print(textwrap.fill(" ".join(l.strip() for l in lines), WIDTH - indent,
                                    initial_indent=pad, subsequent_indent=pad), file=self.out)
            print(file=self.out)

    def raw(self, text: str) -> None:
        """Print program output exactly as it is, indented so it stands apart from the teaching text."""
        for line in text.rstrip("\n").split("\n"):
            print("  | " + line, file=self.out)
        print(file=self.out)

    def heading(self, text: str) -> None:
        print("=" * WIDTH, file=self.out)
        print(text, file=self.out)
        print("=" * WIDTH, file=self.out)
        print(file=self.out)

    def tip(self, text: str) -> None:
        self.say("TIP: " + text)

    # -- input ----------------------------------------------------------
    def _read(self, prompt: str) -> Optional[str]:
        print(prompt, end="", file=self.out, flush=True)
        try:
            line = self.inp.readline()
        except (KeyboardInterrupt, EOFError):
            return None
        if line == "":
            return None
        return line.rstrip("\n")

    def pause(self, text: str = "Press Enter to continue (or type q to quit) ") -> None:
        if self.auto:
            return
        ans = self._read(text)
        if ans is not None and ans.strip().lower() in ("q", "quit", "exit"):
            raise Quit()
        print(file=self.out)

    def choose(self, question: str, options: List[str], default: int = 1, notes: Optional[List[str]] = None) -> int:
        """Ask the user to pick one option by number. Returns the 1-based number."""
        self.say(question)
        for i, opt in enumerate(options, 1):
            mark = "  (default)" if i == default else ""
            print("  %d. %s%s" % (i, opt, mark), file=self.out)
            if notes and notes[i - 1]:
                for l in textwrap.wrap(notes[i - 1], WIDTH - 7):
                    print("       " + l, file=self.out)
        print(file=self.out)
        if self.auto:
            self.answers.append(str(default))
            print("(auto mode: choosing %d)\n" % default, file=self.out)
            return default
        while True:
            ans = self._read("Your choice [%d]: " % default)
            if ans is None:
                self.answers.append(str(default))
                return default
            ans = ans.strip()
            if ans.lower() in ("q", "quit", "exit"):
                raise Quit()
            if ans == "":
                self.answers.append(str(default))
                print(file=self.out)
                return default
            if ans.isdigit() and 1 <= int(ans) <= len(options):
                self.answers.append(ans)
                print(file=self.out)
                return int(ans)
            print("Please type a number from 1 to %d, or press Enter for %d." % (len(options), default), file=self.out)

    def text(self, question: str, default: str = "") -> str:
        """Ask for free text. Empty input keeps the default."""
        self.say(question)
        if self.auto:
            self.answers.append(default)
            print("(auto mode: using %r)\n" % default, file=self.out)
            return default
        ans = self._read("> ")
        print(file=self.out)
        if ans is None or not ans.strip():
            self.answers.append(default)
            return default
        self.answers.append(ans.strip())
        return ans.strip()


class Quit(Exception):
    """Raised when the learner asks to leave the tutorial."""
