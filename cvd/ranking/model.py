"""Dataclasses for the ranking: insert profile, criterion scores, options and the result."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from ..model import Config, Design


@dataclass
class InsertProfile:
    kind: str                 # coding sequence, scFv or guide target
    name: str
    length: int
    source: str               # pasted sequence, or where the assumed length comes from
    known: bool               # True when a sequence was pasted
    gc: Optional[int]
    polya: List[int]          # 1-based positions of AATAAA or ATTAAA
    donors: List[int]         # 1-based positions of splice-donor-like motifs (MAGGTRAGT)
    stops: int                # in-frame stop codons before the last codon
    first_stop: int
    issues: List[Tuple[str, str]]     # (level, text); these affect every option


@dataclass
class CriterionScore:
    key: str
    label: str
    points: int
    maximum: int
    reason: str
    short: str                # a few words, used when comparing options


@dataclass
class Modification:
    """One change made to a prebuilt option (or a change that was considered and not made)."""
    key: str
    title: str
    change: str               # what was changed, before -> after
    reason: str
    bp: int = 0               # change in cassette size between the ITRs/LTRs (negative saves space)
    applied: bool = True
    tradeoff: str = ""        # what the change costs, when it costs anything


@dataclass
class VectorOption:
    key: str
    vector: str
    arrangement: str
    layout: str
    title: str
    config: Config
    design: Design
    cassette: int
    limit: int
    feasible: bool
    scores: List[CriterionScore]
    total: int = 0
    rank: int = 0
    generated_because: str = ""
    base_cassette: int = 0                                     # cassette size before any modification
    mods: List[Modification] = field(default_factory=list)

    @property
    def applied_mods(self) -> List[Modification]:
        return [m for m in self.mods if m.applied]

    def score(self, key: str) -> CriterionScore:
        return next(s for s in self.scores if s.key == key)

    @property
    def applicability(self) -> int:
        """The score shown to the user: 0 when the cassette does not fit the vector."""
        return self.total if self.feasible else 0


@dataclass
class RankingResult:
    strategy: str
    profile: InsertProfile
    setting: str              # in vivo, ex vivo or unspecified
    setting_note: str
    options: List[VectorOption]
    optimized: bool = True    # False when modifications were switched off
