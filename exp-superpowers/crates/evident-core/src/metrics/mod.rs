use rand::Rng;

use crate::models::BinaryModel;

/// Estimates P(B > A) via Monte Carlo simulation.
///
/// # Panics
/// Panics if the underlying Beta distributions cannot be sampled (should not happen with valid models).
#[must_use]
pub fn probability_b_beats_a<R: Rng>(
    model_a: &BinaryModel,
    model_b: &BinaryModel,
    rng: &mut R,
    n_samples: usize,
) -> f64 {
    let posterior_a = model_a.posterior();
    let posterior_b = model_b.posterior();

    let samples_a = posterior_a.sample_n(rng, n_samples);
    let samples_b = posterior_b.sample_n(rng, n_samples);

    let wins: usize = samples_a
        .iter()
        .zip(samples_b.iter())
        .filter(|(a, b)| b > a)
        .count();

    #[allow(clippy::cast_precision_loss)]
    let result = wins as f64 / n_samples as f64;
    result
}
