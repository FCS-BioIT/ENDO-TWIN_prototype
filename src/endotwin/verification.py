"""Assemble the scientific verification report from committed results.

The report answers one question for an external reader: **what has actually been
checked, and what has not?** It therefore keeps five things apart that are easy
to run together:

1. structural correctness of the Boolean network,
2. computational reproducibility,
3. sensitivity to the uncertain rules and transition rates,
4. experimental evidence behind individual mechanisms, and
5. predictions still awaiting experimental evaluation.

Nothing here is computed afresh. Every number is read from an artifact that
``pixi run endotwin-all`` wrote, so the report cannot drift from the results it
describes, and a reader can open the same file. The one thing this module adds
is the arrangement -- and the refusal to let a verified implementation be read
as a validated biology.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from endotwin import DEFAULT_MODEL_VERSION
from endotwin.model import load_model, read_tsv

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "endotwin" / "results"
MODELS = ROOT / "endotwin" / "models"
EVIDENCE = ROOT / "endotwin" / "evidence" / "references.tsv"
PREDICTIONS = ROOT / "endotwin" / "predictions"

#: Readouts a wet-lab arm can measure as a FUNCTION of the tissue, as opposed to
#: the activity of a pathway or the engagement of a drug target. v10 Task 2.1
#: requires the WP2 primary prediction to be one of these.
FUNCTIONAL_READOUTS = {
    "OUT_STROMAL_DECIDUALIZATION",
    "OUT_EPITHELIAL_PROLIFERATION",
    "OUT_EPITHELIAL_SECRETORY",
    "X_PRL",
    "X_IGFBP1",
    "X_PAEP",
}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    return list(read_tsv(path)) if path.is_file() else []


def _h(title: str, level: int = 2) -> str:
    return f"\n{'#' * level} {title}\n"


def _section_structure(structure: dict[str, Any], model: Any) -> str:
    d = structure.get("default", {})
    aliases = [c for c in d.get("alias_classes", []) if len(c) > 1]
    out = [_h("1. Structural correctness of the Boolean network"), "\n"]
    out.append(
        "Exact statements, obtained by enumerating the network rather than by\n"
        "sampling it. They are properties of the rules, not of any simulation.\n"
    )
    out.append(
        f"| Nodes | {d.get('nodes')} |\n|---|---|\n"
        f"| Regulatory dependencies | {d.get('dependencies')} "
        f"({d.get('activations')} activating, {d.get('inhibitions')} inhibiting) |\n"
        f"| Rule-variant families | {len(model.families())} |\n"
        f"| Scenarios (one variant per family) | {len(model.scenarios())} |\n"
        f"| Distinct Boolean functions among the nodes | {d.get('distinct_functions')} |\n"
        f"| Free variables (experimental inputs) | {len(d.get('free_variables', []))} |\n"
    )
    out.append(
        f"\n**{len(aliases)} alias classes.** Nodes inside a class compute the same\n"
        "Boolean function of the inputs, so **no experiment can separate them in\n"
        "this model**. A measured divergence between two members would falsify the\n"
        "aliasing rather than be excluded by it.\n\n"
    )
    for cls in aliases:
        out.append(f"- `{'` = `'.join(cls)}`\n")
    inert = d.get("phenotype_inert_nodes", [])
    unread = d.get("unread_inputs", [])
    if unread:
        out.append(
            f"\n**Unread inputs: {', '.join(f'`{n}`' for n in unread)}.** Declared "
            "because the experimental protocol applies them, read by no rule. The "
            "model is *silent* about them; silence is not a prediction of no "
            "effect (`tests/mainline/test_unmodelled_inputs.py`).\n"
        )
    if inert:
        out.append(
            f"\n**{len(inert)} phenotype-inert nodes** carry no information to any "
            "OUT_* readout under the default rules.\n"
        )
    return "".join(out)


def _section_reproducibility(
    confirmation: dict[str, Any], manifest: dict[str, Any]
) -> str:
    engine = manifest.get("engine", {})
    out = [_h("2. Computational reproducibility"), "\n"]
    out.append(
        "The network is acyclic, so each protocol phase has exactly one fixed\n"
        "point, which can be computed exactly. The stochastic simulation is then\n"
        "checked against that exact answer -- a test of the simulator, not of the\n"
        "biology.\n\n"
    )
    dev = confirmation.get("max_abs_deviation_from_exact_fixed_point")
    out.append(
        f"| Condition-scenario records confirmed | {confirmation.get('records')} |\n"
        f"|---|---|\n"
        f"| Trajectories per record | {confirmation.get('sample_count')} |\n"
        f"| Max deviation from the exact fixed point | {dev} |\n"
        f"| Phases that failed to converge | {confirmation.get('unconverged_phases')} |\n"
        f"| Engine | {engine.get('package', 'maboss')} {engine.get('version', '')} "
        f"({engine.get('backend', '')}) |\n"
    )
    out.append(
        "\nEvery result file carries the SHA-256 of the network text it was produced\n"
        "from, the seed and the trajectory count, so any row can be traced to the\n"
        "exact rules that generated it. `pixi run endotwin-all` regenerates all of\n"
        "them.\n"
    )
    return "".join(out)


def _section_sensitivity(rates: dict[str, Any]) -> str:
    out = [_h("3. Sensitivity to uncertain rules and transition rates"), "\n"]
    agreement = rates.get("all_agreement_fraction")
    scenario = rates.get("scenario", "")
    out.append(
        f"| Random rate sets | {rates.get('samples')} |\n|---|---|\n"
        f"| Rate range sampled (log-uniform, per node, up and down) | "
        f"{rates.get('rate_range')} |\n"
        f"| Trajectories per record | {rates.get('sample_count')} |\n"
        f"| Records | {rates.get('records')} |\n"
    )
    shown = f"{agreement:.0%}" if isinstance(agreement, (int, float)) else agreement
    out.append(f"| Records whose predicted direction is unchanged | {shown} |\n")
    if scenario:
        out.append(
            f"\n**Scope: one scenario.** The rate ensemble was run on "
            f"`{scenario}`\nonly -- the default variant of every family -- not on all "
            "scenarios. Rule\nuncertainty is covered separately and exactly, by "
            "enumerating every\nscenario (section 5); this section covers rate "
            "uncertainty within one of\nthem.\n"
        )
    out.append(
        "\n**Read the rest narrowly too.** It says the predicted *directions*\n"
        "survive the rate sets that were sampled, within the stated range. It is\n"
        "not a claim about rates outside that range, about magnitudes, or about\n"
        "timing. The network is acyclic, so its fixed points cannot depend on\n"
        "transition rates or on the initial state at all; what the sampling probes\n"
        "is whether a finite phase reaches them.\n"
    )
    return "".join(out)


def _section_evidence(edges: list[dict[str, str]], refs: list[dict[str, str]]) -> str:
    classes = Counter(e.get("evidence_class", "") for e in edges)
    depth = Counter(
        (r.get("evidence_depth", "") or "unrecorded").split(" ")[0] for r in refs
    )
    out = [_h("4. Experimental evidence behind individual mechanisms"), "\n"]
    out.append(
        "Every edge carries an evidence class. The classes are not a quality\n"
        "score; they record **what kind of statement the source supports**.\n\n"
    )
    out.append("| Evidence class | Edges |\n|---|---|\n")
    for name, n in sorted(classes.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"| `{name}` | {n} |\n")
    out.append(
        f"\n**{len(refs)} registered references**, by how deeply each was read:\n\n"
    )
    out.append("| Depth | References |\n|---|---|\n")
    for name, n in sorted(depth.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"| `{name}` | {n} |\n")
    weak = [
        e
        for e in edges
        if e.get("evidence_class")
        in {"simplifying_assumption", "literature_supported_species_transfer"}
        and e.get("in_default_network") == "true"
    ]
    if weak:
        out.append(
            f"\n**{len(weak)} default edges rest on a simplifying assumption or on "
            "species transfer**, and are the first place a disagreement with WP1 "
            "data should be looked for:\n\n"
        )
        for e in weak:
            out.append(
                f"- `{e['edge_id']}` {e['source']} → {e['target']} "
                f"(`{e['evidence_class']}`)\n"
            )
    return "".join(out)


def _unfunded_inputs(model: Any) -> set[str]:
    """Inputs the node dictionary itself marks as outside the funded protocol.

    Derived rather than listed here, so a reagent that later enters the plan
    stops being counted the moment its description says so.
    """
    return {
        node
        for node, info in model.node_info.items()
        if "not in the funded protocol" in info.get("biological_meaning", "")
    }


def _candidate_only_comparisons(model: Any) -> set[str]:
    """Comparisons whose perturbed arm needs a reagent that is not funded."""
    # Deliberately not guarded: if the protocols cannot be read, the report must
    # fail rather than quietly report every family as funded.
    from endotwin.protocols import load_protocols

    protocols = load_protocols(model)
    unfunded = _unfunded_inputs(model)
    out = set()
    for comparison_id, comparison in protocols.comparisons.items():
        condition = protocols.conditions.get(comparison.perturbed)
        if condition is None:
            continue
        if any(
            phase.inputs.get(node) for phase in condition.phases for node in unfunded
        ):
            out.add(comparison_id)
    return out


def _section_discrimination(discrimination: list[dict[str, str]], model: Any) -> str:
    out = [_h("5. Which competing hypotheses the planned perturbations separate"), "\n"]
    by_family: dict[str, set[str]] = {}
    functional: dict[str, set[str]] = {}
    for row in discrimination:
        if row.get("discrimination") != "robust":
            continue
        fam = row["family"]
        by_family.setdefault(fam, set()).add(row["comparison"])
        if row.get("readout_node") in FUNCTIONAL_READOUTS:
            functional.setdefault(fam, set()).add(row["comparison"])
    families = sorted(model.families())
    candidate_only = _candidate_only_comparisons(model)
    funded: dict[str, set[str]] = {
        fam: comps - candidate_only for fam, comps in by_family.items()
    }
    out.append(
        f"The model carries **{len(families)} hypothesis families**. A family is\n"
        "separated when some comparison predicts opposite directions for its\n"
        "variants in every rule scenario and under every sampled rate set.\n\n"
        "**Funded** means the perturbed arm needs no reagent the node dictionary\n"
        "marks as outside the funded protocol. That distinction matters: a family\n"
        "separable only by an unfunded candidate is not resolved by the work plan\n"
        "as it stands.\n\n"
    )
    out.append(
        "| Family | Variants | Separated by a funded arm? | Only by a candidate? "
        "| By a functional readout? |\n"
    )
    out.append("|---|---|---|---|---|\n")
    for fam in families:
        variants = len(model.families()[fam])
        has_funded = bool(funded.get(fam))
        only_candidate = bool(by_family.get(fam)) and not has_funded
        out.append(
            f"| `{fam}` | {variants} | {'yes' if has_funded else '**no**'} | "
            f"{'**yes**' if only_candidate else 'no'} | "
            f"{'yes' if functional.get(fam) else 'no'} |\n"
        )
    n_funded = sum(1 for f in families if funded.get(f))
    unresolved = [f for f in families if not by_family.get(f)]
    candidate_families = [f for f in families if by_family.get(f) and not funded.get(f)]
    out.append(
        f"\n**{n_funded} of {len(families)} families are separated by an arm the "
        "work plan funds.**\n"
    )
    if candidate_families:
        out.append(
            "Separable only by a candidate perturbation that is not in the funded "
            "protocol: "
            + ", ".join(f"`{f}`" for f in candidate_families)
            + ". The work plan as written does not decide "
            + ("it" if len(candidate_families) == 1 else "them")
            + ", so any prediction resting on "
            + ("that family" if len(candidate_families) == 1 else "those families")
            + " stays conditional.\n"
        )
    if unresolved:
        out.append(
            "Separated by nothing at all: "
            + ", ".join(f"`{f}`" for f in unresolved)
            + ".\n"
        )
    out.append(
        "\n**These are model scenarios, not biological replicates.** A scenario is\n"
        "one combination of competing rules, enumerated exhaustively on a computer.\n"
        "It carries no donor, no chip and no measurement, and the count must never\n"
        "be reported as a sample size. The biological unit is the donor.\n"
    )
    return "".join(out)


def _section_pending(model: Any) -> str:
    drafts = sorted((PREDICTIONS / "drafts").glob("*.yaml"))
    frozen = sorted((PREDICTIONS / "frozen").glob("*.yaml"))
    out = [_h("6. Predictions awaiting experimental evaluation"), "\n"]
    out.append(
        f"| Frozen prediction records | {len(frozen)} |\n|---|---|\n"
        f"| Drafts, not frozen | {len(drafts)} |\n"
    )
    out.append(
        "\nNothing has been evaluated against experimental data. The proposal\n"
        "freezes the WP2 prediction at the end of WP1, before the first validation\n"
        "experiment; freezing earlier would lock in a model that has not seen the\n"
        "WP1 data.\n"
    )
    for path in drafts:
        out.append(f"\n- `{path.relative_to(ROOT)}` (draft)")
    if drafts:
        out.append("\n")
    return "".join(out)


def build_report(version: str = DEFAULT_MODEL_VERSION) -> str:
    model = load_model(version)
    out = RESULTS / version
    structure = _load_json(out / "structure.json")
    confirmation = _load_json(out / "maboss_confirmation_summary.json")
    manifest = _load_json(out / "run_manifest.json")
    rates = _load_json(out / "rate_sensitivity_summary.json")
    edges = _rows(MODELS / version / "edges.tsv")
    refs = _rows(EVIDENCE)
    discrimination = _rows(out / "discrimination.tsv")

    parts = [
        f"# Scientific verification report — `{version}`\n",
        (
            "\nGenerated by `pixi run endotwin-verification-report` from the committed\n"
            "results. Do not edit by hand.\n"
        ),
        (
            "\n> **Computational verification is not biological validation.** Everything\n"
            "> below checks that the implementation computes what the stated rules say it\n"
            "> should, and that the conclusions survive the uncertainties that were\n"
            "> examined. The model has **not** been calibrated against experimental data\n"
            "> and **no** prediction has been evaluated prospectively. MaBoSS\n"
            "> probabilities are simulated trajectory frequencies under stated rules,\n"
            "> rates and initial conditions: not concentrations, not cell fractions, not\n"
            "> clinical probabilities. MaBoSS time is not experimental time.\n"
        ),
        _section_structure(structure, model),
        _section_reproducibility(confirmation, manifest),
        _section_sensitivity(rates),
        _section_evidence(edges, refs),
        _section_discrimination(discrimination, model),
        _section_pending(model),
    ]
    return "".join(parts)


def write_report(version: str = DEFAULT_MODEL_VERSION) -> Path:
    path = RESULTS / version / "verification_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_report(version), encoding="utf-8")
    return path
