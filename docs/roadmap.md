# CausalIQ WhatIf - Development Roadmap

**Last updated**: May 29, 2026

This project roadmap fits into the
[overall ecosystem roadmap](https://causaliq.org/projects/ecosystem_roadmap/).

`causaliq-whatif` is delivered in three major releases:

- **v1.0 Foundation** — harmonised query API; `pyAgrum` and `DoWhy`
  adapters; effect estimation, observational and interventional
  queries on graph-based models.
- **v1.1 SCMs and Counterfactuals** — `causaliq-core` SCM
  abstractions; `fit_scm`; counterfactual and attribution queries
  through `pyAgrum`, `DoWhy GCM`, and `chirho`.
- **v2.0 Deep and Tractable SCMs** — causal diffusion / normalising
  flow backend; interventional sum–product network backend;
  knowledge-guided identification.

Commits should be made in the order listed below; each must pass
all CI checks at 100% test coverage.

---

## 🎯 Under Development

### Release v1.0.0 Foundation

Harmonised query API and effect estimation across graph-based
backends. **No SCMs and no counterfactuals in this release** —
those land in v1.1 once the `causaliq-core` SCM work is complete.

---

#### Commit 1 — Public API skeleton: `load_model`, `CausalModel`, parameter validation

- `load_model` function in `src/causaliq_whatif/__init__.py` with
  the full parameter signature from the user guide.
- Validation of all parameter types, required/optional constraints,
  and value ranges; clear errors when neither `graph` nor `scm` is
  supplied.
- `CausalModel` façade class with `query`, `effect`,
  `counterfactual`, `attribute` method stubs raising
  `NotImplementedError` until adapters land.
- Typed exception hierarchy: `WhatIfError`,
  `NotIdentifiableError`, `SCMRequiredError`,
  `UnsupportedQueryError`, `BackendUnavailableError`.
- Unit tests for all validation paths and exception messages.

#### Commit 2 — `BackendSpec`, `BackendAdapter`, `BackendRegistry`

- `BackendAdapter` abstract base class with abstract methods
  `identify`, `estimate`, `query`, `counterfactual`, `attribute`,
  `supports(query_spec) -> bool`.
- `BackendSpec` dataclass capturing per-backend metadata: supported
  query classes, variable regimes, identification capability,
  whether an SCM is required, default hyperparameters.
- `BackendRegistry` mapping backend name → `(BackendSpec,
  BackendAdapter)`; spec registration is unconditional, adapter
  registration is conditional on importability of the backing
  package.
- Backend auto-selection algorithm: deterministic ranking over
  matching `(query_class, variable_regime, identifiability_class)`.
- Unit tests for registry lookups, auto-selection, and
  `BackendUnavailableError` paths.

#### Commit 3 — `QuerySpec` and `*Result` dataclasses; output serialisation

- `QuerySpec` internal dataclass (outcome, given, do, marginalise,
  kind, covariates).
- `QueryResult`, `EffectResult`, `CounterfactualResult`,
  `AttributionResult` dataclasses with a common `metadata` and
  `trace` block.
- `save(output)` methods writing JSON to disk; CausalIQ Workflow
  cache serialisation hook.
- Unit tests for serialisation round-trips and metadata schema.

#### Commit 4 — Data and graph input handling

- Accept graph as path (GraphML / DOT), `SDG` object, or
  `networkx.DiGraph`.
- Accept data as CSV path, `pandas.DataFrame`, or `causaliq-core`
  `Data` object; normalise to `Data` early using the same imputation
  rules as `causaliq-discovery`.
- `variable_types` validation against loaded graph nodes.
- `latents` parameter validated against graph node set.
- Functional tests using files from `tests/data/`.

#### Commit 5 — `PyAgrumAdapter`: observational queries

> **Prerequisite**: discrete-variable BN. Continuous and mixed data
> handled in later commits via `DoWhyAdapter` and (v1.1)
> `ChirhoAdapter`.

- `PyAgrumAdapter(BackendAdapter)` concrete implementation:
  - `convert_input`: graph + data → `pyAgrum.BayesNet` with CPTs
    learned from data (parameter learning, structure assumed
    given).
  - `query`: observational queries via `LazyPropagation`.
  - Strictly **does not import** `pyAgrum.lib.notebook` or
    `pyAgrum.lib.image` (see Design Note: Visualisation).
- Unit tests with mocked pyAgrum for the conversion logic.
- Functional tests against discrete benchmark networks (Asia,
  Sachs) verifying exact marginals.

#### Commit 6 — `PyAgrumAdapter`: interventional queries via `pyAgrum.causal`

- Extend `PyAgrumAdapter` with do-queries via `CausalModel`.
- Latents handled explicitly via the `latents` parameter and
  `pyAgrum`'s latent-variable support.
- Symbolic identification formula captured in result metadata
  (LaTeX string), where pyAgrum makes it available.
- `NotIdentifiableError` raised with the pyAgrum-reported reason.
- Functional tests against known interventional queries on
  benchmark networks.

#### Commit 7 — Visualisation module: WASM Graphviz rendering

- `causaliq_whatif.viz` module taking DOT strings (from any
  backend) and rendering SVG via a bundled WASM Graphviz runtime.
- DOT post-processing for CausalIQ styling: treatment / outcome /
  latent colouring; do-edge styling.
- `CausalModel._repr_mimebundle_` for notebook auto-render.
- **No system `dot` dependency**; CI verifies the package imports
  and renders on a clean environment without Graphviz installed.
- Unit tests for DOT post-processing; functional tests for SVG
  output on representative graphs.

#### Commit 8 — `DoWhyAdapter`: identification and effect estimation

> **Prerequisite**: DoWhy and EconML pinned in optional
> dependency group `dowhy`.

- `DoWhyAdapter(BackendAdapter)`:
  - `identify`: DoWhy effect-API identification; returns the
    estimand and the chosen identification strategy
    (adjustment / IV / frontdoor) into result metadata.
  - `estimate`: linear regression and propensity-score
    estimators in this commit; richer estimators in Commit 10.
  - `refute`: placebo, random-common-cause, subset, unobserved-
    confounder sensitivity refutation tests; results captured in
    `EffectResult.metadata["refutations"]`.
- Backend auto-selection prefers `DoWhyAdapter` for
  continuous / mixed data with effect queries.
- Functional tests on continuous benchmark datasets with known
  ATEs.

#### Commit 9 — `model.effect`: ATE / ATT / ATU via `DoWhyAdapter`

- Wire `CausalModel.effect(kind="ate"|"att"|"atu", ...)` through
  `DoWhyAdapter`.
- Result includes point estimate, standard error, confidence
  interval, identification strategy, estimator, and refutation
  outcomes.
- Functional tests against synthetic data with known true effects.

#### Commit 10 — `EconMLAdapter` composition: CATE / heterogeneous effects

- `EconMLAdapter` registered as a composed backend (uses
  `DoWhyAdapter` for identification, EconML estimators for
  estimation).
- Supports DML, DR-learner, causal forests, meta-learners.
- Wires `model.effect(kind="cate", covariates=...)`.
- Functional tests on synthetic data with known heterogeneous
  effects.

#### Commit 11 — `model.query` on graph + data via `DoWhyAdapter`

- Observational queries on continuous data via `DoWhyAdapter`
  (using sampling or analytic where available).
- Interventional queries via DoWhy identification + a default
  estimator producing samples from $P(Y \mid \text{do}(X))$.
- `NotIdentifiableError` raised when the do-query is not
  identifiable.

#### Commit 12 — CLI: `cqwhif` with `query`, `effect`, `counterfactual` commands

- `cqwhif` command-line interface mirroring the Python API.
- Sub-commands: `query`, `effect`, `counterfactual` (the last
  raises `SCMRequiredError` until v1.1).
- `cqwhif --help backend` and `cqwhif --help backend <name>` to
  list backends and their supported queries.
- End-to-end functional tests covering CLI invocations.

#### Commit 13 — `WhatIfActionProvider` workflow integration

- Register `estimate_effect`, `query`, `counterfactual`,
  `attribute` as CausalIQ workflow actions.
- Action parameter matrix support consistent with
  `causaliq-discovery` (matrices over treatment, outcome,
  backend, etc.).
- Output naming convention for matrix runs
  (`<base>/<action>/<treatment>_on_<outcome>/<backend>/`).
- Functional tests covering single-call and matrix-expansion.

#### Commit 14 — Closed-loop equivalence testing

- Test fixtures: pre-extracted JSON reference files in
  `tests/data/reference/` covering each `(backend, query, dataset,
  hyperparameters)` combination, derived offline.
- Integration tests: for each fixture, run the equivalent call
  through `CausalModel` and assert numerical equality (within
  tolerance) against the reference.
- Determinism verified: same `seed` reproduces identical results
  across platforms.

---

### Release v1.1.0 SCMs and Counterfactuals

> **Hard prerequisite**: `causaliq-core` v0.11 (SCM, mechanisms,
> abduction, identifiability primitives). See
> [Design Note: SCM in causaliq-core](architecture/scm-in-core.md)
> for the proposed core release sequence.

This release introduces structural causal models, counterfactual
queries, and attribution. Backends that previously only supported
graph + data queries are extended with their SCM-based APIs (e.g.
`DoWhy GCM`).

#### Commit 15 — `fit_scm` for tractable mechanism families

- `fit_scm(graph, data, mechanism="auto"|"linear"|"additive_noise"|"discrete_cpt", ...)`.
- Delegates to `causaliq-core` `MechanismRegistry`.
- Returns a `causaliq-core` `SCM` object.
- Functional tests on discrete and linear-Gaussian benchmark
  networks.

#### Commit 16 — `PyAgrumAdapter`: counterfactuals via twin networks

- Extend `PyAgrumAdapter` to handle SCM-backed counterfactual
  queries for discrete CPT mechanisms using pyAgrum's twin-network
  machinery.
- `model.counterfactual(...)` wired through.
- Functional tests on discrete benchmark networks against
  hand-computed counterfactuals.

#### Commit 17 — `DoWhyGCMAdapter`: counterfactuals and attribution

- New adapter wrapping `dowhy.gcm` for continuous / mixed SCMs.
- Supports counterfactual sampling (abduction → intervention →
  prediction) and `model.attribute(kind="root_cause"|"shapley")`.
- Refutation / sanity checks recorded in metadata.

#### Commit 18 — `ChirhoAdapter`: probabilistic-programming SCMs

- New adapter wrapping `chirho` (Pyro-based) for SCMs whose
  mechanisms are arbitrary probabilistic programs.
- Counterfactual queries via `chirho`'s intervene / observe
  effect handlers.
- Useful for SCMs with deep / non-tractable mechanisms.

#### Commit 19 — Mediation analysis

- `model.attribute(kind="mediation", mediator=...)` decomposing
  total effect into natural direct and natural indirect components.
- Initial implementation through `DoWhyGCMAdapter`; `PyAgrumAdapter`
  follow-up where exact computation is available.

#### Commit 20 — Sensitivity analysis to unmeasured confounding

- E-value / Cinelli–Hazlett-style sensitivity analysis for
  `EffectResult`.
- Wired through `DoWhyAdapter` and `EconMLAdapter`.

#### Commit 21 — CausalIQ Knowledge integration

- Accept `knowledge` parameter (consistent with `causaliq-discovery`)
  carrying required / forbidden edges, variable-type information,
  and known mechanism families.
- Used both for graph validation at `load_model` time and to
  constrain `fit_scm` mechanism choice.

---

### Release v2.0.0 Deep and Tractable SCMs

#### Commit 22 — `DiffusionAdapter`: causal normalising-flow / diffusion SCMs

- Adapter for a deep-SCM library (candidate: in-house
  implementation built on a normalising-flow / diffusion backbone,
  or `CausalNF` / `DECI` if their APIs stabilise).
- Supports observational, interventional, and counterfactual
  queries on high-dimensional continuous data.
- Counterfactuals via abduction in the latent / noise space.

#### Commit 23 — `SPNAdapter`: interventional sum–product networks

- Adapter for **interventional sum–product networks** (Zecevic et
  al.) providing **tractable** counterfactual queries on discrete
  and mixed data.
- Built on `SPFlow` or `pyjuice`.
- This is a candidate "CausalIQ-native" differentiator — tractable
  counterfactual inference is currently under-served by the
  ecosystem.

#### Commit 24 — Knowledge-guided identification

- Use `causaliq-knowledge` (and where available, LLM-derived
  background knowledge) to:
  - Suggest adjustment sets when the graph admits multiple.
  - Flag plausibility of identification assumptions.
  - Annotate `EffectResult.metadata` with knowledge provenance.

---

## ✅ Previous Releases

*See Git commit history for detailed implementation progress.*

- None yet — repository initialised from the CausalIQ repo template.

---

## 🛣️ Upcoming Releases (post-v2.0)

- **Quasi-experimental designs** — `CausalPyAdapter` for synthetic
  controls, difference-in-differences, regression discontinuity,
  interrupted time series.
- **Time-series counterfactuals** — for dynamic Bayesian networks
  and continuous-time SCMs.
- **Counterfactual fairness** auditing utilities, leveraging
  `causaliq-knowledge` for protected-attribute metadata.
- **Algorithmic recourse** (single-shot) — sits naturally in
  `whatif` as a counterfactual query class. Sequential / multi-step
  recourse is deferred to `causaliq-policy`.
