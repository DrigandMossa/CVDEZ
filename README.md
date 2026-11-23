# CVDEZ

**CVDEZ is the guided, easy version of [CVD](https://github.com/DrigandMossa/CVD)**, the cancer gene therapy vector designer.
Instead of a wall of options, it takes you through the program one step at a time, explains each part, and has you build
an example gene therapy yourself: a replacement copy of **TP53** for a tumor that has lost chromosome arm 17p.

Standard library only. Python 3.8 or newer. No installs.

## Start the tutorial

```
python -m cvdez
```

Press **Enter** to accept the suggested answer at any question, type a number to choose something else, and type **q** to
leave. Jump back in later with `--lesson N`.

```
python -m cvdez --list          # the ten lessons
python -m cvdez --lesson 7      # start at "Ranked vector options and why"
python -m cvdez --auto          # watch the whole tutorial with default answers, no questions
python -m cvdez --out my_files  # where the files are written (default: cvdez_output)
python cvdez.pyz                # the same tutorial as one file, no folders needed
```

## What you learn

| # | Lesson | What you do |
|---|--------|-------------|
| 1 | Welcome | What the tool is, and what it is not |
| 2 | The five words you need | vector, insert, promoter, cassette, capacity |
| 3 | Look at the tumor | read an aneuploidy report (practice tumor, or real open data from TCGA) |
| 4 | Turn findings into a plan | choose a suggested therapy; the example is "Replace TP53" |
| 5 | The insert | how the sequence checker works, on a tiny made-up sequence |
| 6 | Pick the delivery setting | in vivo, ex vivo, or not specified |
| 7 | Ranked vector options and why | score six prebuilt options and read why each ranks where it does |
| 8 | Modifications | see which improvements were applied, and which were considered and skipped |
| 9 | Build the vector and read the map | every part, its position, size and job, plus the design checks |
| 10 | Export and what comes next | the files written, and the one command that repeats your example |

Everything on screen after a `|` mark is the real output of the CVD engine, not a mock-up. The tutorial writes the same files
CVD would: the aneuploidy report, the ranked options report, and the finished design as GenBank, FASTA, SVG map and text summary.

## What is in this repository

```
cvdez/      the tutorial (lessons, console helpers, plain-language glossary,
            and a real open-data copy-number file, TCGA-CHOL W5-AA2X-01, for lesson 3)
cvd/        the CVD engine the tutorial drives (a copy of CVD v1.2.0)
tests/      tests that run the whole tutorial
```

Run the tests with `python -m unittest discover -s tests`.

## Important

This is a learning and design tool. Library elements use typical lengths and are written as runs of N until you supply verified
sequences. Making real virus requires institutional biosafety approval; a medicine for patients needs GMP manufacturing,
preclinical safety data and regulatory authorization. The suggestions follow known gene locations and published associations;
they do not predict response.

When you are done here, move on to the full program: `python -m cvd` (graphical window) or the CVD README.
