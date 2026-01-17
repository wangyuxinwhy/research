from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Decision(Enum):
    SHIP = auto()
    DONT_SHIP = auto()
    KEEP_TESTING = auto()


@dataclass(frozen=True, slots=True)
class LiftEstimate:
    mean: float
    median: float
    ci: tuple[float, float]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    probability_b_wins: float
    lift: LiftEstimate
    recommendation: Decision
