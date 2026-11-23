"""The tutorial's state machine: which step is showing, whether it is done, and what text to show.

No tkinter in here, so it can be tested anywhere.  The coach window (coach.py) is a thin view on top of it.
"""

from typing import List, Optional

from .steps import BUILD, STEPS, TOUR, Step, txt


class Tutorial:
    def __init__(self, app, out: str, steps: Optional[List[Step]] = None):
        self.app = app
        self.out = out
        self.steps = list(steps if steps is not None else STEPS)
        self.index = 0
        self.skipped = set()          # keys of hands-on steps the learner skipped
        self.finished = False

    # ---- position -------------------------------------------------------
    @property
    def step(self) -> Step:
        return self.steps[self.index]

    @property
    def total(self) -> int:
        return len(self.steps)

    def label(self) -> str:
        part = "Part %d: %s" % (self.step.part, "Tour of every control" if self.step.part == 1 else "Build your own example")
        return "%s   |   Step %d of %d" % (part, self.index + 1, self.total)

    def first_index_of_part(self, part: int) -> int:
        for i, s in enumerate(self.steps):
            if s.part == part:
                return i
        return 0

    # ---- progress -------------------------------------------------------
    def needs_action(self) -> bool:
        return self.step.check is not None

    def done(self) -> bool:
        """True when nothing is required, or the learner has done what the step asks."""
        s = self.step
        if s.check is None or s.key in self.skipped:
            return True
        try:
            return bool(s.check(self))
        except Exception:               # a widget that is gone counts as "not done yet", never as a crash
            return False

    def can_next(self) -> bool:
        return self.index < self.total - 1 and self.done()

    def can_back(self) -> bool:
        return self.index > 0

    def next(self) -> bool:
        if not self.can_next():
            if self.index == self.total - 1 and self.done():
                self.finished = True
            return False
        self.index += 1
        self.enter()
        return True

    def back(self) -> bool:
        if not self.can_back():
            return False
        self.index -= 1
        self.enter()
        return True

    def skip(self) -> bool:
        """Let the learner past a hands-on step they cannot or do not want to do."""
        if self.step.check is None:
            return False
        self.skipped.add(self.step.key)
        return self.next()

    def jump_to_part(self, part: int) -> None:
        self.index = self.first_index_of_part(part)
        self.enter()

    def enter(self) -> None:
        """Run the setup of the step that just opened."""
        s = self.step
        if s.strategy is not None and self.app.var["strategy"].get() != s.strategy:
            self.app.var["strategy"].set(s.strategy)
            self.app.on_strategy()
        if s.setup is not None:
            s.setup(self)

    # ---- text -----------------------------------------------------------
    def sections(self) -> List[tuple]:
        """(heading, text) pairs for the current step, skipping empty ones."""
        s = self.step
        out = [("What it is", txt(s.what, self)), ("What it does", txt(s.does, self)),
               ("Why it is there", txt(s.why, self))]
        if s.task:
            out.append(("Your turn", txt(s.task, self)))
        return [(h, t) for h, t in out if t]


__all__ = ["Tutorial", "TOUR", "BUILD", "STEPS"]
