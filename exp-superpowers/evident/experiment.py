from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from evident import _core
from evident.results import AnalysisResult, Decision, LiftEstimate

_DECISION_MAP = [Decision.SHIP, Decision.DONT_SHIP, Decision.KEEP_TESTING]


@dataclass(frozen=True, slots=True)
class BinaryData:
    trials: int
    successes: int


class Experiment:
    @classmethod
    def binary(
        cls,
        *,
        control: dict[str, int],
        treatment: dict[str, int],
        direction: Literal["higher_is_better", "lower_is_better"] = "higher_is_better",
        confidence_threshold: float = 0.95,
    ) -> BinaryExperiment:
        return BinaryExperiment(
            control=BinaryData(**control),
            treatment=BinaryData(**treatment),
            direction=direction,
            confidence_threshold=confidence_threshold,
        )


class BinaryExperiment:
    def __init__(
        self,
        *,
        control: BinaryData,
        treatment: BinaryData,
        direction: Literal["higher_is_better", "lower_is_better"],
        confidence_threshold: float,
    ) -> None:
        self._control = control
        self._treatment = treatment
        self._direction = direction
        self._confidence_threshold = confidence_threshold

    def analyze(self, *, seed: int | None = None) -> AnalysisResult:
        if self._direction == "lower_is_better":
            model_a = _core.BinaryModel(
                self._control.trials - self._control.successes,
                self._control.trials,
            )
            model_b = _core.BinaryModel(
                self._treatment.trials - self._treatment.successes,
                self._treatment.trials,
            )
        else:
            model_a = _core.BinaryModel(self._control.successes, self._control.trials)
            model_b = _core.BinaryModel(self._treatment.successes, self._treatment.trials)

        raw = _core.analyze_binary(
            model_a,
            model_b,
            confidence_threshold=self._confidence_threshold,
            seed=seed,
        )

        return AnalysisResult(
            probability_b_wins=raw.probability_b_wins,
            lift=LiftEstimate(
                mean=raw.lift.mean,
                median=raw.lift.median,
                ci=raw.lift.ci,
            ),
            recommendation=_DECISION_MAP[int(raw.recommendation)],
        )
