"""Apply a KLF12 prior to `E_KLF12_HIGH`, and measure exactly what it moves.

Step three of the three the pre-registration keeps apart. `klf12_state.py`
produced candidate probabilities and the finding that none of them is a measured
biological state; this module puts a probability into the model and reports the
consequence. Under the `CONDITIONAL_GO` tier that is a **sensitivity analysis
over an arbitrary threshold**, never a conditioned twin, and every artifact it
writes says so in its own provenance.

WHAT IS AND IS NOT TOUCHED. `network.bnd` is never read for editing and no
Boolean rule changes. `baseline.cfg` is never rewritten. The prior enters as one
`.istate` line SUBSTITUTED for the plain `E_KLF12_HIGH.istate = FALSE;` that
`baseline.cfg` carries, in the merged configuration that `build_condition_cfg`
already assembles. Substituted and not appended: the bracketed probabilistic
form does not share a merge key with the plain one, so appending leaves both and
MaBoSS refuses with `duplicate node istate declaration`. It is the mechanism
MaBoSS provides
for a free variable and the same mechanism the four interface relays already
use. The canonical unconditioned model stays exactly where it was, and is the
p = 0 row of every table here.

WHY THE PROTOCOL LOOP IS REPEATED HERE. `run_protocol` assembles its own
override texts and has no seam for another one. Adding one would change a file
under `IMPLEMENTATION_GLOBS`, which would invalidate the implementation digest
recorded in `docs/concordance/run_settings.json` and force a regeneration of
artifacts this increment has no business touching. So the loop is repeated, and
`tests/integration/test_klf12_conditioning.py` pins it to `run_protocol` by
running both with no prior and requiring identical node values -- a drift guard,
not a promise.

THE TRAP THIS WAS WRITTEN AROUND. A phase boundary re-initialises the memory
nodes of the protocol's memory policy from the previous phase's joint
distribution, and `minimal_stable_joint` -- the superset default -- contains
`E_LIF`, `E_GP130_STAT3` and `E_RECEPTIVE_SURFACE` but NOT `E_KLF12_HIGH`. So at
each boundary the derived consequences of the prior arrive from memory while the
prior itself is re-drawn independently from the configuration, and the
correlation between them is broken for as long as it takes the rules to
re-impose it. At the converged horizon read here that is immaterial, because
`E_KLF12_HIGH` has logic `E_KLF12_HIGH` and never moves, so the fixed point is
the same. At a declared horizon it would not be. Readings here are converged,
and `analytic_endpoint` states the value they must equal.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

from dt_adoc.concordance.simulate import (
    CONVERGED_PHASE_HORIZON,
    DEFAULT_SEEDS,
    DEFAULT_TRAJECTORIES,
    protocol_lineage,
    run_provenance,
)
from dt_adoc.model.provenance import repo_root
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.simulation.runner import (
    ConditionRunResult,
    _input_override_text,
    _timing_override_text,
    _validate_joint_distribution,
    build_condition_cfg,
    build_continuation,
)

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
NODE = "E_KLF12_HIGH"

#: The prior grid the committed artifacts were swept over. It is the module
#: default AND the pixi task's, so `pixi run sweep-klf12-conditioning`
#: reproduces exactly the committed rows. An earlier default carried 0.05 and
#: 0.75, which appear in neither committed artifact, so the documented
#: invocation did not reconstruct the table it was documented to produce.
DEFAULT_GRID: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5, 1.0)

#: The same arm set the concordance build simulates, so the p = 0 row of this
#: sweep is directly comparable with `docs/concordance/run_settings.json`
#: rather than being a second, differently configured simulation of one model.
ARMS: dict[str, str] = {
    "untreated": "adhesion_challenge_basal",
    "hormone_treated": "adhesion_challenge_hormone_treated",
    "mifepristone": "adhesion_challenge_hormone_treated_mifepristone",
    "basal_maternal": "basal_maternal",
    "e2_primed_maternal": "e2_primed_maternal",
    "hormone_treated_maternal": "hormone_treated_maternal",
}

#: Nodes worth tabulating: the declared outputs, plus the executable states on
#: the route from the conditioned node to them. Recorded for every arm so "which
#: model quantities did not move" is answered from the table, not from silence.
TRACKED: tuple[str, ...] = (
    "E_KLF12_HIGH",
    "E_LIF",
    "E_GP130_STAT3",
    "E_RECEPTIVE_SURFACE",
    "E_ITGAVB3_5",
    "E_CD98_CD9",
    "X_ADHESION_ROUTE_SPP1",
    "X_ADHESION_ROUTE_REDUNDANT",
    "X_ANTIADHESIVE_ROUTE",
    "OUT_EPITHELIAL_RECEPTIVE",
    "OUT_STROMAL_DECIDUALIZED",
    "OUT_MATERNAL_ADHESION_COMPETENCE",
    "OUT_STABLE_ADHESION",
)


class Klf12ConditioningError(RuntimeError):
    """The prior cannot be applied as asked."""


def istate_override_text(prior: float, node: str = NODE) -> str:
    """One `.istate` line for a free variable, in MaBoSS's two-state form.

    The bracketed form is the one MaBoSS accepts for a probability list, and the
    form `baseline.cfg` already uses for its four probabilistic interface
    relays. It does NOT share a merge key with the plain
    `E_KLF12_HIGH.istate = FALSE;` that `baseline.cfg` carries for this node, so
    appending it to `override_texts` leaves BOTH lines in the merged
    configuration -- which MaBoSS then rejects outright with
    ``duplicate node istate declaration``. That refusal is worth recording,
    because it is the reason there is no silent-precedence hazard here: the
    engine will not quietly pick one. `_substitute_istate` therefore replaces
    the plain line rather than adding to it, and asserts it replaced exactly
    one.

    It names exactly one node: an override that silently touched a second one
    would be indistinguishable in the result from a biological consequence of
    the first.
    """
    if not 0.0 <= prior <= 1.0:
        raise Klf12ConditioningError(f"prior {prior!r} is not a probability")
    return f"[{node}].istate = {1.0 - prior}[0], {prior}[1];\n"


def _substitute_istate(cfg_text: str, prior: float, node: str = NODE) -> str:
    """Swap the node's deterministic istate line for the probabilistic form.

    Exactly one line must match. `baseline.cfg` carries one plain istate line
    per node and the condition configurations override some of them by the same
    key, so a count other than one means the merged configuration is not shaped
    the way this substitution assumes and the prior would land somewhere
    unintended -- or nowhere.
    """
    lines = cfg_text.splitlines()
    matched = [
        index
        for index, line in enumerate(lines)
        if line.split("=", 1)[0].strip() == f"{node}.istate"
    ]
    if len(matched) != 1:
        raise Klf12ConditioningError(
            f"expected exactly one {node}.istate line, found {len(matched)}"
        )
    lines[matched[0]] = istate_override_text(prior, node).rstrip("\n")
    return "\n".join(lines) + "\n"


def _run_condition(
    *,
    condition_cfg: Path,
    root: Path | None,
    override_texts: list[str],
    prior: float | None,
    continuation: object | None,
    seed: int,
    sample_count: int,
) -> ConditionRunResult:
    """`run_cmaboss_condition` with one istate line rewritten before the load.

    Deliberately not a call into `run_cmaboss_condition` with an extra override:
    the prior has to REPLACE a line, and that function's merge can only add or
    replace by key, which for a probabilistic istate is a different key. The
    rest of it is reproduced, including the rule-variant branch -- which is
    asserted empty for this model rather than assumed, because a logic override
    would mean a rule had changed and this increment forbids that.
    """
    import maboss

    from dt_adoc.maboss_adapter import (
        apply_joint_distribution,
        apply_node_marginals_independent,
    )
    from dt_adoc.model.runtime import resolve_model, resolve_rule_variants

    active_root = root or repo_root()
    model_spec = resolve_model(MODEL_VERSION, active_root)
    _, logic_overrides = resolve_rule_variants(
        model_version=MODEL_VERSION, root=active_root
    )
    if logic_overrides:
        raise Klf12ConditioningError(
            "a rule variant is active; this increment changes no Boolean rule"
        )
    merged_cfg = build_condition_cfg(
        model_version=MODEL_VERSION,
        condition_cfg=condition_cfg,
        root=active_root,
        override_texts=override_texts,
        seed=seed,
        sample_count=sample_count,
    )
    if prior is not None:
        merged_cfg.write_text(
            _substitute_istate(merged_cfg.read_text(encoding="utf-8"), prior),
            encoding="utf-8",
        )
    simulation = maboss.load(str(model_spec.network_bnd), str(merged_cfg), cmaboss=True)
    if continuation is not None:
        if continuation.mode == "marginal":  # type: ignore[attr-defined]
            apply_node_marginals_independent(
                network=simulation.network,
                result=continuation.previous_result,  # type: ignore[attr-defined]
                forced_nodes=continuation.forced_nodes,  # type: ignore[attr-defined]
            )
        elif continuation.node_ids:  # type: ignore[attr-defined]
            _validate_joint_distribution(
                continuation.distribution,  # type: ignore[attr-defined]
                node_count=len(continuation.node_ids),  # type: ignore[attr-defined]
            )
            apply_joint_distribution(
                network=simulation.network,
                memory_nodes=continuation.node_ids,  # type: ignore[attr-defined]
                distribution=continuation.distribution,  # type: ignore[attr-defined]
                forced_nodes=continuation.forced_nodes,  # type: ignore[attr-defined]
            )
    result = simulation.run()
    last_nodes = result.get_last_nodes_probtraj().copy()
    return ConditionRunResult(
        merged_cfg=merged_cfg,
        raw_result=result,
        last_nodes_probtraj=last_nodes,
        last_states_probtraj=result.get_last_states_probtraj().copy(),
        last={
            key: float(value) for key, value in last_nodes.iloc[-1].to_dict().items()
        },
        nodes_probtraj=None,
    )


@dataclass(frozen=True)
class PriorRun:
    """One arm at one prior, aggregated over seeds at the converged horizon."""

    arm_id: str
    protocol_id: str
    lineage: tuple[str, ...]
    prior: float
    prior_label: str
    node_mean: dict[str, float]
    node_sd: dict[str, float]
    #: The per-seed endpoints the mean and sd above are computed from. Kept so a
    #: reader can recompute both rather than take them on trust; an sd with no
    #: parents is an unverifiable summary.
    node_by_seed: dict[str, tuple[float, ...]]
    seeds: tuple[int, ...]
    trajectory_count: int
    phase_horizon: float


def _run_chain(
    protocol_id: str,
    *,
    prior: float,
    seed: int,
    trajectory_count: int,
    phase_horizon: float,
    root: Path | None,
    apply_prior: bool = True,
) -> dict[str, float]:
    """Run a protocol's full declared lineage with the prior applied throughout.

    The prior is appended to every phase of every protocol in the chain, not
    only the first. `E_KLF12_HIGH` is not in `minimal_stable_joint`, so a phase
    that did not carry the override would silently fall back to the `FALSE` in
    `baseline.cfg` and the chain would report an unconditioned model under a
    conditioned label.
    """
    lineage = protocol_lineage(protocol_id, model_version=MODEL_VERSION, root=root)
    continuation = None
    last: dict[str, float] = {}
    for index, step_protocol in enumerate(lineage):
        protocol = get_protocol(step_protocol, root, model_version=MODEL_VERSION)
        condition_cfg = (root or repo_root()) / protocol.condition_cfg
        condition_run = None
        for step_index, step in enumerate(protocol.steps):
            condition_run = _run_condition(
                condition_cfg=condition_cfg,
                root=root,
                override_texts=[
                    _input_override_text(step.input_states),
                    _timing_override_text(relative_duration=phase_horizon, root=root),
                ],
                prior=prior if apply_prior else None,
                continuation=continuation,
                seed=seed,
                sample_count=trajectory_count,
            )
            if step_index + 1 < len(protocol.steps):
                continuation = build_continuation(
                    previous_condition=condition_run,
                    target_protocol_id=step_protocol,
                    model_version=MODEL_VERSION,
                    forced_nodes=protocol.steps[step_index + 1].input_states,
                    source_protocol=step_protocol,
                    root=root,
                )
        assert condition_run is not None
        last = {key: float(value) for key, value in condition_run.last.items()}
        if index + 1 < len(lineage):
            next_protocol = get_protocol(
                lineage[index + 1], root, model_version=MODEL_VERSION
            )
            continuation = build_continuation(
                previous_condition=condition_run,
                target_protocol_id=lineage[index + 1],
                model_version=MODEL_VERSION,
                forced_nodes=next_protocol.steps[0].input_states,
                source_protocol=step_protocol,
                root=root,
            )
    return last


def run_prior(
    arm_id: str,
    protocol_id: str,
    prior: float,
    *,
    prior_label: str,
    root: Path | None = None,
    trajectory_count: int = DEFAULT_TRAJECTORIES,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    phase_horizon: float = CONVERGED_PHASE_HORIZON,
) -> PriorRun:
    by_seed: dict[str, list[float]] = {}
    for seed in seeds:
        last = _run_chain(
            protocol_id,
            prior=prior,
            seed=seed,
            trajectory_count=trajectory_count,
            phase_horizon=phase_horizon,
            root=root,
        )
        for node_id, value in last.items():
            by_seed.setdefault(node_id, []).append(value)
    return PriorRun(
        arm_id=arm_id,
        protocol_id=protocol_id,
        lineage=protocol_lineage(protocol_id, model_version=MODEL_VERSION, root=root),
        prior=prior,
        prior_label=prior_label,
        node_mean={key: mean(values) for key, values in by_seed.items()},
        node_sd={
            key: (pstdev(values) if len(values) > 1 else 0.0)
            for key, values in by_seed.items()
        },
        node_by_seed={key: tuple(values) for key, values in by_seed.items()},
        seeds=tuple(seeds),
        trajectory_count=trajectory_count,
        phase_horizon=phase_horizon,
    )


def mixture_prediction(low: float, high: float, prior: float) -> float:
    """What every tracked value must equal at an intermediate prior.

    ``(1 - prior) * value_at_0 + prior * value_at_1``.

    WHY, PRECISELY. `E_KLF12_HIGH` has logic `E_KLF12_HIGH`, so within one phase
    a trajectory that starts high stays high and the ensemble splits into two
    sub-ensembles that never mix. Across a CHAIN that argument does not carry:
    `_run_chain` re-applies the prior at every phase, and the declared lineages
    here are four and five phases deep, so a priori the endpoint is a degree-4
    or degree-5 polynomial in the prior rather than a line. What makes it a line
    is the converged horizon -- each phase reaches its fixed point, so the
    endpoint depends on the final phase's draw alone and the earlier draws are
    erased. The law is therefore an OBSERVED property of converged readings,
    checked row by row, and would not be expected to hold at a declared horizon.

    This is the check that the override reached `E_KLF12_HIGH` and nothing else.
    An earlier version of this module asserted the special case
    ``value_at_0 * (1 - prior)``, which is right only for the nodes the high
    sub-ensemble drives to zero. It is wrong for `E_KLF12_HIGH` itself, wrong
    for `OUT_STROMAL_DECIDUALIZED`, which the conditioned node cannot reach, and
    wrong for `E_ITGAVB3_5`, whose rule has a `E_SECRETORY_STATE` disjunct that
    survives the LIF gate being shut. The mixture law covers all of them and is
    exact, so the deviation column now measures Monte Carlo error rather than
    the classification error of a law applied outside its domain.
    """
    if not 0.0 <= prior <= 1.0:
        raise Klf12ConditioningError(f"prior {prior!r} is not a probability")
    return (1.0 - prior) * low + prior * high


RESPONSE_COLUMNS: tuple[str, ...] = (
    "arm_id",
    "protocol_id",
    "prior_label",
    "prior",
    "node_id",
    "node_mean",
    "node_sd_across_seeds",
    "mean_at_prior_0",
    "mean_at_prior_1",
    "mixture_prediction",
    "abs_deviation_from_prediction",
    "moves_with_prior",
)


def write_response(runs: list[PriorRun], destination: Path) -> Path:
    """One row per arm, prior and tracked node, each checkable against the law.

    Requires both extremes for every arm. Without them the mixture prediction
    cannot be formed, and a table that silently omitted the check for some arms
    would be indistinguishable from one where the check passed.

    TWO COLUMNS THAT ARE EASILY MISREAD. The rows at ``prior`` 0 or 1 have a
    deviation of zero **by construction** -- they are the anchors the prediction
    is built from -- so the check has content only at interior priors where the
    two anchors differ. And ``node_sd_across_seeds`` is NOT a Monte Carlo error
    bar: the engine assigns a deterministic number of trajectories to each
    initial state rather than sampling it, which is why `E_KLF12_HIGH` reads
    back a spread of exactly zero at every prior while its realised value
    (2001/20000 for a requested 0.1) is not the requested one. That column
    bounds neither the initial-state assignment nor the residual in
    ``abs_deviation_from_prediction``, which is dominated by the discretisation
    of three independently specified deterministic splits over a finite
    ensemble.
    """
    low = {run.arm_id: run.node_mean for run in runs if run.prior == 0.0}
    high = {run.arm_id: run.node_mean for run in runs if run.prior == 1.0}
    missing = sorted({run.arm_id for run in runs} - (set(low) & set(high)))
    if missing:
        raise Klf12ConditioningError(
            f"arms without both prior extremes, so unverifiable: {missing}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(RESPONSE_COLUMNS)]
    for run in sorted(runs, key=lambda item: (item.arm_id, item.prior)):
        for node_id in TRACKED:
            if node_id not in run.node_mean:
                continue
            at_zero = low[run.arm_id][node_id]
            at_one = high[run.arm_id][node_id]
            predicted = mixture_prediction(at_zero, at_one, run.prior)
            lines.append(
                "\t".join(
                    (
                        run.arm_id,
                        run.protocol_id,
                        run.prior_label,
                        f"{run.prior:.6f}",
                        node_id,
                        f"{run.node_mean[node_id]:.6f}",
                        f"{run.node_sd[node_id]:.6f}",
                        f"{at_zero:.6f}",
                        f"{at_one:.6f}",
                        f"{predicted:.6f}",
                        f"{abs(run.node_mean[node_id] - predicted):.6f}",
                        "true" if abs(at_one - at_zero) > 1e-6 else "false",
                    )
                )
            )
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_settings(
    runs: list[PriorRun],
    destination: Path,
    *,
    root: Path,
    candidate_priors: dict[str, float],
) -> Path:
    from dataclasses import asdict as _asdict

    evidence_path = root / "docs" / "scrna" / "klf12_state_evidence.tsv"
    findings_path = root / "docs" / "scrna" / "klf12_state_findings.json"
    provenance = _asdict(
        run_provenance(
            model_version=MODEL_VERSION,
            root=root,
            trajectory_count=(runs[0].trajectory_count if runs else 0),
            seeds=(runs[0].seeds if runs else ()),
        )
    )
    # The candidate priors are read from the state derivation, so that artifact
    # is an executable input of this run and is hashed like one.
    provenance["source_evidence_sha256"] = _sha256(evidence_path)
    provenance["source_findings_sha256"] = _sha256(findings_path)
    provenance["prior_grid"] = list(DEFAULT_GRID)
    # `implementation_digest` covers the shared simulation/concordance surface,
    # which does NOT include this module -- yet this module decides the grid,
    # the istate substitution and the aggregation, so a change here can move
    # every number while every hash above stays identical. The generator is
    # therefore pinned explicitly alongside them.
    from dt_adoc.concordance.simulate import implementation_digest

    generator_files = (
        "src/dt_adoc/scrna/klf12_conditioning.py",
        "src/dt_adoc/scrna/klf12_state.py",
    )
    provenance["generator_files"] = list(generator_files)
    provenance["generator_digest"] = implementation_digest(root, generator_files)

    payload = {
        "schema_version": "1.1",
        "provenance": provenance,
        "claim_level": "arbitrary_threshold_sensitivity_analysis",
        "not_a_claim": [
            (
                "This is NOT a measured prior. klf12_state_findings.json "
                "records that these data yield no biologically interpretable "
                "KLF12-high boundary, and that the pre-registered decision "
                "branch is NOT uniquely determined: crossing the two "
                "defensible readings of M1(a) with the two of F3 reaches GO, "
                "CONDITIONAL_GO and NO_GO alike. What rules out a measured "
                "prior under every cell of that grid is specificity, not "
                "wording -- all three M1(a) readings, and M1(b), also pass on "
                "a population simulated with no latent state. The raw-UMI "
                "sensitivity agrees on counts alone: 65.5% of detected cells "
                "carry exactly one UMI and the median detected value is one "
                "molecule in every unit, so these data do not justify mapping "
                "KLF12 expression onto a measured E_KLF12_HIGH prior."
            ),
            "MaBoSS occupancy is not calibrated adhesion probability.",
            "Same-dataset scRNA conditioning is not validation.",
            "A moved occupancy is not evidence of KLF12 causality.",
        ],
        "model_version": MODEL_VERSION,
        "conditioned_node": NODE,
        "mechanism": (
            "probabilistic [E_KLF12_HIGH].istate line SUBSTITUTED for "
            "baseline.cfg's plain E_KLF12_HIGH.istate = FALSE; on a free "
            "variable; no rule edited"
        ),
        "horizon_class": "converged",
        "converged_phase_horizon": CONVERGED_PHASE_HORIZON,
        "candidate_priors": candidate_priors,
        "runs": [asdict(run) for run in runs],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def candidate_priors(root: Path) -> dict[str, float]:
    """Every per-unit, per-quantile candidate the state derivation produced."""
    import csv

    path = root / "docs" / "scrna" / "klf12_state_evidence.tsv"
    out: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            for key in ("p_q75", "p_q80", "p_q85", "p_q90", "p_q95"):
                out[f"{row['unit_id']}:{key}"] = float(row[key])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--trajectories", type=int, default=DEFAULT_TRAJECTORIES)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument(
        "--grid",
        type=float,
        nargs="+",
        default=list(DEFAULT_GRID),
        help="prior sweep for the one arm whose endpoint is graded",
    )
    args = parser.parse_args(argv)
    root = args.root or repo_root()
    seeds = tuple(args.seeds)

    candidates = candidate_priors(root)
    envelope = {
        "candidate_min": min(candidates.values()),
        "candidate_max": max(candidates.values()),
    }

    runs: list[PriorRun] = []
    # The response curve, on the one arm the identifiability analysis shows is
    # graded in the latent state.
    graded = "hormone_treated"
    priors = {f"grid_{value:g}": value for value in args.grid}
    priors.update(envelope)
    for label, prior in sorted(priors.items(), key=lambda item: item[1]):
        runs.append(
            run_prior(
                graded,
                ARMS[graded],
                prior,
                prior_label=label,
                root=root,
                trajectory_count=args.trajectories,
                seeds=seeds,
            )
        )
    # Every other arm at both extremes -- which `write_response` requires, since
    # the mixture prediction needs them -- plus the largest candidate, so "which
    # arms did not move" is an entry in the table rather than an absence.
    for arm_id, protocol_id in ARMS.items():
        if arm_id == graded:
            continue
        for label, prior in (
            ("grid_0", 0.0),
            ("candidate_max", envelope["candidate_max"]),
            ("grid_1", 1.0),
        ):
            runs.append(
                run_prior(
                    arm_id,
                    protocol_id,
                    prior,
                    prior_label=label,
                    root=root,
                    trajectory_count=args.trajectories,
                    seeds=seeds,
                )
            )

    response = write_response(
        runs, root / "docs" / "scrna" / "klf12_conditioning_response.tsv"
    )
    settings = write_settings(
        runs,
        root / "docs" / "scrna" / "klf12_conditioning_settings.json",
        root=root,
        candidate_priors=candidates,
    )
    print(f"wrote {response.relative_to(root)}")
    print(f"wrote {settings.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
