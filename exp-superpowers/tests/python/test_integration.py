from evident import Experiment, Decision


def test_customer_service_scenario():
    """Real scenario: testing new AI model for customer service."""
    # Control: 15% human handoff rate
    # Treatment: 12% human handoff rate (lower is better)
    exp = Experiment.binary(
        control={"trials": 5000, "successes": 750},
        treatment={"trials": 5000, "successes": 600},
        direction="lower_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_b_wins > 0.95
    assert result.lift.mean > 0  # Positive lift = improvement in desired direction
    assert result.recommendation == Decision.SHIP


def test_satisfaction_rate_scenario():
    """Real scenario: testing satisfaction rate improvement."""
    # Control: 82% satisfaction (4-5 stars)
    # Treatment: 85% satisfaction
    exp = Experiment.binary(
        control={"trials": 2000, "successes": 1640},
        treatment={"trials": 2000, "successes": 1700},
        direction="higher_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_b_wins > 0.80
    assert result.lift.mean > 0


def test_inconclusive_small_sample():
    """Small sample should recommend keep testing."""
    exp = Experiment.binary(
        control={"trials": 50, "successes": 5},
        treatment={"trials": 50, "successes": 7},
    )

    result = exp.analyze(seed=42)

    assert result.recommendation == Decision.KEEP_TESTING
