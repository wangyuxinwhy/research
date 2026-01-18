# Evident Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Bayesian A/B testing library with Rust core and Python API.

**Architecture:** Rust handles all statistical computation (distributions, sampling, inference). Python provides thin ergonomic wrapper via PyO3. All math in Rust, all UX in Python.

**Tech Stack:** Rust 2021, PyO3, maturin, Python 3.14, uv, ruff, basedpyright

---

## Task 1: Project Structure Setup

**Files:**
- Create: `Cargo.toml` (workspace root)
- Create: `crates/evident-core/Cargo.toml`
- Create: `crates/evident-core/src/lib.rs`
- Create: `pyproject.toml`
- Create: `evident/__init__.py`

**Step 1: Create Rust workspace Cargo.toml**

```toml
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"

[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
all = "deny"
pedantic = "deny"
```

**Step 2: Create evident-core crate Cargo.toml**

```toml
[package]
name = "evident-core"
version.workspace = true
edition.workspace = true
license.workspace = true

[lints]
workspace = true

[dependencies]
rand = "0.8"
rand_distr = "0.4"

[dev-dependencies]
approx = "0.5"
```

**Step 3: Create evident-core lib.rs stub**

```rust
pub mod distributions;
pub mod models;
pub mod inference;
pub mod metrics;
```

**Step 4: Create module stubs**

Create `crates/evident-core/src/distributions/mod.rs`:
```rust
mod beta;
mod dirichlet;

pub use beta::Beta;
pub use dirichlet::Dirichlet;
```

Create `crates/evident-core/src/distributions/beta.rs`:
```rust
// TODO: implement
```

Create `crates/evident-core/src/distributions/dirichlet.rs`:
```rust
// TODO: implement
```

Create `crates/evident-core/src/models/mod.rs`:
```rust
mod binary;
mod ordinal;

pub use binary::BinaryModel;
pub use ordinal::OrdinalModel;
```

Create `crates/evident-core/src/models/binary.rs`:
```rust
// TODO: implement
```

Create `crates/evident-core/src/models/ordinal.rs`:
```rust
// TODO: implement
```

Create `crates/evident-core/src/inference/mod.rs`:
```rust
// TODO: implement
```

Create `crates/evident-core/src/metrics/mod.rs`:
```rust
// TODO: implement
```

**Step 5: Verify Rust builds**

Run: `cargo build`
Expected: Build succeeds with warnings about empty files

**Step 6: Create pyproject.toml**

```toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"

[project]
name = "evident"
requires-python = ">=3.14"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: Implementation :: CPython",
]
dynamic = ["version"]

[tool.maturin]
features = ["pyo3/extension-module"]
module-name = "evident._core"

[tool.ruff]
target-version = "py314"
line-length = 88

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D1", "ANN101", "ANN102", "COM812", "ISC001"]

[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "all"
```

**Step 7: Create Python package stub**

Create `evident/__init__.py`:
```python
from evident.experiment import Experiment
from evident.results import AnalysisResult, Decision, LiftEstimate

__all__ = ["Experiment", "AnalysisResult", "Decision", "LiftEstimate"]
```

Create `evident/experiment.py`:
```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from evident.results import AnalysisResult


class Experiment:
    pass
```

Create `evident/results.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Decision(Enum):
    SHIP = auto()
    DONT_SHIP = auto()
    KEEP_TESTING = auto()


@dataclass(frozen=True, slots=True)
class LiftEstimate:
    mean: float
    median: float
    ci: tuple[float, float]


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    probability_b_wins: float
    lift: LiftEstimate
    recommendation: Decision
```

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: scaffold project structure

- Rust workspace with evident-core crate
- Python package with maturin build
- Module stubs for distributions, models, inference, metrics"
```

---

## Task 2: Beta Distribution

**Files:**
- Modify: `crates/evident-core/src/distributions/beta.rs`
- Create: `crates/evident-core/tests/beta_tests.rs`

**Step 1: Write failing test for Beta creation**

Create `crates/evident-core/tests/beta_tests.rs`:
```rust
use approx::assert_relative_eq;
use evident_core::distributions::Beta;

#[test]
fn beta_creation() {
    let beta = Beta::new(2.0, 3.0);
    assert_relative_eq!(beta.alpha(), 2.0);
    assert_relative_eq!(beta.beta(), 3.0);
}

#[test]
fn beta_mean() {
    let beta = Beta::new(2.0, 3.0);
    // Mean of Beta(2,3) = 2/(2+3) = 0.4
    assert_relative_eq!(beta.mean(), 0.4);
}

#[test]
fn beta_variance() {
    let beta = Beta::new(2.0, 3.0);
    // Var of Beta(2,3) = 2*3 / ((2+3)^2 * (2+3+1)) = 6/150 = 0.04
    assert_relative_eq!(beta.variance(), 0.04);
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test beta_tests`
Expected: FAIL with "cannot find Beta"

**Step 3: Implement Beta struct**

Replace `crates/evident-core/src/distributions/beta.rs`:
```rust
use rand::Rng;
use rand_distr::{Beta as BetaDist, Distribution};

#[derive(Debug, Clone, Copy)]
pub struct Beta {
    alpha: f64,
    beta: f64,
}

impl Beta {
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

    #[must_use]
    pub fn sample<R: Rng>(&self, rng: &mut R) -> f64 {
        let dist = BetaDist::new(self.alpha, self.beta).unwrap();
        dist.sample(rng)
    }

    #[must_use]
    pub fn sample_n<R: Rng>(&self, rng: &mut R, n: usize) -> Vec<f64> {
        let dist = BetaDist::new(self.alpha, self.beta).unwrap();
        (0..n).map(|_| dist.sample(rng)).collect()
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test beta_tests`
Expected: PASS (3 tests)

**Step 5: Add sampling test**

Add to `crates/evident-core/tests/beta_tests.rs`:
```rust
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn beta_sampling_distribution() {
    let beta = Beta::new(2.0, 5.0);
    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let samples = beta.sample_n(&mut rng, 10000);

    let sample_mean: f64 = samples.iter().sum::<f64>() / samples.len() as f64;
    // Mean should be close to theoretical: 2/(2+5) ≈ 0.286
    assert_relative_eq!(sample_mean, beta.mean(), epsilon = 0.01);
}
```

Update `crates/evident-core/Cargo.toml` dev-dependencies:
```toml
[dev-dependencies]
approx = "0.5"
rand_chacha = "0.3"
```

**Step 6: Run test to verify it passes**

Run: `cargo test --test beta_tests`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: implement Beta distribution

- Creation with alpha/beta parameters
- Mean and variance calculations
- Sampling via rand_distr"
```

---

## Task 3: Dirichlet Distribution

**Files:**
- Modify: `crates/evident-core/src/distributions/dirichlet.rs`
- Create: `crates/evident-core/tests/dirichlet_tests.rs`

**Step 1: Write failing test for Dirichlet**

Create `crates/evident-core/tests/dirichlet_tests.rs`:
```rust
use approx::assert_relative_eq;
use evident_core::distributions::Dirichlet;

#[test]
fn dirichlet_creation() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    assert_eq!(dir.alpha().len(), 3);
    assert_relative_eq!(dir.alpha()[0], 1.0);
    assert_relative_eq!(dir.alpha()[1], 2.0);
    assert_relative_eq!(dir.alpha()[2], 3.0);
}

#[test]
fn dirichlet_mean() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    let mean = dir.mean();
    // Mean_i = alpha_i / sum(alpha) = [1/6, 2/6, 3/6]
    assert_relative_eq!(mean[0], 1.0 / 6.0);
    assert_relative_eq!(mean[1], 2.0 / 6.0);
    assert_relative_eq!(mean[2], 3.0 / 6.0);
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test dirichlet_tests`
Expected: FAIL with "cannot find Dirichlet"

**Step 3: Implement Dirichlet struct**

Replace `crates/evident-core/src/distributions/dirichlet.rs`:
```rust
use rand::Rng;
use rand_distr::{Dirichlet as DirichletDist, Distribution};

#[derive(Debug, Clone)]
pub struct Dirichlet {
    alpha: Vec<f64>,
}

impl Dirichlet {
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

    #[must_use]
    pub fn sample<R: Rng>(&self, rng: &mut R) -> Vec<f64> {
        let dist = DirichletDist::new(&self.alpha).unwrap();
        dist.sample(rng).to_vec()
    }

    #[must_use]
    pub fn sample_n<R: Rng>(&self, rng: &mut R, n: usize) -> Vec<Vec<f64>> {
        let dist = DirichletDist::new(&self.alpha).unwrap();
        (0..n).map(|_| dist.sample(rng).to_vec()).collect()
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test dirichlet_tests`
Expected: PASS (2 tests)

**Step 5: Add sampling test**

Add to `crates/evident-core/tests/dirichlet_tests.rs`:
```rust
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn dirichlet_sampling_sums_to_one() {
    let dir = Dirichlet::new(vec![1.0, 2.0, 3.0]);
    let mut rng = ChaCha8Rng::seed_from_u64(42);

    for _ in 0..100 {
        let sample = dir.sample(&mut rng);
        let sum: f64 = sample.iter().sum();
        assert_relative_eq!(sum, 1.0, epsilon = 1e-10);
    }
}

#[test]
fn dirichlet_sampling_distribution() {
    let dir = Dirichlet::new(vec![2.0, 3.0, 5.0]);
    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let samples = dir.sample_n(&mut rng, 10000);

    let theoretical_mean = dir.mean();
    let sample_mean: Vec<f64> = (0..dir.k())
        .map(|i| samples.iter().map(|s| s[i]).sum::<f64>() / samples.len() as f64)
        .collect();

    for i in 0..dir.k() {
        assert_relative_eq!(sample_mean[i], theoretical_mean[i], epsilon = 0.01);
    }
}
```

**Step 6: Run test to verify it passes**

Run: `cargo test --test dirichlet_tests`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: implement Dirichlet distribution

- Creation with alpha vector
- Mean calculation
- Sampling via rand_distr"
```

---

## Task 4: Binary Model

**Files:**
- Modify: `crates/evident-core/src/models/binary.rs`
- Create: `crates/evident-core/tests/binary_model_tests.rs`

**Step 1: Write failing test for BinaryModel**

Create `crates/evident-core/tests/binary_model_tests.rs`:
```rust
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
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test binary_model_tests`
Expected: FAIL with "cannot find BinaryModel"

**Step 3: Implement BinaryModel**

Replace `crates/evident-core/src/models/binary.rs`:
```rust
use crate::distributions::Beta;

#[derive(Debug, Clone)]
pub struct BinaryModel {
    prior: Beta,
    successes: u64,
    trials: u64,
}

impl BinaryModel {
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
    pub fn posterior(&self) -> Beta {
        Beta::new(
            self.prior.alpha() + self.successes as f64,
            self.prior.beta() + self.failures() as f64,
        )
    }

    #[must_use]
    pub fn observed_rate(&self) -> f64 {
        if self.trials == 0 {
            0.0
        } else {
            self.successes as f64 / self.trials as f64
        }
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test binary_model_tests`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement BinaryModel with conjugate posterior

- Beta prior with observed successes/trials
- Posterior computation via conjugate update"
```

---

## Task 5: Ordinal Model

**Files:**
- Modify: `crates/evident-core/src/models/ordinal.rs`
- Create: `crates/evident-core/tests/ordinal_model_tests.rs`

**Step 1: Write failing test for OrdinalModel**

Create `crates/evident-core/tests/ordinal_model_tests.rs`:
```rust
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
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test ordinal_model_tests`
Expected: FAIL with "cannot find OrdinalModel"

**Step 3: Implement OrdinalModel**

Replace `crates/evident-core/src/models/ordinal.rs`:
```rust
use crate::distributions::Dirichlet;

#[derive(Debug, Clone)]
pub struct OrdinalModel {
    prior: Dirichlet,
    counts: Vec<u64>,
}

impl OrdinalModel {
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
    pub fn observed_proportions(&self) -> Vec<f64> {
        let total = self.total() as f64;
        if total == 0.0 {
            vec![0.0; self.k()]
        } else {
            self.counts.iter().map(|c| *c as f64 / total).collect()
        }
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test ordinal_model_tests`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement OrdinalModel with Dirichlet posterior

- Dirichlet prior with observed category counts
- Posterior computation via conjugate update"
```

---

## Task 6: Credible Interval Calculation

**Files:**
- Modify: `crates/evident-core/src/inference/mod.rs`
- Create: `crates/evident-core/tests/inference_tests.rs`

**Step 1: Write failing test for credible interval**

Create `crates/evident-core/tests/inference_tests.rs`:
```rust
use approx::assert_relative_eq;
use evident_core::inference::credible_interval;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn credible_interval_95() {
    let mut rng = ChaCha8Rng::seed_from_u64(42);
    // Generate samples from a known distribution
    let samples: Vec<f64> = (0..10000)
        .map(|i| (i as f64) / 10000.0)
        .collect();

    let (lower, upper) = credible_interval(&samples, 0.95);

    // For uniform [0,1), 95% CI should be approximately [0.025, 0.975]
    assert_relative_eq!(lower, 0.025, epsilon = 0.01);
    assert_relative_eq!(upper, 0.975, epsilon = 0.01);
}

#[test]
fn credible_interval_90() {
    let samples: Vec<f64> = (0..10000)
        .map(|i| (i as f64) / 10000.0)
        .collect();

    let (lower, upper) = credible_interval(&samples, 0.90);

    // For uniform [0,1), 90% CI should be approximately [0.05, 0.95]
    assert_relative_eq!(lower, 0.05, epsilon = 0.01);
    assert_relative_eq!(upper, 0.95, epsilon = 0.01);
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test inference_tests`
Expected: FAIL with "cannot find credible_interval"

**Step 3: Implement credible_interval**

Replace `crates/evident-core/src/inference/mod.rs`:
```rust
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
    let tail = (1.0 - level) / 2.0;
    let lower_idx = (tail * n as f64).floor() as usize;
    let upper_idx = ((1.0 - tail) * n as f64).ceil() as usize - 1;

    (sorted[lower_idx], sorted[upper_idx.min(n - 1)])
}

#[must_use]
pub fn median(samples: &[f64]) -> f64 {
    assert!(!samples.is_empty(), "samples must not be empty");

    let mut sorted = samples.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let n = sorted.len();
    if n % 2 == 0 {
        (sorted[n / 2 - 1] + sorted[n / 2]) / 2.0
    } else {
        sorted[n / 2]
    }
}

#[must_use]
pub fn mean(samples: &[f64]) -> f64 {
    assert!(!samples.is_empty(), "samples must not be empty");
    samples.iter().sum::<f64>() / samples.len() as f64
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test inference_tests`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement credible interval and summary statistics

- Quantile-based credible interval calculation
- Median and mean helper functions"
```

---

## Task 7: P(B > A) Metric

**Files:**
- Modify: `crates/evident-core/src/metrics/mod.rs`
- Create: `crates/evident-core/tests/metrics_tests.rs`

**Step 1: Write failing test for probability_b_beats_a**

Create `crates/evident-core/tests/metrics_tests.rs`:
```rust
use approx::assert_relative_eq;
use evident_core::distributions::Beta;
use evident_core::models::BinaryModel;
use evident_core::metrics::probability_b_beats_a;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

#[test]
fn probability_b_clearly_better() {
    let model_a = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let model_b = BinaryModel::with_uniform_prior(200, 1000); // 20% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // B is clearly better, probability should be very high
    assert!(prob > 0.99);
}

#[test]
fn probability_a_clearly_better() {
    let model_a = BinaryModel::with_uniform_prior(200, 1000); // 20% rate
    let model_b = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // A is clearly better, probability should be very low
    assert!(prob < 0.01);
}

#[test]
fn probability_similar_rates() {
    let model_a = BinaryModel::with_uniform_prior(150, 1000);
    let model_b = BinaryModel::with_uniform_prior(155, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let prob = probability_b_beats_a(&model_a, &model_b, &mut rng, 100_000);

    // Similar rates, probability should be around 0.5-0.7
    assert!(prob > 0.4 && prob < 0.8);
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test metrics_tests`
Expected: FAIL with "cannot find probability_b_beats_a"

**Step 3: Implement probability_b_beats_a**

Replace `crates/evident-core/src/metrics/mod.rs`:
```rust
use rand::Rng;

use crate::models::BinaryModel;

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

    wins as f64 / n_samples as f64
}
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test metrics_tests`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement probability_b_beats_a metric

- Monte Carlo estimation of P(B > A)
- Samples from posterior distributions"
```

---

## Task 8: Lift Distribution

**Files:**
- Modify: `crates/evident-core/src/metrics/mod.rs`
- Modify: `crates/evident-core/tests/metrics_tests.rs`

**Step 1: Write failing test for lift_distribution**

Add to `crates/evident-core/tests/metrics_tests.rs`:
```rust
use evident_core::metrics::lift_distribution;

#[test]
fn lift_distribution_positive() {
    let model_a = BinaryModel::with_uniform_prior(100, 1000); // 10% rate
    let model_b = BinaryModel::with_uniform_prior(150, 1000); // 15% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&model_a, &model_b, &mut rng, 100_000, 0.95);

    // Relative lift = (0.15 - 0.10) / 0.10 = 0.50 (50%)
    assert_relative_eq!(lift.mean, 0.50, epsilon = 0.05);
    assert!(lift.ci.0 > 0.0); // Lower bound positive
}

#[test]
fn lift_distribution_negative() {
    let model_a = BinaryModel::with_uniform_prior(150, 1000); // 15% rate
    let model_b = BinaryModel::with_uniform_prior(100, 1000); // 10% rate

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let lift = lift_distribution(&model_a, &model_b, &mut rng, 100_000, 0.95);

    // Relative lift = (0.10 - 0.15) / 0.15 = -0.33 (-33%)
    assert_relative_eq!(lift.mean, -0.33, epsilon = 0.05);
    assert!(lift.ci.1 < 0.0); // Upper bound negative
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test metrics_tests`
Expected: FAIL with "cannot find lift_distribution"

**Step 3: Implement LiftResult and lift_distribution**

Add to `crates/evident-core/src/metrics/mod.rs`:
```rust
use crate::inference::{credible_interval, mean, median};

#[derive(Debug, Clone)]
pub struct LiftResult {
    pub mean: f64,
    pub median: f64,
    pub ci: (f64, f64),
    pub samples: Vec<f64>,
}

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
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test metrics_tests`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement lift_distribution metric

- Relative lift calculation (B-A)/A
- Mean, median, and credible interval"
```

---

## Task 9: Decision Recommendation

**Files:**
- Modify: `crates/evident-core/src/metrics/mod.rs`
- Modify: `crates/evident-core/tests/metrics_tests.rs`

**Step 1: Write failing test for recommend_decision**

Add to `crates/evident-core/tests/metrics_tests.rs`:
```rust
use evident_core::metrics::{recommend_decision, Decision, DecisionConfig};

#[test]
fn decision_ship_when_clearly_better() {
    let model_a = BinaryModel::with_uniform_prior(100, 1000);
    let model_b = BinaryModel::with_uniform_prior(200, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&model_a, &model_b, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::Ship));
    assert!(result.confidence > 0.95);
}

#[test]
fn decision_dont_ship_when_clearly_worse() {
    let model_a = BinaryModel::with_uniform_prior(200, 1000);
    let model_b = BinaryModel::with_uniform_prior(100, 1000);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&model_a, &model_b, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::DontShip));
}

#[test]
fn decision_keep_testing_when_uncertain() {
    let model_a = BinaryModel::with_uniform_prior(10, 100);
    let model_b = BinaryModel::with_uniform_prior(12, 100);

    let mut rng = ChaCha8Rng::seed_from_u64(42);
    let config = DecisionConfig::default();
    let result = recommend_decision(&model_a, &model_b, &mut rng, &config);

    assert!(matches!(result.recommendation, Decision::KeepTesting));
}
```

**Step 2: Run test to verify it fails**

Run: `cargo test --test metrics_tests`
Expected: FAIL with "cannot find recommend_decision"

**Step 3: Implement Decision types and recommend_decision**

Add to `crates/evident-core/src/metrics/mod.rs`:
```rust
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

#[must_use]
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
```

**Step 4: Run test to verify it passes**

Run: `cargo test --test metrics_tests`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: implement recommend_decision metric

- Ship/DontShip/KeepTesting recommendation
- Configurable confidence threshold"
```

---

## Task 10: PyO3 Bindings

**Files:**
- Create: `crates/evident-py/Cargo.toml`
- Create: `crates/evident-py/src/lib.rs`
- Modify: `Cargo.toml` (workspace)

**Step 1: Create evident-py crate Cargo.toml**

Create `crates/evident-py/Cargo.toml`:
```toml
[package]
name = "evident-py"
version.workspace = true
edition.workspace = true
license.workspace = true

[lints]
workspace = true

[lib]
name = "_core"
crate-type = ["cdylib"]

[dependencies]
evident-core = { path = "../evident-core" }
pyo3 = { version = "0.22", features = ["extension-module"] }
rand = "0.8"
```

**Step 2: Update workspace Cargo.toml**

Update `Cargo.toml`:
```toml
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "MIT"

[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
all = "deny"
pedantic = "deny"
```

**Step 3: Implement PyO3 bindings**

Create `crates/evident-py/src/lib.rs`:
```rust
use evident_core::distributions::Beta as CoreBeta;
use evident_core::metrics::{
    lift_distribution as core_lift, probability_b_beats_a as core_prob_b_beats_a,
    recommend_decision as core_recommend, Decision as CoreDecision, DecisionConfig, LiftResult,
};
use evident_core::models::BinaryModel as CoreBinaryModel;
use pyo3::prelude::*;
use rand::SeedableRng;
use rand::rngs::StdRng;

#[pyclass]
#[derive(Clone)]
pub struct Beta {
    inner: CoreBeta,
}

#[pymethods]
impl Beta {
    #[new]
    #[pyo3(signature = (alpha=1.0, beta=1.0))]
    fn new(alpha: f64, beta: f64) -> Self {
        Self {
            inner: CoreBeta::new(alpha, beta),
        }
    }

    #[getter]
    fn alpha(&self) -> f64 {
        self.inner.alpha()
    }

    #[getter]
    fn beta(&self) -> f64 {
        self.inner.beta()
    }

    fn mean(&self) -> f64 {
        self.inner.mean()
    }
}

#[pyclass]
pub struct BinaryModel {
    inner: CoreBinaryModel,
}

#[pymethods]
impl BinaryModel {
    #[new]
    #[pyo3(signature = (successes, trials, prior=None))]
    fn new(successes: u64, trials: u64, prior: Option<Beta>) -> Self {
        let prior = prior.map_or_else(CoreBeta::uniform, |p| p.inner);
        Self {
            inner: CoreBinaryModel::new(prior, successes, trials),
        }
    }

    fn posterior(&self) -> Beta {
        Beta {
            inner: self.inner.posterior(),
        }
    }

    fn observed_rate(&self) -> f64 {
        self.inner.observed_rate()
    }
}

#[pyclass]
#[derive(Clone)]
pub struct Lift {
    #[pyo3(get)]
    mean: f64,
    #[pyo3(get)]
    median: f64,
    #[pyo3(get)]
    ci: (f64, f64),
}

#[pyclass]
#[derive(Clone, Copy)]
pub enum Decision {
    Ship,
    DontShip,
    KeepTesting,
}

#[pyclass]
#[derive(Clone)]
pub struct AnalysisResult {
    #[pyo3(get)]
    probability_b_wins: f64,
    #[pyo3(get)]
    lift: Lift,
    #[pyo3(get)]
    recommendation: Decision,
}

#[pyfunction]
#[pyo3(signature = (model_a, model_b, n_samples=100000, ci_level=0.95, confidence_threshold=0.95, seed=None))]
fn analyze_binary(
    model_a: &BinaryModel,
    model_b: &BinaryModel,
    n_samples: usize,
    ci_level: f64,
    confidence_threshold: f64,
    seed: Option<u64>,
) -> AnalysisResult {
    let mut rng = match seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    let prob_b_wins = core_prob_b_beats_a(&model_a.inner, &model_b.inner, &mut rng, n_samples);
    let lift_result = core_lift(&model_a.inner, &model_b.inner, &mut rng, n_samples, ci_level);

    let config = DecisionConfig {
        confidence_threshold,
        n_samples,
    };
    let decision_result = core_recommend(&model_a.inner, &model_b.inner, &mut rng, &config);

    let recommendation = match decision_result.recommendation {
        CoreDecision::Ship => Decision::Ship,
        CoreDecision::DontShip => Decision::DontShip,
        CoreDecision::KeepTesting => Decision::KeepTesting,
    };

    AnalysisResult {
        probability_b_wins: prob_b_wins,
        lift: Lift {
            mean: lift_result.mean,
            median: lift_result.median,
            ci: lift_result.ci,
        },
        recommendation,
    }
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Beta>()?;
    m.add_class::<BinaryModel>()?;
    m.add_class::<Lift>()?;
    m.add_class::<Decision>()?;
    m.add_class::<AnalysisResult>()?;
    m.add_function(wrap_pyfunction!(analyze_binary, m)?)?;
    Ok(())
}
```

**Step 4: Build and verify**

Run: `maturin develop`
Expected: Build succeeds, module importable

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: add PyO3 bindings for evident-core

- Beta, BinaryModel wrapped for Python
- analyze_binary function for full analysis"
```

---

## Task 11: Python High-Level API

**Files:**
- Modify: `evident/experiment.py`
- Modify: `evident/results.py`
- Create: `tests/python/test_experiment.py`

**Step 1: Write failing test for Experiment API**

Create `tests/python/test_experiment.py`:
```python
import pytest
from evident import Experiment, Decision


def test_binary_experiment_basic():
    exp = Experiment.binary(
        control={"trials": 1000, "successes": 100},
        treatment={"trials": 1000, "successes": 150},
    )
    result = exp.analyze()

    assert 0.0 <= result.probability_b_wins <= 1.0
    assert result.lift.mean > 0
    assert result.recommendation == Decision.SHIP


def test_binary_experiment_lower_is_better():
    exp = Experiment.binary(
        control={"trials": 1000, "successes": 150},
        treatment={"trials": 1000, "successes": 100},
        direction="lower_is_better",
    )
    result = exp.analyze()

    assert result.probability_b_wins > 0.95
    assert result.recommendation == Decision.SHIP
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/python/test_experiment.py -v`
Expected: FAIL

**Step 3: Implement Experiment class**

Replace `evident/experiment.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from evident import _core
from evident.results import AnalysisResult, Decision, LiftEstimate


@dataclass(frozen=True, slots=True)
class BinaryData:
    trials: int
    successes: int


class Experiment:
    @classmethod
    def binary(
        cls,
        *,
        control: dict[str, int],
        treatment: dict[str, int],
        direction: Literal["higher_is_better", "lower_is_better"] = "higher_is_better",
        confidence_threshold: float = 0.95,
    ) -> BinaryExperiment:
        return BinaryExperiment(
            control=BinaryData(**control),
            treatment=BinaryData(**treatment),
            direction=direction,
            confidence_threshold=confidence_threshold,
        )


class BinaryExperiment:
    def __init__(
        self,
        *,
        control: BinaryData,
        treatment: BinaryData,
        direction: Literal["higher_is_better", "lower_is_better"],
        confidence_threshold: float,
    ) -> None:
        self._control = control
        self._treatment = treatment
        self._direction = direction
        self._confidence_threshold = confidence_threshold

    def analyze(self, *, seed: int | None = None) -> AnalysisResult:
        if self._direction == "lower_is_better":
            model_a = _core.BinaryModel(
                self._control.trials - self._control.successes,
                self._control.trials,
            )
            model_b = _core.BinaryModel(
                self._treatment.trials - self._treatment.successes,
                self._treatment.trials,
            )
        else:
            model_a = _core.BinaryModel(self._control.successes, self._control.trials)
            model_b = _core.BinaryModel(self._treatment.successes, self._treatment.trials)

        raw = _core.analyze_binary(
            model_a,
            model_b,
            confidence_threshold=self._confidence_threshold,
            seed=seed,
        )

        return AnalysisResult(
            probability_b_wins=raw.probability_b_wins,
            lift=LiftEstimate(
                mean=raw.lift.mean,
                median=raw.lift.median,
                ci=raw.lift.ci,
            ),
            recommendation=Decision(raw.recommendation.name),
        )
```

**Step 4: Update results.py**

Replace `evident/results.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    SHIP = "Ship"
    DONT_SHIP = "DontShip"
    KEEP_TESTING = "KeepTesting"


@dataclass(frozen=True, slots=True)
class LiftEstimate:
    mean: float
    median: float
    ci: tuple[float, float]

    def ci_excludes_zero(self) -> bool:
        return self.ci[0] > 0 or self.ci[1] < 0


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    probability_b_wins: float
    lift: LiftEstimate
    recommendation: Decision

    def is_significant(self, threshold: float = 0.95) -> bool:
        return self.probability_b_wins > threshold or self.probability_b_wins < (1 - threshold)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/python/test_experiment.py -v`
Expected: PASS (2 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: implement Python high-level Experiment API

- Experiment.binary() factory method
- Support for higher_is_better/lower_is_better direction
- Clean AnalysisResult dataclass"
```

---

## Task 12: Final Integration Test

**Files:**
- Create: `tests/python/test_integration.py`

**Step 1: Write integration test**

Create `tests/python/test_integration.py`:
```python
from evident import Experiment, Decision


def test_customer_service_scenario():
    """Real scenario: testing new AI model for customer service."""
    # Control: 15% human handoff rate
    # Treatment: 12% human handoff rate (lower is better)
    exp = Experiment.binary(
        control={"trials": 5000, "successes": 750},
        treatment={"trials": 5000, "successes": 600},
        direction="lower_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_b_wins > 0.95
    assert result.lift.mean < 0  # Negative lift = fewer handoffs
    assert result.recommendation == Decision.SHIP


def test_satisfaction_rate_scenario():
    """Real scenario: testing satisfaction rate improvement."""
    # Control: 82% satisfaction (4-5 stars)
    # Treatment: 85% satisfaction
    exp = Experiment.binary(
        control={"trials": 2000, "successes": 1640},
        treatment={"trials": 2000, "successes": 1700},
        direction="higher_is_better",
    )

    result = exp.analyze(seed=42)

    assert result.probability_b_wins > 0.80
    assert result.lift.mean > 0


def test_inconclusive_small_sample():
    """Small sample should recommend keep testing."""
    exp = Experiment.binary(
        control={"trials": 50, "successes": 5},
        treatment={"trials": 50, "successes": 7},
    )

    result = exp.analyze(seed=42)

    assert result.recommendation == Decision.KEEP_TESTING
```

**Step 2: Run integration tests**

Run: `pytest tests/python/test_integration.py -v`
Expected: PASS (3 tests)

**Step 3: Run all tests**

Run: `cargo test && pytest tests/python/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add -A
git commit -m "test: add integration tests for real-world scenarios

- Customer service handoff rate test
- Satisfaction rate improvement test
- Small sample inconclusive test"
```

---

## Summary

**Total Tasks:** 12

**Commits:**
1. Project structure scaffold
2. Beta distribution
3. Dirichlet distribution
4. BinaryModel
5. OrdinalModel
6. Credible interval
7. P(B > A) metric
8. Lift distribution
9. Decision recommendation
10. PyO3 bindings
11. Python high-level API
12. Integration tests

**Not included (future work):**
- OrdinalModel Python bindings
- Web interface
- Real-time streaming
- Visualization helpers
