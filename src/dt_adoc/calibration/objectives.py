"""Higher-level phase-1 objective helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from dt_adoc.calibration.adhesion_likelihood import (
    STRUCTURALLY_CONTRADICTED,
    binomial_log_likelihood,
    is_rankable,
    structural_verdict,
)

#: Retained as the role vocabulary in `config/calibration.yaml`. Since the
#: 2026-09-16 demotion these name *which diagnostic* a readout is, not which
#: readouts are fitted: no term in this repository is magnitude-fitted any more.
#: See `docs/gate3_scope_adjudication.md`.
CALIBRATION_ROLE = "calibration"
HELD_OUT_VALIDATION_ROLE = "validation_if_held_out"


@dataclass(frozen=True)
class AdhesionReadout:
    probability: float
    successes: int
    trials: int
    role: str


@dataclass(frozen=True)
class AdhesionLogLikelihoodSummary:
    calibration_log_likelihood: float
    validation_log_likelihood: float
    total_log_likelihood: float
    calibration_readout_count: int
    validation_readout_count: int
    descriptive_readout_count: int
    #: Arms whose unclipped probability contradicts the observation outright.
    #: Their log-likelihood is ``successes * log(CLIP_EPSILON)`` and is
    #: identical for every candidate, so it must not rank anything.
    structurally_contradicted_count: int = 0
    #: True when at least one summed readout is not rankable, i.e. the sums
    #: above are reportable diagnostics but not a model-selection score.
    contains_unrankable_readouts: bool = False


def readout_structural_verdict(readout: AdhesionReadout) -> str:
    return structural_verdict(
        probability=readout.probability,
        successes=readout.successes,
        trials=readout.trials,
    )


def readout_is_rankable(readout: AdhesionReadout) -> bool:
    return is_rankable(
        probability=readout.probability,
        successes=readout.successes,
        trials=readout.trials,
    )


def rankable_readouts(
    readouts: Iterable[AdhesionReadout],
) -> tuple[AdhesionReadout, ...]:
    """The subset whose log-likelihood carries model content.

    A caller that insists on a scalar must build it from these, and must say so;
    the demotion means this repository has no such caller.
    """
    return tuple(r for r in readouts if readout_is_rankable(r))


def readout_log_likelihood(readout: AdhesionReadout) -> float:
    return binomial_log_likelihood(
        probability=readout.probability,
        successes=readout.successes,
        trials=readout.trials,
    )


def filter_readouts_by_role(
    readouts: Iterable[AdhesionReadout],
    *,
    roles: Iterable[str],
) -> tuple[AdhesionReadout, ...]:
    allowed_roles = frozenset(roles)
    return tuple(readout for readout in readouts if readout.role in allowed_roles)


def summarize_adhesion_log_likelihoods(
    readouts: Iterable[AdhesionReadout],
    *,
    calibration_roles: Iterable[str] = (CALIBRATION_ROLE,),
    validation_roles: Iterable[str] = (HELD_OUT_VALIDATION_ROLE,),
) -> AdhesionLogLikelihoodSummary:
    readout_tuple = tuple(readouts)
    calibration_readouts = filter_readouts_by_role(
        readout_tuple,
        roles=calibration_roles,
    )
    validation_readouts = filter_readouts_by_role(
        readout_tuple,
        roles=validation_roles,
    )
    unrankable = tuple(r for r in readout_tuple if not readout_is_rankable(r))
    return AdhesionLogLikelihoodSummary(
        structurally_contradicted_count=sum(
            1
            for r in readout_tuple
            if readout_structural_verdict(r) == STRUCTURALLY_CONTRADICTED
        ),
        contains_unrankable_readouts=bool(unrankable),
        calibration_log_likelihood=sum(
            readout_log_likelihood(readout) for readout in calibration_readouts
        ),
        validation_log_likelihood=sum(
            readout_log_likelihood(readout) for readout in validation_readouts
        ),
        total_log_likelihood=sum(
            readout_log_likelihood(readout) for readout in readout_tuple
        ),
        calibration_readout_count=len(calibration_readouts),
        validation_readout_count=len(validation_readouts),
        descriptive_readout_count=len(readout_tuple),
    )


def summed_adhesion_log_likelihood(readouts: list[AdhesionReadout]) -> float:
    """Diagnostic sum over the `calibration`-role readouts.

    Kept for reporting and for the existing tests. It is **not** a
    model-selection score: consult ``contains_unrankable_readouts`` on the
    summary before comparing two candidates on it.
    """
    return summarize_adhesion_log_likelihoods(readouts).calibration_log_likelihood
