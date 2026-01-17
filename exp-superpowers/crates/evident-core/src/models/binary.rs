use crate::distributions::Beta;

#[derive(Debug, Clone)]
pub struct BinaryModel {
    prior: Beta,
    successes: u64,
    trials: u64,
}

impl BinaryModel {
    /// # Panics
    /// Panics if successes exceeds trials.
    #[must_use]
    pub fn new(prior: Beta, successes: u64, trials: u64) -> Self {
        assert!(successes <= trials, "successes cannot exceed trials");
        Self {
            prior,
            successes,
            trials,
        }
    }

    #[must_use]
    pub fn with_uniform_prior(successes: u64, trials: u64) -> Self {
        Self::new(Beta::uniform(), successes, trials)
    }

    #[must_use]
    pub fn prior(&self) -> &Beta {
        &self.prior
    }

    #[must_use]
    pub fn successes(&self) -> u64 {
        self.successes
    }

    #[must_use]
    pub fn trials(&self) -> u64 {
        self.trials
    }

    #[must_use]
    pub fn failures(&self) -> u64 {
        self.trials - self.successes
    }

    #[must_use]
    #[allow(clippy::cast_precision_loss)]
    pub fn posterior(&self) -> Beta {
        Beta::new(
            self.prior.alpha() + self.successes as f64,
            self.prior.beta() + self.failures() as f64,
        )
    }

    #[must_use]
    #[allow(clippy::cast_precision_loss)]
    pub fn observed_rate(&self) -> f64 {
        if self.trials == 0 {
            0.0
        } else {
            self.successes as f64 / self.trials as f64
        }
    }
}
