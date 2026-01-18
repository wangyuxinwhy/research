# Evident - Bayesian A/B Testing Library Design

## Overview

A Bayesian statistics library for product A/B testing decisions. Built with Rust core for computational correctness and Python API for user-friendliness.

**Why Bayesian over frequentist?**
- Answers "What's the probability B is better?" directly
- No p-value misinterpretation
- Natural incorporation of prior knowledge
- Early stopping without statistical penalty

## Use Case

**Domain:** AI customer service optimization

**Target Metrics:**
| Metric | Type | Description |
|--------|------|-------------|
| Human handoff rate | Binary | Lower is better |
| Satisfaction rate | Binary | 4-5 stars / total |
| Reply quality score | Ordinal (0-3) | Four-tier quality rating |
| High-quality reply rate | Binary | Score 2-3 / total |

## Core Features

1. **P(B > A)** - Probability that treatment beats control
2. **Lift distribution** - Effect size with credible intervals
3. **Decision recommendation** - Ship / Don't Ship / Keep Testing

## Project Structure

```
evident/
├── crates/
│   └── evident-core/         # Rust core library
│       ├── src/
│       │   ├── lib.rs
│       │   ├── distributions/ # Beta, Dirichlet
│       │   ├── models/        # Binary, Ordinal
│       │   ├── inference/     # Posterior, sampling
│       │   └── metrics/       # Decision metrics
│       └── Cargo.toml
├── evident/                   # Python package
│   ├── __init__.py
│   ├── _core.pyi             # Type stubs for Rust bindings
│   ├── experiment.py         # High-level API
│   └── results.py            # Result objects
├── tests/
│   ├── rust/
│   └── python/
├── pyproject.toml
└── Cargo.toml                # Workspace
```

## Rust Core Design

### Distributions (`distributions/`)

```rust
pub struct Beta {
    alpha: f64,
    beta: f64,
}

pub struct Dirichlet {
    alpha: Vec<f64>,
}
```

### Models (`models/`)

```rust
pub struct BinaryModel {
    prior: Beta,
    successes: u64,
    trials: u64,
}

impl BinaryModel {
    pub fn posterior(&self) -> Beta {
        Beta {
            alpha: self.prior.alpha + self.successes as f64,
            beta: self.prior.beta + (self.trials - self.successes) as f64,
        }
    }
}

pub struct OrdinalModel {
    prior: Dirichlet,
    counts: Vec<u64>,
}

impl OrdinalModel {
    pub fn posterior(&self) -> Dirichlet {
        // Dirichlet(α₀ + c₀, α₁ + c₁, ...)
    }
}
```

### Inference (`inference/`)

- `sample(n: usize) -> Vec<f64>` - Monte Carlo sampling from posterior
- `credible_interval(level: f64) -> (f64, f64)` - Credible interval computation

### Metrics (`metrics/`)

```rust
pub fn probability_b_beats_a(
    model_a: &impl Model,
    model_b: &impl Model,
    samples: usize,
) -> f64

pub struct LiftResult {
    pub mean: f64,
    pub median: f64,
    pub credible_interval: (f64, f64),
    pub samples: Option<Vec<f64>>,
}

pub enum Decision {
    Ship,
    DontShip,
    KeepTesting,
}

pub struct DecisionResult {
    pub recommendation: Decision,
    pub confidence: f64,
    pub expected_remaining_samples: Option<u64>,
}
```

## Python API Design

### Basic Usage

```python
from evident import Experiment

# Binary metric
exp = Experiment.binary(
    control={"trials": 1000, "successes": 150},
    treatment={"trials": 1000, "successes": 120},
    direction="lower_is_better",
)

result = exp.analyze()

result.probability_b_wins   # 0.942
result.lift.mean            # -0.20
result.lift.ci              # (-0.283, -0.105)
result.recommendation       # Decision.SHIP
```

### Ordinal Metric

```python
exp = Experiment.ordinal(
    control={"counts": [50, 150, 500, 300]},
    treatment={"counts": [30, 120, 480, 370]},
)

result = exp.analyze()
```

### Configuration

```python
from evident import Experiment, Beta

exp = Experiment.binary(
    control={...},
    treatment={...},
    prior=Beta(1, 1),              # Default: uninformative
    direction="lower_is_better",
    min_detectable_effect=0.01,
    confidence_threshold=0.95,
)
```

### Result Object

```python
@dataclass(frozen=True)
class AnalysisResult:
    probability_b_wins: float
    lift: LiftEstimate
    recommendation: Decision
    posterior_a: Distribution
    posterior_b: Distribution

@dataclass(frozen=True)
class LiftEstimate:
    mean: float
    median: float
    ci: tuple[float, float]

    def ci_excludes_zero(self) -> bool:
        return self.ci[0] > 0 or self.ci[1] < 0
```

## Configuration

### pyproject.toml

```toml
[build-system]
requires = ["maturin>=1.0"]
build-backend = "maturin"

[project]
name = "evident"
requires-python = ">=3.14"
dependencies = []

[tool.maturin]
features = ["pyo3/extension-module"]

[tool.ruff]
target-version = "py314"
line-length = 88

[tool.ruff.lint]
select = ["ALL"]
ignore = ["D1", "ANN101", "ANN102"]

[tool.basedpyright]
pythonVersion = "3.14"
typeCheckingMode = "all"
```

### Cargo.toml (workspace)

```toml
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
all = "deny"
pedantic = "deny"
```

## Testing Strategy

### Rust Tests
- Distribution sampling correctness (statistical tests)
- Numerical stability with extreme parameters
- Deterministic results with fixed seed

### Python Tests
- API contract validation
- End-to-end scenarios with known results
- Error handling for invalid inputs

### Golden Tests
- Pre-computed results verified against third-party tools
- Regression prevention

## Future Considerations

- Real-time streaming updates
- Web interface for operations team
- Multi-armed bandit extension
- Automatic sample size estimation
