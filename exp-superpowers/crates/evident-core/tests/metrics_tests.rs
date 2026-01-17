use approx::assert_relative_eq;
use evident_core::metrics::{lift_distribution, probability_b_beats_a};
use evident_core::models::BinaryModel;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn probability_b_clearly_better() {
    let model_a = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let model_b = BinaryModel::with_uniform_prior(200, 1000); // 20% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // B is clearly better, probability should be very high
    assert!(prob > 0.99);
}

#[test]
fn probability_a_clearly_better() {
    let model_a = BinaryModel::with_uniform_prior(200, 1000); // 20% rate
    let model_b = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // A is clearly better, probability should be very low
    assert!(prob < 0.01);
}

#[test]
fn probability_similar_rates() {
    let model_a = BinaryModel::with_uniform_prior(150, 1000);
    let model_b = BinaryModel::with_uniform_prior(155, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // Similar rates, probability should be around 0.5-0.7
    assert!(prob > 0.4 && prob < 0.8);
}

#[test]
fn lift_distribution_positive() {
    let model_a = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let model_b = BinaryModel::with_uniform_prior(150, 1000); // 15% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&model_a, &model_b, &mut rng, 100_000, 0.95);

    // Relative lift = (0.15 - 0.10) / 0.10 = 0.50 (50%)
    assert_relative_eq!(lift.mean, 0.50, epsilon = 0.05);
    assert!(lift.ci.0 > 0.0); // Lower bound positive
}

#[test]
fn lift_distribution_negative() {
    let model_a = BinaryModel::with_uniform_prior(150, 1000); // 15% rate
    let model_b = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&model_a, &model_b, &mut rng, 100_000, 0.95);

    // Relative lift = (0.10 - 0.15) / 0.15 = -0.33 (-33%)
    assert_relative_eq!(lift.mean, -0.33, epsilon = 0.05);
    assert!(lift.ci.1 < 0.0); // Upper bound negative
}
