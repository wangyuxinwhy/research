use evident_core::distributions::Beta as CoreBeta;
use evident_core::metrics::{
    lift_distribution as core_lift,
    probability_treatment_beats_control as core_prob_treatment_beats_control,
    recommend_decision as core_recommend, Decision as CoreDecision, DecisionConfig,
};
use evident_core::models::BinaryModel as CoreBinaryModel;
use pyo3::prelude::*;
use rand::rngs::StdRng;
use rand::SeedableRng;

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
    probability_treatment_wins: f64,
    #[pyo3(get)]
    lift: Lift,
    #[pyo3(get)]
    recommendation: Decision,
}

#[pyfunction]
#[pyo3(signature = (control, treatment, n_samples=100_000, ci_level=0.95, confidence_threshold=0.95, seed=None))]
fn analyze_binary(
    control: &BinaryModel,
    treatment: &BinaryModel,
    n_samples: usize,
    ci_level: f64,
    confidence_threshold: f64,
    seed: Option<u64>,
) -> AnalysisResult {
    let mut rng = match seed {
        Some(s) => StdRng::seed_from_u64(s),
        None => StdRng::from_entropy(),
    };

    let prob_treatment_wins =
        core_prob_treatment_beats_control(&control.inner, &treatment.inner, &mut rng, n_samples);
    let lift_result =
        core_lift(&control.inner, &treatment.inner, &mut rng, n_samples, ci_level);

    let config = DecisionConfig {
        confidence_threshold,
        n_samples,
    };
    let decision_result = core_recommend(&control.inner, &treatment.inner, &mut rng, &config);

    let recommendation = match decision_result.recommendation {
        CoreDecision::Ship => Decision::Ship,
        CoreDecision::DontShip => Decision::DontShip,
        CoreDecision::KeepTesting => Decision::KeepTesting,
    };

    AnalysisResult {
        probability_treatment_wins: prob_treatment_wins,
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
