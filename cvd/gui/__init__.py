"""Optional tkinter front end.

Importing this package never fails when tkinter is missing: launch_gui() reports the
problem and the caller falls back to the text prompts.  The window classes are imported
lazily inside launch_gui so that the command-line modes never touch tkinter.
"""

import sys

try:  # the command-line modes keep working when tkinter is not installed
    import tkinter as tk
except ImportError:
    tk = None

__all__ = ["launch_gui"]


def launch_gui() -> int:
    """Open the window. Returns 0 after it closes, or 2 if no window could be opened."""
    if tk is None:
        print("Error: tkinter is not installed. On Debian/Ubuntu run: sudo apt install python3-tk",
              file=sys.stderr)
        return 2
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print("Error: could not open a window (%s)." % exc, file=sys.stderr)
        return 2
    from .app import VectorDesignerApp
    VectorDesignerApp(root)
    root.mainloop()
    return 0
