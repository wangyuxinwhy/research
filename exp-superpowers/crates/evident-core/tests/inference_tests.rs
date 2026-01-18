use approx::assert_relative_eq;
use evident_core::inference::credible_interval;

#[test]
fn credible_interval_95() {
    let samples: Vec<f64> = (0..10000).map(|i| f64::from(i) / 10000.0).collect();

    let (lower, upper) = credible_interval(&samples, 0.95);

    // For uniform [0,1), 95% CI should be approximately [0.025, 0.975]
    assert_relative_eq!(lower, 0.025, epsilon = 0.01);
    assert_relative_eq!(upper, 0.975, epsilon = 0.01);
}

#[test]
fn credible_interval_90() {
    let samples: Vec<f64> = (0..10000).map(|i| f64::from(i) / 10000.0).collect();

    let (lower, upper) = credible_interval(&samples, 0.90);

    // For uniform [0,1), 90% CI should be approximately [0.05, 0.95]
    assert_relative_eq!(lower, 0.05, epsilon = 0.01);
    assert_relative_eq!(upper, 0.95, epsilon = 0.01);
}
