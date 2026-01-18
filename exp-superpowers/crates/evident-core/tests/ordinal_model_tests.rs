use approx::assert_relative_eq;
use evident_core::distributions::Dirichlet;
use evident_core::models::OrdinalModel;

#[test]
fn ordinal_model_posterior_with_uniform_prior() {
    let model = OrdinalModel::new(
        Dirichlet::uniform(4),
        vec![10, 20, 30, 40],
    );
    let posterior = model.posterior();

    // Dirichlet(1,1,1,1) + counts = Dirichlet(11, 21, 31, 41)
    let alpha = posterior.alpha();
    assert_relative_eq!(alpha[0], 11.0);
    assert_relative_eq!(alpha[1], 21.0);
    assert_relative_eq!(alpha[2], 31.0);
    assert_relative_eq!(alpha[3], 41.0);
}

#[test]
fn ordinal_model_category_count() {
    let model = OrdinalModel::new(
        Dirichlet::uniform(4),
        vec![10, 20, 30, 40],
    );
    assert_eq!(model.k(), 4);
    assert_eq!(model.total(), 100);
}
