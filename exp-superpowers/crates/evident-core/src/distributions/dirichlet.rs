use rand::Rng;
use rand_distr::{Dirichlet as DirichletDist, Distribution};

#[derive(Debug, Clone)]
pub struct Dirichlet {
    alpha: Vec<f64>,
}

impl Dirichlet {
    /// # Panics
    /// Panics if alpha is empty or contains non-positive values.
    #[must_use]
    pub fn new(alpha: Vec<f64>) -> Self {
        assert!(!alpha.is_empty(), "alpha must not be empty");
        assert!(
            alpha.iter().all(|&a| a > 0.0),
            "all alpha values must be positive"
        );
        Self { alpha }
    }

    #[must_use]
    pub fn uniform(k: usize) -> Self {
        Self::new(vec![1.0; k])
    }

    #[must_use]
    pub fn alpha(&self) -> &[f64] {
        &self.alpha
    }

    #[must_use]
    pub fn k(&self) -> usize {
        self.alpha.len()
    }

    #[must_use]
    pub fn mean(&self) -> Vec<f64> {
        let sum: f64 = self.alpha.iter().sum();
        self.alpha.iter().map(|a| a / sum).collect()
    }

    /// # Panics
    /// Panics if the underlying distribution cannot be created (should not happen with valid Dirichlet).
    #[must_use]
    pub fn sample<R: Rng>(&self, rng: &mut R) -> Vec<f64> {
        let dist = DirichletDist::new(&self.alpha).unwrap();
        dist.sample(rng).clone()
    }

    /// # Panics
    /// Panics if the underlying distribution cannot be created (should not happen with valid Dirichlet).
    #[must_use]
    pub fn sample_n<R: Rng>(&self, rng: &mut R, n: usize) -> Vec<Vec<f64>> {
        let dist = DirichletDist::new(&self.alpha).unwrap();
        (0..n).map(|_| dist.sample(rng).clone()).collect()
    }
}
