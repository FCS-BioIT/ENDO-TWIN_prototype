"""Run the whole concordance build and write every tracked artifact.

One entry point so the analysis is reproduced by one command rather than by a
remembered sequence. Everything it writes lives under `docs/concordance/` and
`docs/assets/`, both tracked, because `output/` is gitignored and an analysis
whose evidence is untracked cannot be checked by a reader.

The arm and contrast tables below are the only place a result id is tied to a
simulation. They are data, deliberately: a reader checking whether R41b really
describes the hormone-treated adhesion arm reads one dict rather than tracing
control flow.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from dt_adoc.concordance.mechanism import node_records
from dt_adoc.concordance.simulate import (
    DEFAULT_SEEDS,
    DEFAULT_TRAJECTORIES,
    ArmRun,
    run_arm,
    run_provenance,
    write_run_settings,
)
from dt_adoc.concordance.table import build_rows, write_table
from dt_adoc.model.provenance import repo_root
from dt_adoc.reporting.structure import load_structure

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
OUTPUT_DIR = Path("docs") / "concordance"
RUN_SETTINGS = OUTPUT_DIR / "run_settings.json"
CONCORDANCE_TABLE = OUTPUT_DIR / "concordance_table.tsv"
MECHANISM_NODES = OUTPUT_DIR / "mechanism_nodes.tsv"
FIGURE_SOURCE_DATA = OUTPUT_DIR / "figure_source_data.tsv"

#: Arms to simulate: an id, the protocol that realises it, and why it is here.
ARMS: dict[str, str] = {
    # The three adhesion arms the manuscript compares.
    "untreated": "adhesion_challenge_basal",
    "hormone_treated": "adhesion_challenge_hormone_treated",
    "mifepristone": "adhesion_challenge_hormone_treated_mifepristone",
    # The maternal-only arms the secreted-protein comparisons use. Adhesion
    # challenge phases are absent from these by design: PAEP and IGFBP-1 were
    # measured without an embryo.
    "basal_maternal": "basal_maternal",
    "e2_primed_maternal": "e2_primed_maternal",
    "hormone_treated_maternal": "hormone_treated_maternal",
}

#: Which arm supplies a curated row's regenerated simulated value.
ARM_OF_RESULT: dict[str, str] = {
    "R12a": "hormone_treated_maternal",
    "R12b": "hormone_treated_maternal",
    "R12c": "hormone_treated_maternal",
    "R15a": "hormone_treated_maternal",
    "R15b": "hormone_treated_maternal",
    "R41a": "hormone_treated",
    "R41b": "hormone_treated",
    "R42": "untreated",
    "R43a": "mifepristone",
    "R43b": "mifepristone",
    "R54": "hormone_treated_maternal",
    "R55": "hormone_treated",
}

#: The two arms whose difference a row's carrying path describes. R44 compares
#: three arms and is deliberately absent: a three-arm ordering has no single
#: contrast, and inventing one would misstate what the row asserts.
CONTRAST_OF_RESULT: dict[str, tuple[str, str]] = {
    "R12a": ("basal_maternal", "hormone_treated_maternal"),
    "R12b": ("basal_maternal", "hormone_treated_maternal"),
    "R12c": ("basal_maternal", "hormone_treated_maternal"),
    "R15a": ("e2_primed_maternal", "hormone_treated_maternal"),
    "R15b": ("e2_primed_maternal", "hormone_treated_maternal"),
    "R41a": ("untreated", "hormone_treated"),
    "R41b": ("untreated", "hormone_treated"),
    "R42": ("untreated", "hormone_treated"),
    "R43a": ("hormone_treated", "mifepristone"),
    "R43b": ("hormone_treated", "mifepristone"),
    "R55": ("untreated", "hormone_treated"),
}

#: Rows promoted to ``structural_falsification``. **Deliberately empty.**
#:
#: An earlier revision promoted R43b here on the grounds that
#: ``E_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE`` (likewise ``S_PGR``) makes
#: ``OUT_STABLE_ADHESION`` false in all 524,288 assignments whenever
#: ``IN_MIFEPRISTONE`` is set, so the observed 1/8 had zero likelihood. That
#: argument is wrong, and the run artifact refutes it: the *target function* is 0
#: under sustained mifepristone, but MaBoSS simulates asynchronous stochastic
#: dynamics, and at the declared horizon the same arm records
#: ``OUT_STABLE_ADHESION = 0.000050`` -- transient occupancy carried in from the
#: hormone-conditioned state. A finite-horizon observable probability is
#: therefore not zero, and it depends on rates, initial states and horizon, none
#: of which the Boolean enumeration constrains.
#:
#: The class is kept in the vocabulary rather than deleted so that its emptiness
#: is visible: this analysis found no structural falsification. What it found is
#: a magnitude failure, which is a weaker and more accurate claim.
STRUCTURAL_FALSIFICATION_IDS: dict[str, str] = {}

#: Rows whose simulated arm does not implement the regimen the evidence records.
#:
#: REPAIRED 2026-09-13. This block previously documented a wiring defect: every
#: named perturbation challenge was seeded from ``hormone_treated_maternal``,
#: the UNPERTURBED hormone-treated terminal joint state, so the perturbation
#: switched on at the same instant as the embryo. `SOFIA-HT-002` records the
#: opposite -- 10 uM mifepristone for 24 h AFTER the six-day protocol and
#: BEFORE the adhesion assay, acting on maternal tissue while no embryo is
#: present. The superset clone layer now seeds each challenge from the maternal
#: phase whose name it carries, so the executed chain is
#:
#:     basal_maternal -> e2_primed_maternal -> hormone_treated_maternal
#:         -> hormone_treated_mifepristone
#:         -> adhesion_challenge_hormone_treated_mifepristone
#:
#: and the regimen mismatch that made R43a unassessable is GONE.
#:
#: R43a is nonetheless still unassessable, for a DIFFERENT and now MEASURED
#: reason, and the distinction matters because the old reason must not be
#: carried over as though it still applied. The declared horizon reads the
#: endpoint roughly 4000x before its fixed point
#: (`docs/endpoint_convergence_finding.md`), and at that horizon the repaired
#: arm has no stable value to compare against. Measured at 20000 trajectories
#: across seeds 1-5:
#:
#:     seed   pre-repair chain     repaired chain
#:     1      0.00005              0.0
#:     2      0.00005              0.00000025047226105073816
#:     3      0.00005              0.0
#:     4      0.00005              0.00005025047226105073
#:     5      0.00005              0.00005025047226105073
#:
#: The across-seed spread of the repaired arm is the same size as the value
#: itself, ranging over two orders of magnitude including exact zeros. A
#: comparison against an observed 1/8 = 0.125 is not meaningful against a
#: quantity that unstable, so R43a stays unassessable with its reason rewritten
#: rather than being promoted to a comparison.
#:
#: Two incidental facts worth keeping, because both misled earlier revisions.
#: The pre-repair arm reported exactly 0.00005 = 1/20000 in all five seeds,
#: which is the coincidence behind the withdrawn "one trajectory in 20,000"
#: reading. The repaired values are not multiples of 1/20000 at all, which is
#: what `docs/maboss_estimator_semantics.md` predicts: the estimator is a
#: time-averaged occupancy, never a path count.
#:
#: R43b is UNMOVED by the repair, and that is now measured rather than argued.
#: The converged endpoint is 0.0 in all five seeds at 20000 trajectories on
#: BOTH chains, which supersedes the earlier 3-seed/2000-trajectory
#: counterfactual the row used to rest on. Its held-out direction agreement and
#: magnitude disagreement therefore survive the repair unchanged -- and now
#: without a regimen caveat attached, which strengthens the row.
#:
#: The text below is derived from the resolved protocol graph at build time, so
#: it cannot go stale if the wiring changes again; `_regimen_mismatch` raises if
#: the repair is ever reverted without this block being revisited.
#: Result ids this layer forces to ``not_assessable``, each with WHY.
#:
#: A mapping rather than a set, and renamed from ``REGIMEN_UNASSESSABLE``,
#: because the old name encoded a reason in an identifier and the reason then
#: changed underneath it. R43a was unassessable because the simulated regimen
#: was not the experiment's; the wiring repair fixed that, and the name went on
#: asserting a defect that no longer existed. Encoding the reason as data means
#: the next change of reason edits a value instead of silently invalidating a
#: name -- and the reason travels with the id to every surface that reads it.
UNASSESSABLE_RESULT_IDS: dict[str, str] = {
    "R43a": (
        "horizon instability, not regimen: the declared horizon reads ~4000x "
        "before the fixed point and the arm's across-seed spread is the size of "
        "its value, including exact zeros"
    ),
}

#: The maternal phase the recorded regimen requires, and which the executed
#: chain for the mifepristone arm is checked against. Named once so the test
#: suite and the generated narrative refer to the same protocol id.
MATERNAL_MIFEPRISTONE_PROTOCOL = "hormone_treated_mifepristone"


def _regimen_mismatch(
    *, model_version: str = MODEL_VERSION, root: Path | None = None
) -> dict[str, str]:
    """Build the per-row regimen text from the resolved protocol graph.

    Derived rather than typed. A hand-written predecessor asserted that
    `config/protocols.yaml` contained no maternal mifepristone phase, which was
    false. A sentence nothing recomputes is free to be wrong about the
    repository it describes, so the chain is read from `protocol_lineage` here.

    Raises if the repair is reverted without this text being revisited: a
    fidelity note claiming the regimen matches after the bypass returns would be
    the same failure in the opposite direction.
    """
    from dt_adoc.concordance.simulate import protocol_lineage

    lineage = protocol_lineage(
        ARMS["mifepristone"], model_version=model_version, root=root
    )
    chain = " -> ".join(lineage)
    if MATERNAL_MIFEPRISTONE_PROTOCOL not in lineage:
        raise ValueError(
            f"{MATERNAL_MIFEPRISTONE_PROTOCOL!r} is no longer in the executed "
            f"chain ({chain}): the maternal-perturbation wiring repair has been "
            "reverted, so the R43a/R43b text below describes a regimen the "
            "model does not run. Re-derive both rows against the actual wiring."
        )
    seeded_from = lineage[-2] if len(lineage) > 1 else "the model baseline"
    return {
        "R43a": (
            "matches the recorded regimen. The executed chain is "
            f"{chain}, so the embryo challenge is seeded from the terminal "
            f"joint state of {seeded_from} and mifepristone has acted on "
            "maternal tissue before any embryo is present, which is what "
            "SOFIA-HT-002 records. The row is nonetheless NOT assessable, for "
            "a reason that is about the horizon rather than the regimen: the "
            "declared horizon reads the endpoint roughly 4000x before its "
            "fixed point, and at that horizon this arm has no stable value. "
            "Measured at 20000 trajectories, seeds 1-5 give 0.0, "
            "0.00000025047226105073816, 0.0, 0.00005025047226105073 and "
            "0.00005025047226105073 -- a spread the size of the value itself, "
            "including exact zeros. Comparing that against an observed "
            "1/8 = 0.125 would not be meaningful. Before the wiring repair this "
            "row was unassessable because the simulated regimen was not the "
            "experiment's; that defect is fixed and this reason replaces it, "
            "rather than being added to it."
        ),
        "R43b": (
            "matches the recorded regimen, and the converged endpoint is "
            "unmoved by the repair that achieved it. Measured, not argued: the "
            "converged value is 0.0 across seeds 1-5 at 20000 trajectories on "
            "the repaired chain AND on the pre-repair chain that bypassed the "
            "maternal phase. That supersedes the earlier 3-seed, 2000-trajectory "
            "counterfactual this row rested on. The structural reason is "
            "unchanged and independent, and is asymptotic: each phase runs to "
            "its logical fixed point and the network is a DAG over its free "
            "variables, so the fixed point under a sustained input assignment is "
            "unique and independent of the starting state. No claim of exact "
            "invariance beyond those runs is made: fixed seeds give "
            "reproducibility, not Monte Carlo stability. On that evidence BOTH "
            "the direction and the magnitude failure survive, and they now carry "
            "no regimen caveat at all. R43a, the declared-horizon transient, is "
            "the row that stays unassessable, on its own separate reason."
        ),
    }


def _write_mechanism_nodes(facts, destination: Path) -> Path:
    """Per-node evidence class and degeneracy, the figure's node encoding."""
    import csv

    records = node_records(facts, model_version=MODEL_VERSION)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "node_id",
        "label",
        "compartment",
        "evidence_class",
        "declared_confidence",
        "phenotype_inert",
        "alias_of",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for node_id in facts.node_ids:
            record = records[node_id]
            payload = asdict(record)
            payload["alias_of"] = ";".join(record.alias_of)
            payload["phenotype_inert"] = str(record.phenotype_inert).lower()
            writer.writerow(payload)
    return destination


def run(
    *,
    root: Path | None = None,
    trajectories: int = DEFAULT_TRAJECTORIES,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
) -> dict[str, Path]:
    """Execute the build. Returns the artifacts written, by role."""
    active_root = root or repo_root()
    facts = load_structure(MODEL_VERSION, active_root)

    # Resolved BEFORE anything is simulated or written. `_regimen_mismatch`
    # raises when the mifepristone wiring is repaired, and a guard that fires
    # after `write_run_settings` would abort a build that had already replaced
    # the tracked `run_settings.json`, leaving `concordance_table.tsv` stale
    # against a newer run record. Failing here costs a re-run and leaves every
    # tracked artifact consistent with each other.
    regimen_mismatch = _regimen_mismatch(root=active_root)

    runs: dict[tuple[str, str], ArmRun] = {}
    for arm_id, protocol_id in ARMS.items():
        for horizon in ("declared", "converged"):
            runs[(arm_id, horizon)] = run_arm(
                arm_id,
                protocol_id,
                horizon_class=horizon,
                model_version=MODEL_VERSION,
                root=active_root,
                trajectory_count=trajectories,
                seeds=seeds,
            )

    provenance = run_provenance(
        model_version=MODEL_VERSION,
        root=active_root,
        trajectory_count=trajectories,
        seeds=seeds,
    )
    settings_path = write_run_settings(
        provenance, list(runs.values()), active_root / RUN_SETTINGS
    )

    rows = build_rows(
        facts=facts,
        runs=runs,
        arm_of_result=ARM_OF_RESULT,
        contrast_of_result=CONTRAST_OF_RESULT,
        structural_ids=set(STRUCTURAL_FALSIFICATION_IDS),
        regimen_mismatch=regimen_mismatch,
        unassessable_result_ids=UNASSESSABLE_RESULT_IDS,
        artifact_pointer=str(RUN_SETTINGS),
        root=active_root,
    )
    table_path = write_table(rows, active_root / CONCORDANCE_TABLE)
    mechanism_path = _write_mechanism_nodes(facts, active_root / MECHANISM_NODES)

    from dt_adoc.concordance.figure import write_figure_source_data

    figure_data_path = write_figure_source_data(
        rows=rows,
        runs=runs,
        facts=facts,
        destination=active_root / FIGURE_SOURCE_DATA,
    )

    return {
        "run_settings": settings_path,
        "concordance_table": table_path,
        "mechanism_nodes": mechanism_path,
        "figure_source_data": figure_data_path,
    }


def main() -> None:  # pragma: no cover - thin CLI
    written = run()
    print(json.dumps({k: str(v) for k, v in written.items()}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
