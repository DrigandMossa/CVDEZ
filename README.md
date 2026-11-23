# CVDEZ

**CVDEZ is the guided, easy version of [CVD](https://github.com/DrigandMossa/CVD)**, a cancer gene therapy vector designer.
CVD has many options. CVDEZ takes you through it one step at a time, explains each part in plain language, and has you build
a complete example gene therapy yourself.

The example: a replacement copy of **TP53** (a tumor suppressor) for a tumor that has lost chromosome arm 17p, where TP53 lives.

Standard library only. Python 3.8 or newer. Nothing to install.

## Quick start

```
git clone https://github.com/DrigandMossa/CVDEZ
cd CVDEZ
python -m cvdez
```

Or run the single-file version, with no folders needed: `python cvdez.pyz`

At every question, press **Enter** to take the suggested answer, type a number to choose another, or type **q** to leave.

| Command | What it does |
|---------|--------------|
| `python -m cvdez` | Start the tutorial |
| `python -m cvdez --list` | List the ten lessons |
| `python -m cvdez --lesson 7` | Start at lesson 7 (earlier steps are filled in with defaults) |
| `python -m cvdez --auto` | Play the whole tutorial with default answers, no questions |
| `python -m cvdez --out DIR` | Choose where files are written (default `cvdez_output`) |

## What is a gene therapy vector?

A vector is a delivery truck for a gene. CVDEZ teaches five ideas that explain almost everything in CVD:

1. **Vector**: the truck. A virus with its harmful genes removed (lentivirus or AAV), or a plain plasmid.
2. **Insert**: the cargo. The gene you want cells to make (here, TP53).
3. **Promoter**: the ignition. It sets when and how strongly the insert is switched on.
4. **Cassette**: everything that gets packaged: promoter, insert and helper parts.
5. **Capacity**: the size of the truck bed. AAV holds about 4.7 kb and lentivirus about 8 kb. A cassette that is too big does not fit.

## The ten lessons

| # | Lesson | What you do |
|---|--------|-------------|
| 1 | Welcome | Learn what the tool is, and what it is not |
| 2 | The five words you need | Vector, insert, promoter, cassette, capacity |
| 3 | Look at the tumor | Read an aneuploidy report for a practice tumor or real open data (TCGA-CHOL W5-AA2X-01) |
| 4 | Turn findings into a plan | Choose a suggested therapy; the example is "Replace TP53" |
| 5 | The insert | See how the sequence checker works, using a tiny made-up sequence |
| 6 | Pick the delivery setting | In vivo, ex vivo, or not specified |
| 7 | Ranked vector options and why | Read the scores for six prebuilt options and why each ranks where it does |
| 8 | Modifications | See which improvements were applied, and which were considered and skipped |
| 9 | Build the vector and read the map | Every part, its position, size and job, plus the design checks |
| 10 | Export and what comes next | The files written, and the one command that repeats your example |

Everything shown after a `|` mark on screen is the real output of the CVD engine, not a mock-up.

## What you get at the end

The tutorial writes real files into the output folder:

- an aneuploidy report and per-arm table for the tumor
- a ranked vector options report
- `design/`: the finished vector as a GenBank file (opens in SnapGene, Benchling, ApE), a FASTA file, an SVG circular map and a text summary

## Repository layout

```
cvdez/      the tutorial: lessons, console helpers, plain-language glossary,
            and the bundled open-data tumor file
cvd/        the CVD engine the tutorial drives (a copy of CVD v1.2.0)
tests/      tests that run the whole tutorial
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
