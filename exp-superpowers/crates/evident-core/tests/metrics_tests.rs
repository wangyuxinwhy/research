use approx::assert_relative_eq;
use evident_core::metrics::{
    lift_distribution, probability_treatment_beats_control, recommend_decision, Decision,
    DecisionConfig,
};
use evident_core::models::BinaryModel;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn probability_treatment_clearly_better() {
    let control = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let treatment = BinaryModel::with_uniform_prior(200, 1000); // 20% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_treatment_beats_control(&control, &treatment, &mut rng, 100_000);

    assert!(prob > 0.99);
}

#[test]
fn probability_control_clearly_better() {
    let control = BinaryModel::with_uniform_prior(200, 1000); // 20% rate
    let treatment = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_treatment_beats_control(&control, &treatment, &mut rng, 100_000);

    assert!(prob < 0.01);
}

#[test]
fn probability_similar_rates() {
    let control = BinaryModel::with_uniform_prior(150, 1000);
    let treatment = BinaryModel::with_uniform_prior(155, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_treatment_beats_control(&control, &treatment, &mut rng, 100_000);

    assert!(prob > 0.4 && prob < 0.8);
}

#[test]
fn lift_distribution_positive() {
    let control = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let treatment = BinaryModel::with_uniform_prior(150, 1000); // 15% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&control, &treatment, &mut rng, 100_000, 0.95);

    // Relative lift = (0.15 - 0.10) / 0.10 = 0.50 (50%)
    assert_relative_eq!(lift.mean, 0.50, epsilon = 0.05);
    assert!(lift.ci.0 > 0.0);
}

#[test]
fn lift_distribution_negative() {
    let control = BinaryModel::with_uniform_prior(150, 1000); // 15% rate
    let treatment = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&control, &treatment, &mut rng, 100_000, 0.95);

    // Relative lift = (0.10 - 0.15) / 0.15 = -0.33 (-33%)
    assert_relative_eq!(lift.mean, -0.33, epsilon = 0.05);
    assert!(lift.ci.1 < 0.0);
}

#[test]
fn decision_ship_when_clearly_better() {
    let control = BinaryModel::with_uniform_prior(100, 1000);
    let treatment = BinaryModel::with_uniform_prior(200, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&control, &treatment, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::Ship));
    assert!(result.confidence > 0.95);
}

#[test]
fn decision_dont_ship_when_clearly_worse() {
    let control = BinaryModel::with_uniform_prior(200, 1000);
    let treatment = BinaryModel::with_uniform_prior(100, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&control, &treatment, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::DontShip));
}

#[test]
fn decision_keep_testing_when_uncertain() {
    let control = BinaryModel::with_uniform_prior(10, 100);
    let treatment = BinaryModel::with_uniform_prior(12, 100);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&control, &treatment, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::KeepTesting));
}
