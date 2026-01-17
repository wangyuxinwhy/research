use approx::assert_relative_eq;
use evident_core::distributions::Beta;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn beta_creation() {
    let beta = Beta::new(2.0, 3.0);
    assert_relative_eq!(beta.alpha(), 2.0);
    assert_relative_eq!(beta.beta(), 3.0);
}

#[test]
fn beta_mean() {
    let beta = Beta::new(2.0, 3.0);
    // Mean of Beta(2,3) = 2/(2+3) = 0.4
    assert_relative_eq!(beta.mean(), 0.4);
}

#[test]
fn beta_variance() {
    let beta = Beta::new(2.0, 3.0);
    // Var of Beta(2,3) = 2*3 / ((2+3)^2 * (2+3+1)) = 6/150 = 0.04
    assert_relative_eq!(beta.variance(), 0.04);
}

#[test]
fn beta_sampling_distribution() {
    let beta = Beta::new(2.0, 5.0);
    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let samples = beta.sample_n(&mut rng, 10000);

    #[allow(clippy::cast_precision_loss)]
    let sample_mean: f64 = samples.iter().sum::<f64>() / samples.len() as f64;
    // Mean should be close to theoretical: 2/(2+5) ≈ 0.286
    assert_relative_eq!(sample_mean, beta.mean(), epsilon = 0.01);
}
