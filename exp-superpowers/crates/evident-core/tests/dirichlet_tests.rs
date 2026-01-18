use approx::assert_relative_eq;
use evident_core::distributions::Dirichlet;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn dirichlet_creation() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    assert_eq!(dir.alpha().len(), 3);
    assert_relative_eq!(dir.alpha()[0], 1.0);
    assert_relative_eq!(dir.alpha()[1], 2.0);
    assert_relative_eq!(dir.alpha()[2], 3.0);
}

#[test]
fn dirichlet_mean() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    let mean = dir.mean();
    // Mean_i = alpha_i / sum(alpha) = [1/6, 2/6, 3/6]
    assert_relative_eq!(mean[0], 1.0 / 6.0);
    assert_relative_eq!(mean[1], 2.0 / 6.0);
    assert_relative_eq!(mean[2], 3.0 / 6.0);
}

#[test]
fn dirichlet_sampling_sums_to_one() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    let mut rng = ChaCha8Rng::seed_from_u64(42);

    for _ in 0..100 {
        let sample = dir.sample(&mut rng);
        let sum: f64 = sample.iter().sum();
        assert_relative_eq!(sum, 1.0, epsilon = 1e-10);
    }
}

#[test]
#[allow(clippy::cast_precision_loss)]
fn dirichlet_sampling_distribution() {
    let dir = Dirichlet::new(vec![2.0, 3.0, 5.0]);
    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let samples = dir.sample_n(&mut rng, 10000);

    let theoretical_mean = dir.mean();
    let n_samples = samples.len() as f64;
    let sample_mean: Vec<f64> = (0..dir.k())
        .map(|i| samples.iter().map(|s| s[i]).sum::<f64>() / n_samples)
        .collect();

    for i in 0..dir.k() {
        assert_relative_eq!(sample_mean[i], theoretical_mean[i], epsilon = 0.01);
    }
}
