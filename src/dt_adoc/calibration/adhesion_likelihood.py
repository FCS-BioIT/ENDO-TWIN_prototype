"""Binomial objectives for adhesion readouts.

Adhesion is **not** a magnitude-fitted objective. `config/calibration.yaml`
demoted it to an ordinal/diagnostic readout on 2026-09-16; see
`docs/gate3_scope_adjudication.md` for why. These helpers remain because the
per-arm log-likelihood is still *reported* as a diagnostic, but a caller that
ranks candidates on it is using it outside its declared role.

The clip below is the reason this module needs care. Clipping a probability
into ``[eps, 1-eps]`` is an ordinary numerical guard when the probability is
merely *small*. It is unsound when the probability is **structurally zero** --
when the model says the observed event is impossible -- because it silently
converts "impossible" into "penalised by ``log(eps)``", a number that is a
property of the constant and not of the model. Changing ``eps`` by three
decades moves such a score by 6.9 nats with the model and the data untouched.

So the unclipped probability is kept and inspected: :func:`structural_verdict`
reports ``structurally_contradicted`` when a model assigns probability zero to
an arm in which successes were observed, and
:func:`is_rankable` refuses that arm for candidate ranking.
"""

from __future__ import annotations

import math
from typing import Final

#: Numerical guard only. Never a statement about how unlikely anything is.
CLIP_EPSILON: Final = 1e-9

#: The model can produce the observation; its log-likelihood is meaningful.
CONSISTENT: Final = "consistent"
#: P(event) == 0 exactly, yet successes were observed. The clipped score for
#: this arm is ``successes * log(CLIP_EPSILON)`` and carries no model content.
STRUCTURALLY_CONTRADICTED: Final = "structurally_contradicted"
#: P(event) == 1 exactly, yet failures were observed. The mirror case.
STRUCTURALLY_SATURATED: Final = "structurally_saturated"


def _clip_probability(probability: float) -> float:
    return min(1.0 - CLIP_EPSILON, max(CLIP_EPSILON, probability))


def structural_verdict(*, probability: float, successes: int, trials: int) -> str:
    """Classify an arm from the **unclipped** probability.

    Deliberately takes the raw model probability, because the whole point is to
    see the exact 0 or 1 that clipping would hide.
    """
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("invalid binomial counts")
    failures = trials - successes
    if probability == 0.0 and successes > 0:
        return STRUCTURALLY_CONTRADICTED
    if probability == 1.0 and failures > 0:
        return STRUCTURALLY_SATURATED
    return CONSISTENT


def is_rankable(*, probability: float, successes: int, trials: int) -> bool:
    """Whether this arm's log-likelihood may be used to rank candidates.

    False exactly when the score would be a function of :data:`CLIP_EPSILON`
    rather than of the model.
    """
    return (
        structural_verdict(probability=probability, successes=successes, trials=trials)
        == CONSISTENT
    )


def binomial_log_likelihood(
    *, probability: float, successes: int, trials: int
) -> float:
    """Clipped binomial log-likelihood.

    Safe to report. **Not** safe to rank on without consulting
    :func:`is_rankable` first: for a structurally contradicted arm the value is
    ``successes * log(CLIP_EPSILON)`` and is identical for every candidate.
    """
    if trials < 0 or successes < 0 or successes > trials:
        raise ValueError("invalid binomial counts")
    p = _clip_probability(probability)
    return successes * math.log(p) + (trials - successes) * math.log(1.0 - p)


def binomial_deviance(*, probability: float, successes: int, trials: int) -> float:
    if trials == 0:
        return 0.0
    observed = successes / trials
    if observed in {0.0, 1.0}:
        observed = _clip_probability(observed)
    fitted = _clip_probability(probability)
    return 2.0 * (
        successes * math.log(observed / fitted)
        + (trials - successes) * math.log((1.0 - observed) / (1.0 - fitted))
    )
