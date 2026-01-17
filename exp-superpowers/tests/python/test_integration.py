from evident import Decision, Experiment


def test_customer_service_scenario():
    """Real scenario: testing new AI model for customer service.

    Control has 15% human handoff rate, treatment has 12%.
    Lower is better, so treatment should win.
    """
    exp = Experiment.binary(
        control={"trials": 5000, "successes": 750},
        treatment={"trials": 5000, "successes": 600},
        direction="lower_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_treatment_wins > 0.95
    assert result.lift.mean > 0
    assert result.recommendation == Decision.SHIP


def test_satisfaction_rate_scenario():
    """Real scenario: testing satisfaction rate improvement.

    Control has 82% satisfaction, treatment has 85%.
    Higher is better, so treatment should win.
    """
    exp = Experiment.binary(
        control={"trials": 2000, "successes": 1640},
        treatment={"trials": 2000, "successes": 1700},
        direction="higher_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_treatment_wins > 0.80
    assert result.lift.mean > 0


def test_inconclusive_small_sample():
    """Small sample should recommend keep testing."""
    exp = Experiment.binary(
        control={"trials": 50, "successes": 5},
        treatment={"trials": 50, "successes": 7},
    )

    result = exp.analyze(seed=42)

    assert result.recommendation == Decision.KEEP_TESTING
