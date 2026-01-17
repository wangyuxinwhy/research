/// Computes the equal-tailed credible interval for the given samples.
///
/// # Panics
///
/// Panics if `samples` is empty or if `level` is not in [0, 1].
#[must_use]
pub fn credible_interval(samples: &[f64], level: f64) -> (f64, f64) {
    assert!(!samples.is_empty(), "samples must not be empty");
    assert!(
        (0.0..=1.0).contains(&level),
        "level must be between 0 and 1"
    );

    let mut sorted = samples.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let n = sorted.len();
    #[allow(clippy::cast_precision_loss)]
    let tail = (1.0 - level) / 2.0;
    #[allow(clippy::cast_precision_loss, clippy::cast_possible_truncation, clippy::cast_sign_loss)]
    let lower_idx = (tail * n as f64).floor() as usize;
    #[allow(clippy::cast_precision_loss, clippy::cast_possible_truncation, clippy::cast_sign_loss)]
    let upper_idx = ((1.0 - tail) * n as f64).ceil() as usize - 1;

    (sorted[lower_idx], sorted[upper_idx.min(n - 1)])
}

/// Computes the median of the given samples.
///
/// # Panics
///
/// Panics if `samples` is empty.
#[must_use]
pub fn median(samples: &[f64]) -> f64 {
    assert!(!samples.is_empty(), "samples must not be empty");

    let mut sorted = samples.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let n = sorted.len();
    if n.is_multiple_of(2) {
        f64::midpoint(sorted[n / 2 - 1], sorted[n / 2])
    } else {
        sorted[n / 2]
    }
}

/// Computes the arithmetic mean of the given samples.
///
/// # Panics
///
/// Panics if `samples` is empty.
#[must_use]
#[allow(clippy::cast_precision_loss)]
pub fn mean(samples: &[f64]) -> f64 {
    assert!(!samples.is_empty(), "samples must not be empty");
    samples.iter().sum::<f64>() / samples.len() as f64
}
