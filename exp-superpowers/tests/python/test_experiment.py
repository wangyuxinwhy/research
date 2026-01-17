import pytest
from evident import Experiment, Decision


def test_binary_experiment_basic():
    exp = Experiment.binary(
        control={"trials": 1000, "successes": 100},
        treatment={"trials": 1000, "successes": 150},
    )
    result = exp.analyze()

    assert 0.0 <= result.probability_b_wins <= 1.0
    assert result.lift.mean > 0
    assert result.recommendation == Decision.SHIP


def test_binary_experiment_lower_is_better():
    exp = Experiment.binary(
        control={"trials": 1000, "successes": 150},
        treatment={"trials": 1000, "successes": 100},
        direction="lower_is_better",
    )
    result = exp.analyze()

    assert result.probability_b_wins > 0.95
    assert result.recommendation == Decision.SHIP
