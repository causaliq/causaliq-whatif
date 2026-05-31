# Design Note: Visualisation

**Status**: Proposal
**Last updated**: May 29, 2026

## Context

Several candidate backends (notably `pyAgrum`) ship their own
visualisation helpers that depend on a **system installation of
Graphviz** (`dot` on `PATH`) and pull large notebook dependencies
into the import surface. `causaliq-whatif` deliberately avoids this:

- It is awkward to require a system binary in a pip-installable
  Python package, especially on Windows.
- `pyAgrum.lib.notebook` imports `matplotlib`, `IPython`, etc. at
  import time, which would bloat `causaliq-whatif`'s base
  dependencies.
- Different backends have different visualisation conventions; the
  CausalIQ ecosystem wants a single, consistent look.

## Decision

1. **Never import a backend's notebook helpers** from
   `causaliq-whatif`. In particular, no module under
   `causaliq_whatif` imports `pyAgrum.lib.notebook`,
   `pyAgrum.lib.image`, or any equivalent.
2. **Use each backend's DOT-emitting interface only**
   (`bn.toDot()`, `cm.toDot()`, etc.) and render in a
   `causaliq-whatif` visualisation module.
3. **Render via a WASM Graphviz** runtime (e.g. `@hpcc-js/wasm` in
   notebooks, `wasmtime-py` + the Graphviz WASM module for pure
   Python contexts). No system `dot` install required.
4. **Implement `_repr_mimebundle_`** on `CausalModel` so that
   notebook rendering "just works" without users calling helpers.
5. **Post-process DOT** to apply consistent CausalIQ styling
   (treatment / outcome / latent colouring, do-edge styling,
   posterior overlays).

## Out of scope

- Reproducing pyAgrum's bar-chart-in-node inference visualisations
  in v1.0. If desired later, build them by computing marginals,
  rendering small SVG bar charts, and embedding them in
  HTML-labelled Graphviz nodes — but only on demand.
