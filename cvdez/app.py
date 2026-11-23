"""The real CVD window, with a few hooks so the coach can tell what the learner has done.

TutorialApp IS the CVD VectorDesignerApp.  It only records events (the analysis window opened, a prebuilt
vector was opened, files were exported); it changes no behaviour.
"""

import os

from cvd.gui.app import VectorDesignerApp


class TutorialApp(VectorDesignerApp):
    def __init__(self, root, out: str) -> None:
        self.out = out
        self.aneu = None
        self.expanded = False
        self.exported = False
        super().__init__(root)
        root.title("CVD (CVDEZ tutorial)")
        root.geometry("1220x700+10+10")
        os.makedirs(out, exist_ok=True)

    def open_aneuploidy(self) -> None:
        from cvd.gui.aneuploidy import AneuploidyWindow
        self.aneu = AneuploidyWindow(self)

    def expand_option(self, key: str) -> None:
        self.expanded = True
        super().expand_option(key)

    def set_status(self, text: str) -> None:
        if text.startswith("Exported"):
            self.exported = True
        super().set_status(text)
