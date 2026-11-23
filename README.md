# CVDEZ

**CVDEZ is the guided, easy version of [CVD](https://github.com/DrigandMossa/CVD)**, a cancer gene therapy vector designer.
CVD has many options. CVDEZ takes you through it one step at a time, explains each part in plain language, and has you build
a complete example gene therapy yourself.

The example: a replacement copy of **TP53** (a tumor suppressor) for a tumor that has lost chromosome arm 17p, where TP53 lives.

Standard library only. Python 3.8 or newer. Nothing to install.

## How it works

CVDEZ opens the **real CVD window** and puts a small **coach window** beside it. The coach points at each control with an
orange outline and tells you what it is, what it does and why it is there. You never leave the real program: every click you
make changes the real design.

- **Part 1, tour of every control (35 steps).** One step per control: vector type, strategy, gene, variant, insert box, Load
  file / Clear, the Guide RNA and CAR boxes, promoter, tag, reporter, linker, polyadenylation, bacterial selection, WPRE,
  Kozak, short WPRE, vector name, the Design tab (map, element table, checks, export buttons), and the Vector options tab
  (delivery setting, modifications switch, gallery, ranked list, "Why this ranking", "Modifications", option buttons).
- **Part 2, build your own example (27 steps).** You make a gene therapy yourself. The coach says what to click, and **Next**
  unlocks only when you have done it (or press **Skip this step**). The path: open the Aneuploidy analysis window and learn
  each of its controls, analyze a practice tumor, pick "Replace TP53", send it to the designer, choose AAV, compare ranked
  options, read "Why this ranking" and "Modifications", open a prebuilt vector, use the top option, name it, check it, and
  **export** the files.

## Quick start

```
git clone https://github.com/DrigandMossa/CVDEZ
cd CVDEZ
python -m cvdez
```

Or run the single-file version: `python cvdez.pyz`

The window needs **tkinter** (included with Python on Windows and macOS; on Debian/Ubuntu run `sudo apt install python3-tk`).
Without tkinter or a display, CVDEZ falls back to a text-only tutorial.

| Command | What it does |
|---------|--------------|
| `python -m cvdez` | Open CVD with the coach (starts at Part 1) |
| `python -m cvdez --part 2` | Start straight at Part 2, building your own example |
| `python -m cvdez --out DIR` | Folder for the practice tumor file (default `cvdez_output`) |
| `python -m cvdez --list` | List every step of both tutorials |
| `python -m cvdez --console` | Use the text-only tutorial in the terminal |
| `python -m cvdez --console --auto` | Play the text tutorial with default answers (no questions) |

In the coach: **Back** and **Next** move between steps, **Skip the tour** jumps to Part 2, **Close coach** leaves the CVD window
open for your own work. You can drag the coach window anywhere.

## What is a gene therapy vector?

A vector is a delivery truck for a gene. CVDEZ teaches five ideas that explain almost everything in CVD:

1. **Vector**: the truck. A virus with its harmful genes removed (lentivirus or AAV), or a plain plasmid.
2. **Insert**: the cargo. The gene you want cells to make (here, TP53).
3. **Promoter**: the ignition. It sets when and how strongly the insert is switched on.
4. **Cassette**: everything that gets packaged: promoter, insert and helper parts.
5. **Capacity**: the size of the truck bed. AAV holds about 4.7 kb and lentivirus about 8 kb. A cassette that is too big does not fit.

## What you get at the end

At the end of Part 2 you export, with the real **Export files...** button, four files named after your vector:

- a GenBank file `.gb` (opens in SnapGene, Benchling, ApE)
- a FASTA file `.fasta`
- an SVG circular map `.svg`
- a text summary `.txt` with the checks and the reasoning behind the design

## Repository layout

```
cvdez/      the tutorial
  steps.py    all the lesson text (what / does / why / task) and the "is it done?" checks
  tutorial.py the step-by-step state machine (no tkinter)
  coach.py    the coach window and the orange outline
  app.py      the real CVD window, with three small hooks that record what you have done
  lessons.py, ui.py, glossary.py   the text-only fallback tutorial and its bundled TCGA tumor file
cvd/        the CVD engine the tutorial drives (a copy of CVD v1.2.0; the tutorial window IS this program's window)
tests/      tests, including a simulated learner who builds and exports the example
cvdez.pyz   the tutorial as a single runnable file
```

Run the tests with `python -m unittest discover -s tests`.

## From CVDEZ to CVD

CVDEZ teaches the workflow. For your own work use CVD: `python -m cvd` opens the graphical window, and the same example
as one command is `python -m cvd --strategy rep --gene TP53 --setting "in vivo" --rank --use-option 1`.

## Important

This is a learning and design tool, not a way to make a medicine. Library parts use typical lengths and are written as runs of N
until you supply verified sequences, so the files are not ready to order. Making real virus needs institutional biosafety approval.
A medicine for patients needs GMP manufacturing, preclinical safety data and regulatory authorization. Suggestions follow known
gene locations and published associations and do not predict response. Arm-level loss does not prove a gene is inactive, so
confirm with mutation and expression data.

## Testing note

The tests drive the real CVD window code through stand-in widgets, so they run without a display. They check that every step
has text, every outline target exists, each hands-on step is locked until it is done, and that a simulated learner really builds
and exports the example. They cannot show how the orange outline looks on a real screen. If an outline is misplaced on your
machine, please open an issue; the lesson text is unaffected.
