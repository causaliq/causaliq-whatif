# CausalIQ WhatIf

<!-- add in coverage and CI badges when repo is public -->

![Python Versions](https://img.shields.io/badge/python-3.9%2C%203.10%2C%203.11%2C%203.12-blue)

## Welcome

Welcome to the documentation for **CausalIQ WhatIf** — part of the
[CausalIQ ecosystem](https://causaliq.org) for intelligent causal
analysis.

`causaliq-whatif` provides **causal effect estimation and
counterfactual reasoning** over causal graphs and structural causal
models (SCMs). It answers questions of the form:

- *What is the effect of intervening to set $X = x$ on outcome $Y$?*
- *Given that we observed $Y = y$ for unit $u$, what would $Y$ have
  been had $X$ been set to $x'$ instead?*
- *Which upstream variable is most responsible for an observed
  anomaly?*

---

## Overview

`causaliq-whatif` exposes a single, harmonised API for causal queries
that dispatches transparently to one of several mature backends —
including [DoWhy / EconML](https://www.pywhy.org/),
[pyAgrum](https://pyagrum.org), and (in later releases) deep
structural causal models based on normalising flows / diffusion and
tractable probabilistic circuits (sum–product networks).

This site provides detailed documentation, including the development
roadmap, user guide, architectural vision, design notes, and API
reference for users and contributors.

---

## Quickstart & Installation

For a quickstart guide and installation instructions, see the [README on GitHub](https://github.com/causaliq/causaliq-whatif#readme).

---

## Documentation Contents

- [Development Roadmap](roadmap.md): roadmap of upcoming features
- [User Guide](userguide/introduction.md): comprehensive user guide
- [Architecture](architecture/overview.md): overall architecture and design notes
- [API Reference](api/overview.md): complete reference for Python code
- [Development Guidelines](https://github.com/causaliq/causaliq-whatif/blob/main/CONTRIBUTING.md): CausalIQ guidelines for developers
- [Changelog](https://github.com/causaliq/causaliq-whatif/blob/main/CHANGELOG.md)
- [License](https://github.com/causaliq/causaliq-whatif/blob/main/LICENSE)

---

## Support & Community

- [GitHub Issues](https://github.com/causaliq/causaliq-whatif/issues): Report bugs or request features.
- [GitHub Discussions](https://github.com/causaliq/causaliq-whatif/discussions): Ask questions and join the community.

---

**Tip:**  
Use the navigation sidebar to explore the documentation.  
For the latest code and releases, visit the [causaliq-whatif GitHub repository](https://github.com/causaliq/causaliq-whatif).

---

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12  
**Default Python Version**: 3.11