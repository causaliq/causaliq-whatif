# CausalIQ WhatIf User Guide

`causaliq-whatif` provides **causal effect estimation and
counterfactual reasoning** over causal graphs and structural causal
models (SCMs). It exposes a single harmonised API across several
mature backends (DoWhy / EconML, pyAgrum, and — in later releases —
deep SCMs and tractable probabilistic circuits), so that users can
phrase causal queries in one consistent way regardless of the engine
that ultimately answers them.

This guide introduces the core concepts, the public API, and the
parameters used across the CLI, Python, and CausalIQ Workflow
interfaces.

---

## Concepts

A causal query has three things attached to it:

1. **A causal model** — either a *causal graph* (a DAG, possibly with
   latent variables) together with observational data, or a fully
   specified *structural causal model* (functional mechanisms plus
   noise distributions for every variable).
2. **A query type** — observational, interventional, or
   counterfactual.
3. **A target** — the variables and the quantity of interest (e.g. a
   marginal, a conditional, an average treatment effect, a
   counterfactual sample).

What you can ask depends on what you provide:

| You have...                              | You can ask for...                                       |
|------------------------------------------|----------------------------------------------------------|
| Graph + data                             | Observational queries; interventional effects (ATE/CATE) |
| Graph + data + identifiability checking  | Symbolic identification formulae for $P(Y \mid do(X))$    |
| Fully fitted SCM                         | All of the above, plus counterfactuals and attribution    |

The harmonised API surfaces this distinction honestly: queries that
require an SCM raise a clear, typed error when called on a
graph-only model.

---

## Getting Started

### From Python

```python
from causaliq_whatif import load_model

# Load a causal model — graph + data, or a fully specified SCM.
model = load_model(
    graph="dag.graphml",
    data="data.csv",
)

# Observational query: P(Y | X = 1)
p_y = model.query("Y", given={"X": 1})

# Interventional query: P(Y | do(X = 1))
p_y_do = model.query("Y", do={"X": 1})

# Average treatment effect: E[Y | do(X=1)] - E[Y | do(X=0)]
ate = model.effect("Y", treatment="X", treated=1, control=0)

# Counterfactual (requires SCM): "What would Y have been for this
# unit if X had been 0 instead of the observed value?"
cf = model.counterfactual(
    "Y",
    evidence={"X": 1, "Z": 0.4, "Y": 3.2},
    do={"X": 0},
)
```

### From the command line

```bash
# Interventional query
cqwhif -g dag.graphml -i data.csv \
       --query Y --do X=1

# Average treatment effect
cqwhif -g dag.graphml -i data.csv \
       --effect Y --treatment X --treated 1 --control 0

# Counterfactual (SCM required)
cqwhif -s model.scm.json \
       --counterfactual Y --evidence X=1,Z=0.4,Y=3.2 --do X=0
```

### As a CausalIQ Workflow action

```yaml
steps:
  - name: "Estimate ATE of X on Y"
    uses: "causaliq-whatif"
    with:
      action: "estimate_effect"
      graph: "results/learnt_graph.graphml"
      data: "data.csv"
      outcome: "Y"
      treatment: "X"
      treated: 1
      control: 0
      output: "results/ate.json"
```

---

## The harmonised query API

The core abstraction is a `CausalModel` with four query methods.
Every backend implements the same surface; the model itself decides
which queries it can answer.

### `model.query(outcome, *, given=None, do=None, marginalise=None)`

Answer a probabilistic query over the model.

- `given={X: x, ...}` — observational conditioning.
- `do={X: x, ...}` — interventional conditioning (Pearl's
  $\text{do}$-operator).
- `marginalise=[Z, ...]` — variables to sum/integrate out.

Returns a `QueryResult` whose representation depends on the variable
type:

- Discrete outcome → a categorical distribution (`dict` or pandas
  `Series`).
- Continuous outcome → a sample-based or analytic distribution
  (`Distribution` object exposing `.mean()`, `.var()`, `.quantile()`,
  `.sample(n)`).

### `model.effect(outcome, *, treatment, treated, control, kind="ate", covariates=None)`

Estimate a causal effect.

- `kind` ∈ `{"ate", "att", "atu", "cate"}` — average, on the
  treated/untreated, or conditional.
- `covariates=...` — required for `cate`; defines the conditioning
  profile.

Returns an `EffectResult` with `.point_estimate`, `.std_error`,
`.confidence_interval`, and `.method` (the estimator used).

### `model.counterfactual(outcome, *, evidence, do, n_samples=None)`

Answer a unit-level counterfactual query.

- `evidence={X: x, ...}` — observed values for the unit.
- `do={X: x', ...}` — the hypothetical intervention.
- `n_samples` — for SCMs with continuous noise, the number of
  posterior samples to draw.

Returns a `CounterfactualResult` exposing the counterfactual
distribution (or point value, for deterministic discrete SCMs).

Raises `SCMRequiredError` when called on a graph-only model.

### `model.attribute(outcome, *, observed, kind="root_cause")`

Explain an outcome by attributing it to upstream variables.

- `kind="root_cause"` — root-cause analysis for an anomaly.
- `kind="shapley"` — Shapley-value feature relevance.
- `kind="mediation"` — direct/indirect effect decomposition.

Returns an `AttributionResult` with per-variable scores.

Raises `SCMRequiredError` when the chosen `kind` requires an SCM.

---

## Model construction

### `load_model(...)` — the main entry point

```python
load_model(
    graph=None,           # path | SDG | networkx.DiGraph
    data=None,            # path | DataFrame | causaliq Data
    scm=None,             # path | SCM object
    variable_types=None,  # dict | knowledge context file
    latents=None,         # iterable of latent variable names
    backend=None,         # explicit backend selection (optional)
)
```

You must supply *either*:

- `graph` (with optional `data`) — a **graph-based model**, or
- `scm` — a **structural causal model**.

If `backend` is not given, `causaliq-whatif` chooses one based on
variable types and query support (see
[Architecture](../architecture/overview.md)).

### Building an SCM

A graph can be promoted to an SCM by fitting causal mechanisms to
each node:

```python
from causaliq_whatif import fit_scm

scm = fit_scm(
    graph="dag.graphml",
    data="data.csv",
    mechanism="auto",   # or per-node dict
)

model = load_model(scm=scm)
model.counterfactual("Y", evidence={...}, do={...})
```

The `mechanism` argument selects a mechanism family per node
(`"linear"`, `"additive_noise"`, `"discrete_cpt"`, `"neural"`,
`"diffusion"`, `"spn"`, `"auto"`). The default `"auto"` picks based
on variable type and the active backend.

---

## Parameters

| Parameter          | CLI flag | Required | Description                                                              |
|--------------------|----------|----------|--------------------------------------------------------------------------|
| `graph`            | `-g`     | one of   | Causal graph (DAG, possibly with latents)                                |
| `scm`              | `-s`     | one of   | Fully specified structural causal model                                  |
| `data`             | `-i`     | No*      | Observational data (required for fitting and estimation, not for SCMs)   |
| `variable_types`   | `-T`     | No       | Variable type information (`CONTINUOUS`, `DISCRETE`, `BINARY`, ...)      |
| `latents`          | `-L`     | No       | Names of latent (unobserved) variables                                   |
| `backend`          | `-B`     | No       | Backend selection (`auto`, `pyagrum`, `dowhy`, `chirho`, `spn`, ...)     |
| `output`           | `-o`     | No       | Output file/folder/Workflow cache; if omitted, results are returned only |
| `seed`             | `-S`     | No       | Randomisation seed for sampling-based estimators                         |

\* `data` is required whenever `graph` is supplied without an SCM, or
whenever statistical estimation (e.g. ATE/CATE) is requested.

---

## Backends

`causaliq-whatif` is a harmonised front end. The supported backends
and the queries they can answer are documented in
[Architecture > Overview](../architecture/overview.md).

A short summary:

| Backend            | Strengths                                                        | Variable regime         |
|--------------------|------------------------------------------------------------------|-------------------------|
| `pyagrum`          | Exact discrete inference; symbolic do-calculus; latents          | Discrete                |
| `dowhy`            | Identification + statistical estimators + refutation             | Continuous / mixed      |
| `econml`           | CATE / heterogeneous effects (DML, DR, causal forests)           | Continuous / mixed      |
| `causalpy`         | Quasi-experimental (synthetic controls, DiD, RDD)                | Continuous / time series|
| `chirho`           | Probabilistic-programming SCMs; deep counterfactuals             | Continuous / mixed      |
| `diffusion`        | Deep SCMs for high-dimensional continuous data                   | Continuous              |
| `spn`              | Tractable counterfactuals via probabilistic circuits             | Discrete / mixed        |

The default backend is chosen automatically. Users may override it
with the `backend` parameter when they have specific requirements.

---

## Output formats

Query results may be returned as Python objects, written to disk, or
stored in a CausalIQ Workflow cache:

|                  | File           | Workflow cache         | Python object         |
|------------------|----------------|------------------------|-----------------------|
| Query result     | JSON           | compressed JSON        | `QueryResult`         |
| Effect estimate  | JSON           | compressed JSON        | `EffectResult`        |
| Counterfactual   | JSON           | compressed JSON        | `CounterfactualResult`|
| Attribution      | JSON           | compressed JSON        | `AttributionResult`   |
| Metadata         | JSON file      | compressed JSON        | `dict`                |
| Trace            | JSON file      | compressed JSON        | `list[dict]`          |

All results include a `metadata` block recording the backend used,
the identification strategy, the estimator, the hyperparameters
(default and explicit), and the elapsed time — sufficient for a
human or LLM to understand how the answer was produced.

---

## Errors and identifiability

The API surfaces causal-inference-specific failure modes as typed
exceptions:

- `NotIdentifiableError` — the requested interventional or
  counterfactual quantity cannot be identified from the supplied
  graph (e.g. unobserved confounding with no valid adjustment).
- `SCMRequiredError` — the query requires a fully specified SCM but
  only a graph + data was supplied.
- `UnsupportedQueryError` — the chosen backend cannot answer this
  query class for the given variable types.

Where possible the exception messages include the smallest reason
(missing adjustment set, missing mechanism for node $X$, etc.) and a
suggested remedy (supply more variables, fit an SCM, switch
backend).
