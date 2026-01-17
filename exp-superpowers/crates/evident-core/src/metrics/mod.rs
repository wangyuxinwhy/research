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
    pub probability_treatment_wins: f64,
}

/// Estimates P(treatment > control) via Monte Carlo simulation.
///
/// # Panics
/// Panics if the underlying Beta distributions cannot be sampled (should not happen with valid models).
#[must_use]
pub fn probability_treatment_beats_control<R: Rng>(
    control: &BinaryModel,
    treatment: &BinaryModel,
    rng: &mut R,
    n_samples: usize,
) -> f64 {
    let posterior_control = control.posterior();
    let posterior_treatment = treatment.posterior();

    let samples_control = posterior_control.sample_n(rng, n_samples);
    let samples_treatment = posterior_treatment.sample_n(rng, n_samples);

    let wins: usize = samples_control
        .iter()
        .zip(samples_treatment.iter())
        .filter(|(c, t)| t > c)
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

/// Computes the relative lift distribution ((treatment-control)/control) via Monte Carlo.
///
/// # Panics
///
/// Panics if the underlying Beta distributions cannot be sampled.
#[must_use]
pub fn lift_distribution<R: Rng>(
    control: &BinaryModel,
    treatment: &BinaryModel,
    rng: &mut R,
    n_samples: usize,
    ci_level: f64,
) -> LiftResult {
    let posterior_control = control.posterior();
    let posterior_treatment = treatment.posterior();

    let samples_control = posterior_control.sample_n(rng, n_samples);
    let samples_treatment = posterior_treatment.sample_n(rng, n_samples);

    let lift_samples: Vec<f64> = samples_control
        .iter()
        .zip(samples_treatment.iter())
        .map(|(c, t)| {
            if *c == 0.0 {
                0.0
            } else {
                (t - c) / c
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

/// Recommends Ship/DontShip/KeepTesting based on P(treatment > control) and threshold.
///
/// # Panics
///
/// Panics if the underlying Beta distributions cannot be sampled.
#[must_use]
pub fn recommend_decision<R: Rng>(
    control: &BinaryModel,
    treatment: &BinaryModel,
    rng: &mut R,
    config: &DecisionConfig,
) -> DecisionResult {
    let prob_treatment_wins =
        probability_treatment_beats_control(control, treatment, rng, config.n_samples);
    let prob_control_wins = 1.0 - prob_treatment_wins;

    let (recommendation, confidence) = if prob_treatment_wins >= config.confidence_threshold {
        (Decision::Ship, prob_treatment_wins)
    } else if prob_control_wins >= config.confidence_threshold {
        (Decision::DontShip, prob_control_wins)
    } else {
        (Decision::KeepTesting, prob_treatment_wins.max(prob_control_wins))
    };

    DecisionResult {
        recommendation,
        confidence,
        probability_treatment_wins: prob_treatment_wins,
    }
}
