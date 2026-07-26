# Patient personalization and validation

## Choose the least invasive mapping

Prefer, in order:

1. initial-state distribution;
2. node clamp with strong evidence;
3. relative transition-rate modifier with kinetic support;
4. rule or topology change with patient-specific mechanistic evidence.

Abundance alone usually supports context or uncertainty, not a unique Boolean
state or rate.

## Binarization

Pre-specify source field and unit, normalization and batch handling, reference
population, threshold method, uncertainty band, missingness handling,
sensitivity variants, and whether outcomes were hidden during threshold
selection.

Do not force uncertain values to 0 or 1. Use alternative variants or
probabilistic initial conditions.

## Prevent circular validation

Partition evidence by role:

- topology/rule curation;
- patient personalization;
- parameter calibration;
- validation.

The same phenotype can be used for calibration or validation, not both, unless
the analysis explicitly uses a valid resampling design and labels the result.

## Sensitivity matrix

At minimum, cross plausible thresholds, uncertain rules/signs, initial-state
distributions, rate scenarios, and multiple seeds or trajectory counts. Report
which perturbation effects keep direction and material magnitude across the
matrix.

## Validation targets

Prefer independent baseline phenotypes, time-course ordering, genetic or
pharmacologic perturbations, measurements not used for personalization, held-out
patients, and external cohorts. Record the scoring rule before comparison.
