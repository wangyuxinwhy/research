use rand::Rng;
use rand_distr::{Beta as BetaDist, Distribution};

#[derive(Debug, Clone, Copy)]
pub struct Beta {
    alpha: f64,
    beta: f64,
}

impl Beta {
    /// # Panics
    /// Panics if alpha or beta is not positive.
    #[must_use]
    pub fn new(alpha: f64, beta: f64) -> Self {
        assert!(alpha > 0.0, "alpha must be positive");
        assert!(beta > 0.0, "beta must be positive");
        Self { alpha, beta }
    }

    #[must_use]
    pub fn uniform() -> Self {
        Self::new(1.0, 1.0)
    }

    #[must_use]
    pub fn alpha(&self) -> f64 {
        self.alpha
    }

    #[must_use]
    pub fn beta(&self) -> f64 {
        self.beta
    }

    #[must_use]
    pub fn mean(&self) -> f64 {
        self.alpha / (self.alpha + self.beta)
    }

    #[must_use]
    pub fn variance(&self) -> f64 {
        let sum = self.alpha + self.beta;
        (self.alpha * self.beta) / (sum * sum * (sum + 1.0))
    }

    /// # Panics
    /// Panics if the underlying distribution cannot be created (should not happen with valid Beta).
    #[must_use]
    pub fn sample<R: Rng>(&self, rng: &mut R) -> f64 {
        let dist = BetaDist::new(self.alpha, self.beta).unwrap();
        dist.sample(rng)
    }

    /// # Panics
    /// Panics if the underlying distribution cannot be created (should not happen with valid Beta).
    #[must_use]
    pub fn sample_n<R: Rng>(&self, rng: &mut R, n: usize) -> Vec<f64> {
        let dist = BetaDist::new(self.alpha, self.beta).unwrap();
        (0..n).map(|_| dist.sample(rng)).collect()
    }
}
