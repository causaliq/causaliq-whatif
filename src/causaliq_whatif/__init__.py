"""
causaliq-whatif: Template package for CausalIQ repos
"""

__version__ = "0.1.0"
__author__ = "CausalIQ"
__email__ = "info@causaliq.org"

# Package metadata
__title__ = "causaliq-whatif"
__description__ = "Causal effect estimation and counterfactual reasoning."

__url__ = "https://github.com/causaliq/causaliq-whatif"
__license__ = "MIT"

# Version tuple for programmatic access
VERSION = tuple(map(int, __version__.split(".")))

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "VERSION",
]
