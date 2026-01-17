from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    SHIP = "Ship"
    DONT_SHIP = "DontShip"
    KEEP_TESTING = "KeepTesting"


@dataclass(frozen=True, slots=True)
class LiftEstimate:
    mean: float
    median: float
    ci: tuple[float, float]

    def ci_excludes_zero(self) -> bool:
        return self.ci[0] > 0 or self.ci[1] < 0


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    probability_b_wins: float
    lift: LiftEstimate
    recommendation: Decision

    def is_significant(self, threshold: float = 0.95) -> bool:
        above = self.probability_b_wins > threshold
        below = self.probability_b_wins < (1 - threshold)
        return above or below
