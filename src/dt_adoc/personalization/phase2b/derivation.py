"""Phase 2B: the pre-registered KLF12-high state-separation procedure.

WHAT THIS IS. The exact, executable form of the threshold derivation that the
Phase-2B rules pre-registration (`docs/phase2b/preregistration.json`) freezes by
sha256 BEFORE any candidate reference's KLF12 value is read. It is a pure
function of one input: per-cell KLF12 values and per-cell depths on the
decontX-corrected layer, grouped by independent reference donor. Nothing else
can reach it -- not an ADOC value, not an outcome, not a model output -- because
its signature admits nothing else and its imports are asserted by
`tests/unit/test_phase2b_contract.py`.

THE PROCEDURE (owner decisions D3/D4 of 2026-09-25). Per reference donor:

1. `x = count / depth * 1e4` (`count_per_10k`, exactly as Phase 2A's
   `per_cell_quantity` computes it for the ADOC cells). Detected := x > 0.
2. The Phase-1B two-component Gaussian mixture on log(detected x)
   (`dt_adoc.scrna.klf12_state.fit_two_component_mixture`, reused unchanged:
   deterministic, median-split initialisation, zeros excluded).
3. The separation qualifies only if ALL of:
   S1 exactly one posterior-0.5 crossing inside the detected support, lying
      between the component means (a unique ORDERED high/low separation);
   S2 the fitted density is bimodal;
   S3 the boundary clears one molecule at the donor's median detected depth
      (`1e4 / median depth`), so it is not the dropout / one-molecule split;
   S5 specificity against a PLUG-IN stateless null: one homogeneous Poisson
      rate per unit depth at this donor's own depths, its rate calibrated so
      that the EXPECTED detection fraction over these depths equals this
      donor's observed one (amendment 06; a donor detected in every cell or
      none cannot be calibrated and fails S5), shrunk by ratios resampled from its
      own decontX layer. A null replicate that cannot be fitted counts as one
      the observed separation did NOT beat. The plug-in-null Monte Carlo
      exceedance score is (1 + exceeding + unfitted) / (1 + NULL_REPLICATES),
      and S5 passes iff it is at most 1 / (1 + NULL_REPLICATES) = 1/100: all
      99 replicates fitted and the observed Ashman's D strictly above each
      (amendment 01, ratified by the owner). Because the null's parameters
      are estimated from the same donor, the score is NOT an exact p-value
      and no exact frequentist or Type-I level is claimed (amendment 03). How
      many null replicates also pass S1-S3 is reported as a diagnostic.
4. Boundaries at posterior 0.25, 0.5 and 0.75, each the unique in-support
   root, strictly ordered.

D4 (Phase-1B M1(b): the high component excludes at least half the detected
cells) is REPORTED, not gating. A genuine state whose high cells are most of the
detected cells fails it, and the dropout split it was written against is
already refused by S3 and by the null (S5).

Across donors: EVERY donor must qualify (no donor is dropped for failing), and
there must be at least `min_reference_donors`. The primary threshold is the
median across donors of the posterior-0.5 boundaries; the two sensitivity
variants are the medians of the 0.25 and 0.75 boundaries. All three are
reported; none is selected. If any condition fails the result is
`NO_STABLE_SEPARATION` and no threshold is emitted. A lattice or dropout split
is a failure, never a threshold.

`count` (not per 10k) is run as a DIAGNOSTIC only: it is reported and can never
become the primary quantity or a variant.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Sequence
from dataclasses import dataclass

from dt_adoc.personalization.phase2b.identity import IdentityError, donor_key
from dt_adoc.scrna import klf12_state as _klf12_state
from dt_adoc.scrna.klf12_state import (
    M1_B_MIN_EXCLUDED_SHARE,
    ONE_TRANSCRIPT,
    _component_crossings,
    fit_two_component_mixture,
)

#: Fitted by `fit_two_component_mixture`, which refuses fewer.
MIN_DETECTED_CELLS = 20
NULL_REPLICATES = 99
NULL_SEED = 20260925
POSTERIOR_LEVELS = (0.25, 0.5, 0.75)
PRIMARY_QUANTITY = "count_per_10k"
DIAGNOSTIC_QUANTITY = "count"
RULE = ">="
QUALIFIED = "SEPARATION_QUALIFIED"
NOT_QUALIFIED = "NO_STABLE_SEPARATION"


class DerivationError(ValueError):
    """An input the procedure refuses to run on at all."""


@dataclass(frozen=True)
class DonorCells:
    """One independent reference donor's epithelial cells in the qualifying arm.

    `counts` is KLF12 on the decontX-corrected layer and `depths` each cell's
    column sum of that layer, index-aligned. No barcode is carried.
    """

    donor_id: str
    counts: tuple[float, ...]
    depths: tuple[float, ...]


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def quantity(count: float, depth: float, name: str) -> float:
    if name == PRIMARY_QUANTITY:
        if not depth > 0:
            raise DerivationError("count_per_10k needs a positive depth")
        return count / depth * 1e4
    if name == DIAGNOSTIC_QUANTITY:
        return count
    raise DerivationError(f"unknown quantity {name!r}")


def posterior_roots(fit: dict[str, float], level: float) -> list[float]:
    """Every x (log scale) where P(high | x) = level, sorted.

    P(high) = level is P(high) = 0.5 for the prior odds divided by the level's
    odds, so the Phase-1B quadratic solver is reused rather than re-derived.
    """
    weight = fit["high_component_weight"]
    if not 0.0 < weight < 1.0 or not 0.0 < level < 1.0:
        return []
    odds = (weight / (1.0 - weight)) * ((1.0 - level) / level)
    return _component_crossings(
        fit["log_mean_low"],
        fit["log_sd_low"] ** 2,
        fit["log_mean_high"],
        fit["log_sd_high"] ** 2,
        odds / (1.0 + odds),
    )


class _SaturatingMath:
    """`math`, except that exp() of a too-large argument is +inf, not an error."""

    def __getattr__(self, name: str) -> object:
        return getattr(math, name)

    @staticmethod
    def exp(value: float) -> float:
        try:
            return math.exp(value)
        except OverflowError:
            return math.inf


def fit_mixture(detected: Sequence[float]) -> dict[str, float]:
    """The Phase-1B mixture fit, unchanged, except that it cannot crash on a report field.

    `fit_two_component_mixture` finishes EM and then returns exp() of every
    posterior crossing as a report-only field. A crossing far outside the data
    (log value > ~709) makes that exp() overflow AFTER the fit has converged,
    and none of S1-S3 reads it (only in-support crossings count). While the fit
    runs, exp() therefore saturates to +inf instead of raising; every value that
    does not overflow is bit-for-bit what the frozen fitter computes
    (tests/unit/test_phase2b_contract.py checks this). Amendment 06.
    """
    saved = _klf12_state.math
    _klf12_state.math = _SaturatingMath()
    try:
        return fit_two_component_mixture(detected)
    finally:
        _klf12_state.math = saved


def separation(values: Sequence[float], floor: float) -> dict[str, object]:
    """S1-S3, diagnostic D4 and the three posterior boundaries for one set of per-cell values."""
    detected = [v for v in values if v > 0]
    if len(detected) < MIN_DETECTED_CELLS:
        return {
            "qualifies": False,
            "reason": "too_few_detected",
            "n_detected": len(detected),
        }
    try:
        fit = fit_mixture(detected)
    except (OverflowError, ValueError, ZeroDivisionError):
        # A genuine failure to fit: the observed data then fail, and a null
        # replicate counts as UNFITTED, i.e. against the observed separation
        # (amendment 01).
        return {"qualifies": False, "reason": "fit_failed", "n_detected": len(detected)}
    low, high = fit["detected_log_support"]
    boundaries: dict[str, float | None] = {}
    for level in POSTERIOR_LEVELS:
        inside = [r for r in posterior_roots(fit, level) if low <= r <= high]
        boundaries[f"{level:g}"] = math.exp(inside[0]) if len(inside) == 1 else None
    b25, b50, b75 = (boundaries[f"{level:g}"] for level in POSTERIOR_LEVELS)
    checks = {
        "S1_unique_ordered_separation": bool(fit["ordered_separation"]),
        "S2_bimodal": bool(fit["analytic_bimodal"]),
        "S3_clears_one_molecule": fit["boundary_value"] is not None
        and float(fit["boundary_value"]) >= floor,
        "posterior_boundaries_unique_and_ordered": None not in (b25, b50, b75)
        and b25 < b50 < b75,
    }
    diagnostics = {
        "D4_high_excludes_half_of_detected": 1.0
        - float(fit["high_component_share_of_detected"])
        >= M1_B_MIN_EXCLUDED_SHARE,
    }
    return {
        "qualifies": all(checks.values()),
        "ashman_d": ashman_d(fit),
        "checks": checks,
        "diagnostics": diagnostics,
        "n_detected": len(detected),
        "one_molecule_floor": floor,
        "boundaries": boundaries,
        "fit": {k: fit[k] for k in sorted(fit) if not isinstance(fit[k], list)},
    }


def ashman_d(fit: dict[str, object]) -> float:
    """Separation of the two fitted components: sqrt(2) |mu1 - mu0| / sqrt(v0 + v1)."""
    spread = float(fit["log_sd_low"]) ** 2 + float(fit["log_sd_high"]) ** 2
    return (
        math.sqrt(2.0)
        * abs(float(fit["log_mean_high"]) - float(fit["log_mean_low"]))
        / math.sqrt(spread)
    )


def _seed(donor_id: str, quantity_name: str) -> int:
    digest = hashlib.sha256(
        f"{NULL_SEED}:{donor_id}:{quantity_name}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _poisson(rate: float, draw: random.Random) -> int:
    if rate <= 0.0:
        return 0
    limit, count, product = math.exp(-rate), 0, 1.0
    while True:
        product *= draw.random()
        if product <= limit:
            return count
        count += 1


def _floor(cells: DonorCells, quantity_name: str) -> float:
    if quantity_name == DIAGNOSTIC_QUANTITY:
        return ONE_TRANSCRIPT
    depths = [d for c, d in zip(cells.counts, cells.depths) if c > 0]
    return 1e4 / _median(depths)


def expected_detection(depths: Sequence[float], rate: float) -> float:
    """The EXPECTED fraction of cells with at least one molecule under the null:
    mean over cells of 1 - exp(-rate * depth / mean depth). Monotone in `rate`."""
    mean_depth = sum(depths) / len(depths)
    return sum(1.0 - math.exp(-rate * d / mean_depth) for d in depths) / len(depths)


def calibrated_rate(depths: Sequence[float], detection: float) -> float | None:
    """The null rate whose EXPECTED detection equals the observed fraction.

    Bisection on `expected_detection`, which is strictly increasing, so the
    root is unique. A detection fraction of 0 or 1 has no finite positive
    rate, and the null cannot be calibrated (S5 then fails closed).
    """
    if not 0.0 < detection < 1.0:
        return None
    low, high = 0.0, 1.0
    while expected_detection(depths, high) < detection:
        high *= 2.0
        if high > 1e12:
            return None
    for _ in range(200):
        middle = (low + high) / 2
        if expected_detection(depths, middle) < detection:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def null_specificity(
    cells: DonorCells, quantity_name: str, observed_d: float
) -> dict[str, object]:
    """S5: is the observed separation stronger than every plug-in stateless null replicate?"""
    depths = list(cells.depths)
    mean_depth = sum(depths) / len(depths)
    detection = sum(1 for c in cells.counts if c > 0) / len(depths)
    ratios = [c / round(c) for c in cells.counts if round(c) >= 1]
    if not ratios:
        return {"passes": False, "reason": "no_shrinkage_ratio"}
    floor = _floor(cells, quantity_name)

    rate = calibrated_rate(depths, detection)
    if rate is None:
        return {"passes": False, "reason": "detection_fraction_not_calibratable"}
    draw = random.Random(_seed(cells.donor_id, quantity_name))
    fitted = certified = 0
    null_d: list[float] = []
    for _ in range(NULL_REPLICATES):
        values = []
        for depth in depths:
            drawn = _poisson(rate * depth / mean_depth, draw)
            value = drawn * ratios[draw.randrange(len(ratios))] if drawn else 0.0
            values.append(quantity(value, depth, quantity_name))
        verdict = separation(values, floor)
        if verdict.get("reason") in ("too_few_detected", "fit_failed"):
            continue
        fitted += 1
        certified += int(bool(verdict["qualifies"]))
        null_d.append(float(verdict["ashman_d"]))
    exceeds = sum(1 for d in null_d if d >= observed_d)
    unfitted = NULL_REPLICATES - fitted
    score = (1 + exceeds + unfitted) / (1 + NULL_REPLICATES)
    return {
        "passes": score <= 1 / (1 + NULL_REPLICATES),
        "replicates": NULL_REPLICATES,
        "fitted": fitted,
        "observed_ashman_d": observed_d,
        "max_null_ashman_d": max(null_d) if null_d else None,
        "null_replicates_at_or_above_observed": exceeds,
        "null_replicates_unfitted_counted_as_exceeding": unfitted,
        "plugin_null_exceedance_score": score,
        "diagnostic_null_replicates_passing_s1_s3": certified,
        "calibrated_rate_at_mean_depth": rate,
        "detection_fraction": detection,
    }


def donor_result(cells: DonorCells, quantity_name: str) -> dict[str, object]:
    if len(cells.counts) != len(cells.depths) or not cells.counts:
        raise DerivationError(
            f"{cells.donor_id}: counts and depths must align and be non-empty"
        )
    if any(not (math.isfinite(c) and c >= 0) for c in cells.counts):
        raise DerivationError(
            f"{cells.donor_id}: counts must be finite and non-negative"
        )
    if any(not (math.isfinite(d) and d > 0) for d in cells.depths):
        raise DerivationError(f"{cells.donor_id}: depths must be finite and positive")
    values = [quantity(c, d, quantity_name) for c, d in zip(cells.counts, cells.depths)]
    if not any(c > 0 for c in cells.counts):
        return {
            "donor_id": cells.donor_id,
            "n_cells": len(values),
            "qualifies": False,
            "reason": "too_few_detected",
        }
    observed = separation(values, _floor(cells, quantity_name))
    null = (
        null_specificity(cells, quantity_name, float(observed["ashman_d"]))
        if observed["qualifies"]
        else None
    )
    return {
        "donor_id": cells.donor_id,
        "n_cells": len(values),
        "observed": observed,
        "null_specificity": null,
        "qualifies": bool(observed["qualifies"]) and bool(null and null["passes"]),
    }


def _one_quantity(
    donors: Sequence[DonorCells], quantity_name: str
) -> dict[str, object]:
    results = [donor_result(d, quantity_name) for d in donors]
    if not all(r["qualifies"] for r in results):
        return {"verdict": NOT_QUALIFIED, "per_donor": results}
    per_level = {
        f"{level:g}": _median(
            [r["observed"]["boundaries"][f"{level:g}"] for r in results]
        )
        for level in POSTERIOR_LEVELS
    }
    return {
        "verdict": QUALIFIED,
        "per_donor": results,
        "primary_threshold": per_level["0.5"],
        "threshold_variants": [per_level["0.25"], per_level["0.75"]],
    }


def derive(
    donors: Sequence[DonorCells], *, min_reference_donors: int
) -> dict[str, object]:
    """The pre-registered derivation. The ONLY route to a Phase-2B threshold."""
    if (
        isinstance(min_reference_donors, bool)
        or not isinstance(min_reference_donors, int)
        or min_reference_donors < 1
    ):
        raise DerivationError("min_reference_donors must be an owner-set integer >= 1")
    try:
        keys = [donor_key(d.donor_id) for d in donors]
    except IdentityError as refused:
        raise DerivationError(str(refused)) from refused
    if len(set(keys)) != len(keys):
        raise DerivationError(
            "a donor appears twice; clones and replicates are one donor"
        )
    ordered = sorted(donors, key=lambda d: d.donor_id)
    if len(ordered) < min_reference_donors:
        return {
            "verdict": NOT_QUALIFIED,
            "reason": "fewer_reference_donors_than_min_reference_donors",
            "n_reference_donors": len(ordered),
            "min_reference_donors": min_reference_donors,
        }
    primary = _one_quantity(ordered, PRIMARY_QUANTITY)
    diagnostic = _one_quantity(ordered, DIAGNOSTIC_QUANTITY)
    out: dict[str, object] = {
        "verdict": primary["verdict"],
        "quantity": PRIMARY_QUANTITY,
        "rule": RULE,
        "aggregation_unit": "donor",
        "n_reference_donors": len(ordered),
        "min_reference_donors": min_reference_donors,
        "per_donor": primary["per_donor"],
        "variant_selection": "all_reported_none_selected",
        "diagnostic_count_scale": {
            "role": "diagnostic only; never the primary quantity and never a variant",
            "verdict": diagnostic["verdict"],
            "per_donor": diagnostic["per_donor"],
        },
    }
    if primary["verdict"] == QUALIFIED:
        out["primary_threshold"] = primary["primary_threshold"]
        out["threshold_variants"] = primary["threshold_variants"]
    return out
