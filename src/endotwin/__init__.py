"""ENDO-TWIN: a mechanistic MaBoSS model of human endometrial hormonal regulation.

The package is organised so that the regulatory network can be used on its own:

* :mod:`endotwin.model` loads the executable network, its rule variants and its
  compartment interface, and renders MaBoSS text. It knows nothing about
  protocols, data or figures.
* :mod:`endotwin.structure` computes exact structural facts (fixed points,
  composed functions, aliases) by exhaustive enumeration.
* :mod:`endotwin.protocols` and :mod:`endotwin.simulate` run sequential
  hormonal protocols with MaBoSS.
* :mod:`endotwin.regulatory_unit` is the per-cell interface a future multiscale
  coupling would call (docs/architecture/future_multiscale_extension.md).
* :mod:`endotwin.observations`, :mod:`endotwin.predictions` and
  :mod:`endotwin.data_interfaces` hold the model-data contract, the WP2/WP4
  prediction-freezing workflow and the planned experimental data interfaces.

MaBoSS probabilities are simulated trajectory frequencies under stated rules,
rates and initial conditions. They are not concentrations, not cell fractions and
not clinical probabilities, and MaBoSS time is not experimental time.
"""

DEFAULT_MODEL_VERSION = "endotwin-v0.1.0"

__all__ = ["DEFAULT_MODEL_VERSION"]
