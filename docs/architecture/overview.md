# Architecture Overview

## CausalIQ Ecosystem

`causaliq-whatif` is a component of the overall
[CausalIQ ecosystem](https://causaliq.org/projects/ecosystem_architecture/).
It provides the **causal query** layer: given a causal model (a graph
plus data, or a fully specified SCM), it answers observational,
interventional, counterfactual, effect-estimation, and attribution
queries.

The package sits downstream of `causaliq-discovery` (which produces
the graph) and `causaliq-knowledge` (which can supply or constrain
it), and upstream of `causaliq-policy` (planned — sequential
decision-making over the same world models). Shared low-level
abstractions — graphs, SCMs, distributions, intervention semantics
— live in `causaliq-core`.

```
causaliq-discovery ──┐
                     ├──►  causaliq-whatif  ──►  causaliq-policy
causaliq-knowledge ──┘            │
                                  ▼
                          causaliq-core  (SCM, graph, distributions)
```

---

## Architectural Principles

### Single harmonised query API, many backends

Users interact with one façade — `CausalModel` — exposing the
methods `query`, `effect`, `counterfactual`, and `attribute`. The
backend that actually answers the query is selected automatically
from the model's variable types, the query class, and the
identifiability requirements, and may be overridden explicitly.

This mirrors `causaliq-discovery`'s registry-based plug-in
architecture: each backend is described by a `BackendSpec` and
implemented by a `BackendAdapter` subclass, registered with a
`BackendRegistry` at import time. Adapter registration is
conditional on the backing package being importable, so missing
optional dependencies produce a clear `BackendUnavailableError`
rather than an `ImportError` at user-call time.

### Honest separation of graph-based and SCM-based queries

The API surfaces — but does not paper over — the fundamental
distinction between what a *causal graph* can answer (interventional
distributions, identifiable effects) and what a *structural causal
model* can answer (unit-level counterfactuals, attribution,
mechanism-level reasoning). Graph-only models raise
`SCMRequiredError` for SCM-only queries with an actionable message
(e.g. "fit an SCM with `fit_scm(...)` or load a fully specified
SCM").

### Capability negotiation, not silent fallback

When several backends could in principle answer a query, the
selection is deterministic and transparent: each `BackendAdapter`
declares the `(query_class, variable_regime, identifiability_class)`
tuples it supports, and the registry picks the highest-ranked match.
The selected backend, the estimand, the estimator, and any
identification formula are always recorded in the result metadata.

### Visualisation is decoupled from any specific backend

Graph and SCM visualisation goes through the `causaliq-core`
DOT-emitting layer and a WASM Graphviz renderer bundled by
`causaliq-whatif`. The package does **not** depend on a system
`dot` install, and does not import any backend's notebook helpers
(e.g. `pyAgrum.lib.notebook`). See
[Design Note: Visualisation](visualisation.md).

---

## Architecture Components

### `load_model` / `fit_scm`

The two public constructors.

- `load_model(graph=..., data=..., scm=..., ...)` — builds a
  `CausalModel` façade, validates inputs, normalises data
  (delegating to `causaliq-core`'s `Data` object), and selects an
  initial backend.
- `fit_scm(graph=..., data=..., mechanism=..., ...)` — fits causal
  mechanisms to each node of a graph to produce an `SCM` object
  (defined in `causaliq-core`).

### `CausalModel`

The user-facing façade. Holds:

- A reference to the underlying graph and/or SCM (both
  `causaliq-core` types).
- The selected `BackendAdapter`.
- A cache of computed identification formulae.

Methods (`query`, `effect`, `counterfactual`, `attribute`) translate
the harmonised arguments into a `QuerySpec`, dispatch to the
backend, and wrap the result in the appropriate `*Result` dataclass.

### `BackendRegistry`

Class-level registry mapping backend names to `(BackendSpec,
BackendAdapter)` pairs. Backend specs include:

- The query classes supported (`observational`, `interventional`,
  `counterfactual`, `ate`, `cate`, `attribution`, ...).
- The supported variable regimes (`discrete`, `continuous`,
  `mixed`).
- Identification capability (`adjustment_set`, `id_algorithm`,
  `iv`, `frontdoor`, `none`).
- Whether an SCM is required.

### `BackendAdapter`

Abstract base class. Concrete subclasses translate the
harmonised `QuerySpec` into the backend's native call and wrap the
result. Initial adapters:

- `PyAgrumAdapter` — discrete BNs; exact inference; symbolic
  identification; counterfactuals via twin networks. **Does not
  import** `pyAgrum.lib.notebook` or shell out to `dot`.
- `DoWhyAdapter` — graph + data effect estimation; identification;
  refutation tests.
- `EconMLAdapter` — CATE / heterogeneous effects (often composed
  with `DoWhyAdapter`).
- `CausalPyAdapter` — quasi-experimental designs.
- `ChirhoAdapter` — Pyro-backed probabilistic-programming SCMs.

Planned (post v1.0):

- `DiffusionAdapter` — causal diffusion / normalising-flow SCMs
  for high-dimensional continuous data.
- `SPNAdapter` — interventional sum–product networks /
  probabilistic circuits, enabling tractable counterfactual queries
  on discrete and mixed data.

### `QuerySpec` and `*Result` dataclasses

`QuerySpec` is the internal, backend-agnostic representation of a
query (outcome, given, do, marginalise, kind, ...). `*Result`
dataclasses (`QueryResult`, `EffectResult`,
`CounterfactualResult`, `AttributionResult`) hold the value plus a
common metadata block (backend, estimand, estimator,
hyperparameters, elapsed time) and an optional trace.

### `WhatIfActionProvider`

Workflow integration. Subclasses `CausalIQActionProvider` from
`causaliq-workflow` and registers `estimate_effect`, `query`,
`counterfactual`, and `attribute` actions. When `causaliq-workflow`
is not installed, the provider is replaced by a stub class and
`WORKFLOW_AVAILABLE` is set to `False` (same pattern as
`causaliq-discovery`).

---

## Dependencies on `causaliq-core`

Several abstractions are core to *both* `causaliq-whatif` and
`causaliq-policy`, and therefore belong in `causaliq-core` rather
than in either consumer:

- **`SCM`** — a structural causal model: graph + per-node mechanism
  + per-node exogenous noise distribution. Supports `sample`,
  `intervene`, and `abduct` (posterior over noise given evidence).
- **Intervention semantics** — `do(X = x)` as a model
  transformation; soft / stochastic interventions; conditional
  interventions.
- **Distributions** — a small `Distribution` protocol covering
  discrete and continuous cases (`pmf`/`pdf`, `mean`, `var`,
  `quantile`, `sample`).
- **Mechanism families** — linear, additive-noise, discrete CPT,
  neural, diffusion, SPN — registered through a `MechanismRegistry`
  in `causaliq-core` so that fitting and sampling are uniform.
- **Identifiability primitives** — graph operations needed by
  do-calculus (backdoor / frontdoor adjustment set search, ADMG
  conversions, c-component decomposition).

See [Design Note: SCM in causaliq-core](scm-in-core.md) for the
proposed core module structure and migration plan.

---

## Data Flow

### Effect estimation (graph + data)

```
graph + data + outcome + treatment
        │
        ▼
  load_model() ──► CausalModel (backend = DoWhyAdapter)
        │
        ▼
  model.effect(...) ──► QuerySpec
        │
        ▼
  DoWhyAdapter.identify() ──► estimand (adjustment / IV / frontdoor)
        │
        ▼
  DoWhyAdapter.estimate() ──► EconML estimator (DML, DR, ...)
        │
        ▼
  DoWhyAdapter.refute() ──► refutation tests
        │
        ▼
  EffectResult(value, std_error, ci, metadata, trace)
```

### Counterfactual (SCM)

```
scm + evidence + do
        │
        ▼
  load_model(scm=...) ──► CausalModel (backend selected from SCM type)
        │
        ▼
  model.counterfactual(...) ──► QuerySpec
        │
        ▼
  BackendAdapter.abduct()    ── posterior over exogenous noise
        │
        ▼
  BackendAdapter.intervene() ── apply do
        │
        ▼
  BackendAdapter.predict()   ── push counterfactual noise through SCM
        │
        ▼
  CounterfactualResult(distribution, metadata, trace)
```

---

## Roadmap alignment

The [Development Roadmap](../roadmap.md) sequences the architecture
above into concrete commits, beginning with the harmonised API and
the `pyAgrum` and `DoWhy` adapters in v1.0, the `causaliq-core` SCM
work in v1.1, and the deep-SCM / SPN backends in v2.0.
