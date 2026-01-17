use approx::assert_relative_eq;
use evident_core::distributions::Beta;
use evident_core::models::BinaryModel;

#[test]
fn binary_model_posterior_with_uniform_prior() {
    let model = BinaryModel::new(Beta::uniform(), 10, 100);
    let posterior = model.posterior();

    // Beta(1,1) + 10 successes, 90 failures = Beta(11, 91)
    assert_relative_eq!(posterior.alpha(), 11.0);
    assert_relative_eq!(posterior.beta(), 91.0);
}

#[test]
fn binary_model_posterior_with_informative_prior() {
    let prior = Beta::new(5.0, 5.0);
    let model = BinaryModel::new(prior, 20, 50);
    let posterior = model.posterior();

    // Beta(5,5) + 20 successes, 30 failures = Beta(25, 35)
    assert_relative_eq!(posterior.alpha(), 25.0);
    assert_relative_eq!(posterior.beta(), 35.0);
}
