use rand::Rng;

use crate::inference::{credible_interval, mean, median};
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

#[derive(Debug, Clone)]
pub struct LiftResult {
    pub mean: f64,
    pub median: f64,
    pub ci: (f64, f64),
    pub samples: Vec<f64>,
}

/// Computes the relative lift distribution ((B-A)/A) via Monte Carlo simulation.
///
/// # Panics
///
/// Panics if the underlying Beta distributions cannot be sampled.
#[must_use]
pub fn lift_distribution<R: Rng>(
    model_a: &BinaryModel,
    model_b: &BinaryModel,
    rng: &mut R,
    n_samples: usize,
    ci_level: f64,
) -> LiftResult {
    let posterior_a = model_a.posterior();
    let posterior_b = model_b.posterior();

    let samples_a = posterior_a.sample_n(rng, n_samples);
    let samples_b = posterior_b.sample_n(rng, n_samples);

    let lift_samples: Vec<f64> = samples_a
        .iter()
        .zip(samples_b.iter())
        .map(|(a, b)| {
            if *a == 0.0 {
                0.0
            } else {
                (b - a) / a
            }
        })
        .collect();

    LiftResult {
        mean: mean(&lift_samples),
        median: median(&lift_samples),
        ci: credible_interval(&lift_samples, ci_level),
        samples: lift_samples,
    }
}
