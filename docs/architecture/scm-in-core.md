# Design Note: SCM Abstractions in `causaliq-core`

**Status**: Proposal
**Owners**: causaliq-whatif, causaliq-policy
**Last updated**: May 29, 2026

## Context

Both `causaliq-whatif` (causal queries) and the planned
`causaliq-policy` (sequential decision-making under causal world
models) need a shared notion of a **structural causal model (SCM)**
and its operations:

- Sampling from the observational distribution.
- Applying an intervention $\text{do}(X = x)$ as a model
  transformation (including soft / stochastic interventions).
- Abduction — computing the posterior over exogenous noise given
  evidence — for counterfactuals.
- A uniform way of attaching per-node *mechanisms* and *noise
  distributions* of varying functional form.

If these live in either consumer package they will be duplicated or
create a circular dependency once `causaliq-policy` needs to
evaluate counterfactual rollouts during planning. They therefore
belong in `causaliq-core`.

## Proposed `causaliq-core` modules

```
causaliq_core/
├── graph/          # already present (SDG, DAG, ADMG, CPDAG, MAG, PAG)
├── data/           # already present (Data, variable types)
├── scm/            # NEW
│   ├── model.py            # SCM dataclass; sample/intervene/abduct
│   ├── mechanism.py        # Mechanism protocol; MechanismRegistry
│   ├── mechanisms/         # built-in mechanism families
│   │   ├── linear.py
│   │   ├── additive_noise.py
│   │   ├── discrete_cpt.py
│   │   ├── neural.py       # later release
│   │   ├── diffusion.py    # later release
│   │   └── spn.py          # later release
│   ├── noise.py            # exogenous-noise distributions
│   └── intervene.py        # hard, soft, conditional interventions
├── distributions/  # NEW (small Distribution protocol)
└── identifiability/ # NEW (do-calculus primitives shared by adapters)
    ├── adjustment.py       # backdoor / frontdoor adjustment-set search
    ├── id_algorithm.py     # Tian & Pearl ID algorithm (later)
    └── admg.py             # ADMG / latent-projection utilities
```

## Public surface (sketch)

```python
from causaliq_core.scm import SCM, Mechanism, register_mechanism
from causaliq_core.distributions import Distribution
from causaliq_core.identifiability import find_adjustment_set

scm = SCM(graph=dag, mechanisms={...}, noise={...})

# Sample observational distribution
samples = scm.sample(n=1000, seed=42)

# Apply intervention
scm_do = scm.intervene({"X": 1})

# Abduction: posterior over exogenous noise given evidence
posterior = scm.abduct(evidence={"X": 1, "Y": 3.2, "Z": 0.4})

# Counterfactual = abduct → intervene → sample/push
cf_samples = scm.intervene({"X": 0}).predict(noise=posterior.sample(100))
```

## Migration plan

Sequenced as a precursor to `causaliq-whatif` v1.1:

1. **causaliq-core v0.9** — add `Distribution` protocol and discrete
   / continuous standard implementations.
2. **causaliq-core v0.10** — add `SCM`, `Mechanism`, `MechanismRegistry`,
   and the `linear`, `additive_noise`, `discrete_cpt` mechanism
   families. Add `intervene` (hard interventions). No abduction yet.
3. **causaliq-core v0.11** — add `abduct` for tractable mechanism
   families (linear-Gaussian, discrete) and the
   `identifiability.adjustment` module.
4. **causaliq-core v1.0** — stable SCM API; `id_algorithm` and full
   ADMG support follow in a later minor release.

`causaliq-whatif` v1.0 depends only on the graph + data side of
`causaliq-core` (already present). The full SCM API is needed only
when `fit_scm` / `model.counterfactual` / `model.attribute` are
implemented in `causaliq-whatif` v1.1 (see roadmap).

## Out of scope for this note

- Neural / diffusion / SPN mechanism implementations — these are
  added incrementally as the corresponding `causaliq-whatif`
  backends land.
- Policy-specific abstractions (MDP/POMDP wrappers, expected free
  energy) — these belong in `causaliq-policy` and are not needed
  by `causaliq-whatif`.
