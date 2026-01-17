use rand::Rng;

use crate::inference::{credible_interval, mean, median};
use crate::models::BinaryModel;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Decision {
    Ship,
    DontShip,
    KeepTesting,
}

#[derive(Debug, Clone)]
pub struct DecisionConfig {
    pub confidence_threshold: f64,
    pub n_samples: usize,
}

impl Default for DecisionConfig {
    fn default() -> Self {
        Self {
            confidence_threshold: 0.95,
            n_samples: 100_000,
        }
    }
}

#[derive(Debug, Clone)]
pub struct DecisionResult {
    pub recommendation: Decision,
    pub confidence: f64,
    pub probability_b_wins: f64,
}

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

/// Recommends Ship/DontShip/KeepTesting based on P(B>A) and confidence threshold.
///
/// # Panics
///
/// Panics if the underlying Beta distributions cannot be sampled.
#[must_use]
#[allow(clippy::similar_names)]
pub fn recommend_decision<R: Rng>(
    model_a: &BinaryModel,
    model_b: &BinaryModel,
    rng: &mut R,
    config: &DecisionConfig,
) -> DecisionResult {
    let prob_b_wins = probability_b_beats_a(model_a, model_b, rng, config.n_samples);
    let prob_a_wins = 1.0 - prob_b_wins;

    let (recommendation, confidence) = if prob_b_wins >= config.confidence_threshold {
        (Decision::Ship, prob_b_wins)
    } else if prob_a_wins >= config.confidence_threshold {
        (Decision::DontShip, prob_a_wins)
    } else {
        (Decision::KeepTesting, prob_b_wins.max(prob_a_wins))
    };

    DecisionResult {
        recommendation,
        confidence,
        probability_b_wins: prob_b_wins,
    }
}
