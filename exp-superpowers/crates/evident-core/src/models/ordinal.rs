use crate::distributions::Dirichlet;

#[derive(Debug, Clone)]
pub struct OrdinalModel {
    prior: Dirichlet,
    counts: Vec<u64>,
}

impl OrdinalModel {
    /// # Panics
    /// Panics if prior dimension does not match counts length.
    #[must_use]
    pub fn new(prior: Dirichlet, counts: Vec<u64>) -> Self {
        assert_eq!(
            prior.k(),
            counts.len(),
            "prior dimension must match counts length"
        );
        Self { prior, counts }
    }

    #[must_use]
    pub fn with_uniform_prior(counts: Vec<u64>) -> Self {
        let k = counts.len();
        Self::new(Dirichlet::uniform(k), counts)
    }

    #[must_use]
    pub fn prior(&self) -> &Dirichlet {
        &self.prior
    }

    #[must_use]
    pub fn counts(&self) -> &[u64] {
        &self.counts
    }

    #[must_use]
    pub fn k(&self) -> usize {
        self.counts.len()
    }

    #[must_use]
    pub fn total(&self) -> u64 {
        self.counts.iter().sum()
    }

    #[must_use]
    #[allow(clippy::cast_precision_loss)]
    pub fn posterior(&self) -> Dirichlet {
        let alpha: Vec<f64> = self
            .prior
            .alpha()
            .iter()
            .zip(self.counts.iter())
            .map(|(a, c)| a + *c as f64)
            .collect();
        Dirichlet::new(alpha)
    }

    #[must_use]
    #[allow(clippy::cast_precision_loss)]
    pub fn observed_proportions(&self) -> Vec<f64> {
        let total = self.total() as f64;
        if total == 0.0 {
            vec![0.0; self.k()]
        } else {
            self.counts.iter().map(|c| *c as f64 / total).collect()
        }
    }
}
