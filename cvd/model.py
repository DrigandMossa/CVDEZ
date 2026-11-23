"""Dataclasses shared across the designer and the CNV analysis."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Config:
    vector: str = "lenti"
    strategy: str = "rep"
    gene: str = ""
    variant: str = ""
    sequence: str = ""            # insert ORF / scFv (text, FASTA allowed)
    promoter: Optional[str] = None
    marker: Optional[str] = None
    link: str = "P2A"
    tag: str = "none"
    polya: Optional[str] = None
    resistance: str = "AmpR"
    wpre: Optional[bool] = None
    wpre_short: bool = False      # 247 bp WPRE3 instead of the 589 bp WPRE (saves space in AAV)
    kozak: bool = True
    hinge: str = "CD8a hinge/TM"
    costim: str = "4-1BB"
    guide_type: str = "shRNA"
    target: str = ""
    name: str = ""
    overrides: Dict[str, str] = field(default_factory=dict)
    basis: str = ""               # why this design was chosen; shown in the summary


@dataclass
class Feature:
    id: str
    name: str
    kind: str
    length: int
    seq: Optional[str] = None
    in_cassette: bool = False
    custom: bool = False
    start: int = 0
    end: int = 0


@dataclass
class Design:
    name: str
    vector: str
    strategy: str
    features: List[Feature]
    seq: str
    messages: List[Tuple[str, str]]   # (level, text); level: error / warn / info
    basis: str = ""

    @property
    def total(self) -> int:
        return len(self.seq)


@dataclass
class Segment:
    chrom: str
    start: int
    end: int
    value: float


@dataclass
class ArmResult:
    arm: str
    coverage: float      # fraction of the arm covered by input segments
    mean_lr: float       # mean log2 ratio relative to the baseline
    frac_gain: float
    frac_loss: float
    call: str            # gain, loss, neutral, partial, no data or not scored


@dataclass
class AneuploidyResult:
    sample: str
    build: str
    value_type: str
    baseline_desc: str
    arms: List[ArmResult]
    whole_chromosomes: List[str]
    gains: int
    losses: int
    fga: float           # percent of the covered autosomal genome that is gained or lost
    wgd_suspected: bool
    findings: List[Tuple[str, str]]
    notes: List[str]

    @property
    def score(self) -> int:
        return self.gains + self.losses


@dataclass
class Recommendation:
    strategy: str
    gene: str
    promoter: Optional[str]
    title: str
    reason: str
