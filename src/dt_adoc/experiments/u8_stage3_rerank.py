"""U8: the frozen Stage-3 experiment selection, recomputed against adopted v0.5.1.

`docs/scrna/node_support_finding.md` §8 made the rerank mandatory and declined to
predict it: "Whether `dropout_e2` remains best is an output of the new model".
`docs/v05_mechanistic_integration_plan.md` §14 fixes the protocol, and this
module is that protocol and nothing wider:

1. **The same computation.** `stage3_design.evaluate` is called with the model
   version as its only argument. The forks, the sixteen experiments, their
   curated cost declarations and `_readout_tier` -- which reads
   `config/observation_model_map.tsv` and nothing else -- are the objects the
   frozen v0.4 analysis used, not copies of them. `config/candidate_score.yaml`
   is not read (§14).
2. **The frozen result is read, never rewritten.** The v0.4 side of every
   comparison is parsed from the committed
   `docs/experiments/stage3_experiment_design.tsv`, and the build refuses to run
   if a fresh v0.4 evaluation no longer reproduces that file.
3. **Three reported objects** (§14 item 3, the source of §17's "three rankings"):
   the frozen v0.4 ranking, the v0.5.1 ranking, and the per-arm delta.
4. **No new ranking criterion.** Stage-3 never emitted a scalar score: its
   ordering is `stage3_experiment_selection.md` §3 and §6 arguing over computed
   columns and curated declarations. So the v0.5.1 ranking is not re-scored here.
   Each computed premise that ordering cites is re-evaluated on both models. If
   every premise is unchanged the frozen ordering carries over; if any one moves,
   the build reports `READJUDICATION_REQUIRED` instead of inventing an order.

The mandate is conditional. It exists because `AC01` is `alias_challenged`, and
that verdict depends on the post-extraction deviation D1; without D1, `AC01` is
`unclassified_by_section_5_4` and the rerank is optional rather than owed. The
condition is read from `docs/scrna/node_support_findings.json`, carried into the
summary verbatim and never re-adjudicated here.

Nothing here simulates or edits a model. Every number is an exact Boolean
marginal, exactly as in Stage 3.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path

from dt_adoc.experiments import stage3_design
from dt_adoc.experiments.stage3_design import (
    EXPERIMENTS,
    FORKS,
    TSV_COLUMNS,
    _class_rules,
    _experiment_inputs,
    _marginals,
    _rows,
    _scrna_can_alter_a_readout_tier,
    evaluate,
    render,
)
from dt_adoc.experiments.variant_discrimination import (
    MAPPED_COMPOSITE,
    NO_ASSAY,
    USABLE_ASSAY,
    _readout_tier,
)
from dt_adoc.reporting.identifiability import (
    _observed_arms,
    load_identifiability,
    parse_bnd_rules,
    repo_root,
    resolve_model,
)
from dt_adoc.reporting.structure import load_structure

FROZEN_VERSION = stage3_design.MODEL_VERSION
ADOPTED_VERSION = "adoc-literature-superset-v0.5.1"
TASK = "build-u8-stage3-rerank"

#: The frozen Stage-3 artifacts. Read, never written.
FROZEN_TSV = stage3_design.OUT_TSV
FROZEN_MD = stage3_design.OUT_MD
FROZEN_TABLES = stage3_design.OUT_TABLES
FROZEN_SELECTION = Path("docs/stage3_experiment_selection.md")

OUT_DIR = Path("docs/experiments/u8_stage3_rerank")
OUT_DESIGN_MD = OUT_DIR / "stage3_experiment_design_v0.5.1.md"
OUT_DESIGN_TSV = OUT_DIR / "stage3_experiment_design_v0.5.1.tsv"
OUT_PER_ARM = OUT_DIR / "per_arm_rerank.tsv"
OUT_PAIRS = OUT_DIR / "pair_separation_delta.tsv"
OUT_SUMMARY = OUT_DIR / "u8_rerank_summary.json"
OUT_REPORT = OUT_DIR / "u8_rerank_report.md"
OUTPUTS = (
    OUT_DESIGN_MD,
    OUT_DESIGN_TSV,
    OUT_PER_ARM,
    OUT_PAIRS,
    OUT_SUMMARY,
    OUT_REPORT,
)

OBSERVATION_MAP = Path("config/observation_model_map.tsv")
SCRNA_MAP = Path("config/scrna_observation_map.tsv")
#: Named so a test can prove it is never opened, not so it can be read.
NOT_READ_CANDIDATE_SCORE = Path("config/candidate_score.yaml")
D1_SOURCE = Path("docs/scrna/node_support_findings.json")
U6B_CATALOG = Path("docs/u6b_muc1_reconciliation/rule_variants.tsv")

#: The frozen ordering, as `stage3_experiment_selection.md` states it. Curated
#: positions, quoted with their section, not computed: Stage 3 never produced a
#: score, and writing one now would be the new criterion §14 forbids.
FROZEN_ORDERING = (
    ("recommended", "dropout_e2", "§3"),
    ("runner_up", "smo_antagonist", "§6"),
    ("third_explicitly_not_recommended", "dropout_camp", "§6"),
    ("prerequisite_registration_not_run", "observe_e2_primed", "§3"),
)

READJUDICATION_REQUIRED = "READJUDICATION_REQUIRED"
CARRIED_OVER = "CARRIED_OVER_UNCHANGED"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tsv_text(report: dict) -> str:
    """The Stage-3 TSV exactly as `stage3_design.build` writes it."""
    return _tsv(TSV_COLUMNS, _rows(report))


def _read_tsv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text), delimiter="\t"))


def _split(cell: str) -> list[str]:
    return [x for x in cell.split(";") if x]


# --------------------------------------------------------------------------
# Per-arm profile, derived from the Stage-3 TSV alone
# --------------------------------------------------------------------------
#
# The same derivation is applied to the frozen v0.4 file and to the freshly
# generated v0.5.1 file, so "the v0.4 ranking" is read from the immutable
# artifact rather than from a re-evaluation that could itself have drifted.

PROFILE_FIELDS = (
    "forks_separated_any",
    "forks_separated_usable_assay",
    "forks_separated_mapped_composite",
    "forks_separated_no_assay_only",
    "forks_separated_usable_opposite",
    "usable_assay_pairs",
    "usable_assay_nodes",
    "committed_model_propagates",
    "in_candidate_set",
)


def arm_profiles(
    rows: list[dict[str, str]], tiers: dict[str, tuple[str, str]]
) -> dict[str, dict[str, str]]:
    """Per arm: every column the frozen ordering argues from, as strings.

    The tier of a separating node is looked up in the same `_readout_tier`
    mapping Stage 3 used; the TSV stores usable nodes explicitly and the rest by
    name, so `mapped_composite` and `no_assay` are recovered from the map.
    """
    out: dict[str, dict[str, str]] = {}
    for experiment in EXPERIMENTS:
        mine = [r for r in rows if r["experiment"] == experiment.experiment_id]
        by_fork: dict[str, list[dict[str, str]]] = {}
        for r in mine:
            by_fork.setdefault(r["fork"], []).append(r)
        any_, usable, composite, no_assay_only, opposite = [], [], [], [], []
        for fork_id, fork_rows in by_fork.items():
            hits = [n for r in fork_rows for n in _split(r["separating_nodes"])]
            if not hits:
                continue
            any_.append(fork_id)
            node_tiers = {tiers.get(n, (NO_ASSAY, ""))[0] for n in hits}
            if any(_split(r["usable_assay_nodes"]) for r in fork_rows):
                usable.append(fork_id)
            elif MAPPED_COMPOSITE in node_tiers:
                composite.append(fork_id)
            if node_tiers == {NO_ASSAY}:
                no_assay_only.append(fork_id)
            if any(_split(r["usable_assay_opposite_nodes"]) for r in fork_rows):
                opposite.append(fork_id)
        pairs = [
            f"{r['fork']}:{r['left_class']}/{r['right_class']}"
            for r in mine
            if _split(r["usable_assay_nodes"])
        ]
        nodes = sorted({n for r in mine for n in _split(r["usable_assay_nodes"])})
        propagates = {r["committed_model_changes_anything"] for r in mine}
        assert len(propagates) == 1, experiment.experiment_id
        out[experiment.experiment_id] = {
            "forks_separated_any": ",".join(sorted(any_)),
            "forks_separated_usable_assay": ",".join(sorted(usable)),
            "forks_separated_mapped_composite": ",".join(sorted(composite)),
            "forks_separated_no_assay_only": ",".join(sorted(no_assay_only)),
            "forks_separated_usable_opposite": ",".join(sorted(opposite)),
            "usable_assay_pairs": ";".join(pairs),
            "usable_assay_nodes": ";".join(nodes),
            "committed_model_propagates": propagates.pop(),
            "in_candidate_set": str(bool(usable)),
        }
    return out


# --------------------------------------------------------------------------
# The computed premises of the frozen ordering
# --------------------------------------------------------------------------
#
# Each premise is one that `stage3_experiment_selection.md` §3/§6 argues from
# and that `tests/unit/test_stage3_design.py` pins for v0.4. Each returns a
# JSON-able VALUE, not a pass/fail, so a changed premise shows what it changed
# to.


def _fork(report: dict, experiment_id: str, fork_id: str) -> dict:
    result = next(r for r in report["results"] if r["experiment"] == experiment_id)
    return next(f for f in result["forks"] if f["fork"] == fork_id)


def _reached(report: dict, experiment_id: str, fork_id: str) -> list[str]:
    return sorted(
        f"{p['left']} vs {p['right']}"
        for p in _fork(report, experiment_id, fork_id)["pairs"]
        if p["hits"]
    )


def _premises(report: dict) -> list[dict]:
    by_id = {r["experiment"]: r for r in report["results"]}
    usable_nodes = sorted(
        n for n, (t, _) in report["readout_tiers"].items() if t == USABLE_ASSAY
    )

    def usable_nodes_of(result: dict) -> set[str]:
        return {
            h["node"] for f in result["forks"] for p in f["pairs"] for h in p["usable"]
        }

    sec_usable_counts = {
        r["experiment"]: sum(
            1 for p in _fork(report, r["experiment"], "SEC")["pairs"] if p["usable"]
        )
        for r in report["results"]
    }
    top = max(sec_usable_counts.values())
    sec = _fork(report, "dropout_e2", "SEC")
    against = {
        p["right"]: sorted(h["node"] for h in p["usable_opposite"])
        for p in sec["pairs"]
        if p["left"] == "SEC-a" and p["usable_opposite"]
    }
    exists = {USABLE_ASSAY, MAPPED_COMPOSITE}
    unreached = sorted(
        f"{fork['fork']}:{pair['left']} vs {pair['right']}"
        for fork in report["results"][0]["forks"]
        if fork["fork"] == "SEC"
        for pair in fork["pairs"]
        if not any(
            h["readout_tier"] in exists
            for r in report["results"]
            for f in r["forks"]
            if f["fork"] == "SEC"
            for p in f["pairs"]
            if (p["left"], p["right"]) == (pair["left"], pair["right"])
            for h in p["hits"]
        )
    )
    hh = _fork(report, "smo_antagonist", "HH")
    return [
        {
            "id": "P1_usable_readouts",
            "cited_by": "§3 Readouts; test_only_two_maternal_nodes_carry_a_usable_assay",
            "value": usable_nodes,
        },
        {
            "id": "P2_only_arm_on_both_usable_readouts",
            "cited_by": "§3 Readouts; test_dropout_e2_is_the_only_arm_separating_both_usable_assays",
            "value": sorted(
                r["experiment"]
                for r in report["results"]
                if set(usable_nodes) <= usable_nodes_of(r)
            ),
        },
        {
            "id": "P3_dropout_e2_opposite_against_committed",
            "cited_by": "§3 Mechanisms separated; test_dropout_e2_separates_the_committed_class_from_every_other",
            "value": against,
        },
        {
            "id": "P4_most_sec_pairs_on_usable_assay",
            "cited_by": "§3 'More SEC class pairs on a usable assay than any other candidate'",
            "value": {
                "counts": {k: v for k, v in sorted(sec_usable_counts.items()) if v},
                "arms_at_maximum": sorted(
                    k for k, v in sec_usable_counts.items() if v == top
                ),
            },
        },
        {
            "id": "P5_e2_only_arms_reach_only_sec_c_pairs",
            "cited_by": "§3; test_the_e2_only_arms_resolve_only_whether_sec_c_survives",
            "value": {
                x: _reached(report, x, "SEC")
                for x in ("observe_e2_primed", "add_hcg_on_e2")
            },
        },
        {
            "id": "P6_sec_pairs_unreached_at_a_readout_that_exists",
            "cited_by": "§3 'exactly one pair unreached'; §7",
            "value": unreached,
        },
        {
            "id": "P7_dropout_e2_decision_table",
            "cited_by": "§5; test_the_four_outcome_decision_table_is_what_the_model_predicts",
            "value": {
                cid: {n: values[n] for n in usable_nodes}
                for cid, values in sorted(sec["predictions"].items())
            },
        },
        {
            "id": "P8_runner_up_propagates_nowhere",
            "cited_by": "§6 point 1 (decisive); test_xav939_and_smo_propagate_nowhere_in_the_committed_model",
            "value": {
                x: by_id[x]["committed_model_changes"]
                for x in ("smo_antagonist", "dropout_xav939", "dropout_e2")
            },
        },
        {
            "id": "P9_runner_up_usable_opposite_separation",
            "cited_by": "§6 'Its separation lands on S_IGFBP1 ... with opposite predictions'",
            "value": sorted(
                f"{p['left']} vs {p['right']}:"
                + ",".join(sorted(h["node"] for h in p["usable_opposite"]))
                for p in hh["pairs"]
                if p["usable_opposite"]
            ),
        },
        {
            "id": "P10_third_arm_usable_separation",
            "cited_by": "§6 'separates a pair on a usable assay'",
            "value": sorted(
                f"{p['left']} vs {p['right']}:"
                + ",".join(sorted(h["node"] for h in p["usable"]))
                for p in _fork(report, "dropout_camp", "CAMP")["pairs"]
                if p["usable"]
            ),
        },
    ]


# --------------------------------------------------------------------------
# Cause attribution
# --------------------------------------------------------------------------


_OPERATORS = frozenset({"and", "or", "not"})


def _regulators(rule: str | None) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", rule or "")) - _OPERATORS


def _design_lineage(version: str, root: Path) -> dict[str, str]:
    """Every file the Stage-3 evaluation of `version` reads, with its SHA-256.

    Mirrors `identifiability.load_design`: the network, `baseline.cfg`, the
    condition cfg of every arm that carries a recorded observation, and the two
    configs that decide which arms those are. Also the model's own provenance
    and node dictionary (the structural facts read compartments from it), and
    `config/visualization.yaml`, which the structure loaders open although it
    carries visual metadata only. The guard checks this list against the files
    the computation actually opens, so it cannot silently fall short.
    """
    spec = resolve_model(version, root)
    paths = [
        spec.network_bnd,
        spec.baseline_cfg,
        spec.node_dictionary,
        spec.network_bnd.parent / "provenance.toml",
        root / "config/calibration.yaml",
        root / "config/visualization.yaml",
        root / OBSERVATION_MAP,
    ]
    for protocol in sorted(_observed_arms(root, spec.condition_dir)):
        cfg = spec.condition_dir / f"{protocol}.cfg"
        if cfg.exists():
            paths.append(cfg)
    return {str(p.relative_to(root)): _sha256(p) for p in sorted(set(paths))}


def _rule_diff(frozen: dict[str, str], adopted: dict[str, str]) -> list[dict]:
    """Rules that differ, with the dependency edges each change retires or adds.

    The edges are syntactic -- a regulator named in the rule. That is the level
    at which U5b's "two retired edges" exist; `absorbed_edges` in the structural
    facts is a different, semantic notion and does not show them.
    """
    return [
        {
            "node": n,
            FROZEN_VERSION: frozen.get(n),
            ADOPTED_VERSION: adopted.get(n),
            "dependencies_retired": sorted(
                _regulators(frozen.get(n)) - _regulators(adopted.get(n))
            ),
            "dependencies_added": sorted(
                _regulators(adopted.get(n)) - _regulators(frozen.get(n))
            ),
        }
        for n in sorted(set(frozen) | set(adopted))
        if frozen.get(n) != adopted.get(n)
    ]


def _full_state_delta(root: Path) -> dict:
    """Every node's exact marginal, every (experiment, fork, class), both models.

    Stage 3 compares maternal nodes only. This compares ALL nodes, so a change
    the rerank's summary could not show -- a difference in model state at an
    embryo-side or unassayed node -- is still counted, not assumed absent.
    """
    per_version = {}
    for version in (FROZEN_VERSION, ADOPTED_VERSION):
        facts = load_identifiability(version, root)
        base = parse_bnd_rules(resolve_model(version, root).network_bnd)
        arms = {arm.arm_id: dict(arm.inputs) for arm in facts.arms}
        values = {}
        for experiment in EXPERIMENTS:
            for fork in FORKS:
                inputs = _experiment_inputs(experiment, arms, fork)
                for klass in fork.classes:
                    rules, order = _class_rules(base, klass)
                    marg = _marginals(rules, order, facts.latent, inputs)
                    for node, value in marg.items():
                        values[(experiment.experiment_id, klass.class_id, node)] = value
        per_version[version] = (values, facts)
    a, fa = per_version[FROZEN_VERSION]
    b, fb = per_version[ADOPTED_VERSION]
    differing = sorted(
        f"{e}|{c}|{n}"
        for (e, c, n) in set(a) | set(b)
        if a.get((e, c, n)) is None
        or b.get((e, c, n)) is None
        or abs(a[(e, c, n)] - b[(e, c, n)]) > 1e-12
    )
    return {
        "evaluations_compared": len(set(a) | set(b)),
        "differing": differing,
        "latent_identical": list(fa.latent) == list(fb.latent),
        "arms_identical": [(x.arm_id, dict(x.inputs)) for x in fa.arms]
        == [(x.arm_id, dict(x.inputs)) for x in fb.arms],
    }


def _stage3_touched_nodes() -> dict[str, list[str]]:
    """Nodes any Stage-3 class rewrites and any Stage-3 arm sets or clamps."""
    overridden = sorted({n for f in FORKS for k in f.classes for n in k.overrides})
    added = sorted({n for f in FORKS for k in f.classes for n in k.added_free})
    set_ = sorted({n for e in EXPERIMENTS for n in (*e.input_overrides, *e.clamps)})
    return {"class_overrides": overridden, "class_added_free": added, "arm_sets": set_}


def _structure_delta(root: Path) -> dict:
    fs = load_structure(FROZEN_VERSION, root)
    ad = load_structure(ADOPTED_VERSION, root)

    def pack(s) -> dict:
        return {
            "nodes": len(s.node_ids),
            "free": len(s.free),
            "distinct_functions": s.distinct_function_count,
            "alias_classes": [list(c) for c in s.alias_classes if len(c) > 1],
            "absorbed_edges": [list(e) for e in s.absorbed_edges],
            "phenotype_inert": list(s.phenotype_inert),
        }

    a, b = pack(fs), pack(ad)
    return {
        FROZEN_VERSION: {k: a[k] for k in ("nodes", "free", "distinct_functions")},
        ADOPTED_VERSION: {k: b[k] for k in ("nodes", "free", "distinct_functions")},
        "alias_classes_identical": a["alias_classes"] == b["alias_classes"],
        "absorbed_edges_only_in_frozen": sorted(
            map(
                list,
                {tuple(e) for e in a["absorbed_edges"]}
                - {tuple(e) for e in b["absorbed_edges"]},
            )
        ),
        "absorbed_edges_only_in_adopted": sorted(
            map(
                list,
                {tuple(e) for e in b["absorbed_edges"]}
                - {tuple(e) for e in a["absorbed_edges"]},
            )
        ),
        "phenotype_inert_only_in_frozen": sorted(
            set(a["phenotype_inert"]) - set(b["phenotype_inert"])
        ),
        "phenotype_inert_only_in_adopted": sorted(
            set(b["phenotype_inert"]) - set(a["phenotype_inert"])
        ),
    }


def _d1(root: Path) -> dict:
    findings = json.loads((root / D1_SOURCE).read_text(encoding="utf-8"))
    ac01 = findings["alias_classes"]["AC01"]
    prov = ac01["decision_provenance"]
    return {
        "source": str(D1_SOURCE),
        "source_sha256": _sha256(root / D1_SOURCE),
        "AC01_class_verdict": ac01["class_verdict"],
        "depends_on_deviations": prov["depends_on_deviations"],
        "counterfactual_verdict_without_D1": prov["counterfactual_verdict_without_D1"],
        "registration_status": prov.get("registration_status"),
        "mandate": (
            "MANDATORY_CONDITIONAL_ON_D1"
            if ac01["class_verdict"] == "alias_challenged"
            and "D1" in prov["depends_on_deviations"]
            else "D1_CONDITION_NOT_AS_RECORDED"
        ),
        "reading": (
            "The rerank is owed because AC01 is alias_challenged, and that verdict "
            "rests on D1, a post-extraction interpretive call. Without D1, AC01 is "
            "unclassified_by_section_5_4 and the rerank is optional. U8 carries "
            "this condition and does not re-adjudicate D1."
        ),
    }


def _u6b_isolation(root: Path, adopted_rules: dict[str, str]) -> dict:
    with (root / U6B_CATALOG).open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    catalog_nodes = sorted({r["node_id"] for r in rows})
    touched = _stage3_touched_nodes()
    all_touched = set().union(*touched.values())
    return {
        "catalog": str(U6B_CATALOG),
        "catalog_statuses": sorted({r["status"] for r in rows}),
        "catalog_nodes": catalog_nodes,
        "catalog_nodes_absent_from_adopted_model": sorted(
            set(catalog_nodes) - set(adopted_rules)
        ),
        "stage3_nodes_touching_catalog": sorted(all_touched & set(catalog_nodes)),
    }


def _pair_rows(frozen: dict, adopted: dict) -> list[list[str]]:
    """Per (experiment, fork, pair): what separates it on each model."""

    def index(report: dict) -> dict:
        return {
            (r["experiment"], f["fork"], p["left"], p["right"]): p
            for r in report["results"]
            for f in r["forks"]
            for p in f["pairs"]
        }

    fa, fb = index(frozen), index(adopted)
    rows = []
    for key in fa:
        a, b = fa[key], fb[key]

        def nodes(p, k):
            return ";".join(h["node"] for h in p[k])

        va = {h["node"]: (h["left"], h["right"], h["readout_tier"]) for h in a["hits"]}
        vb = {h["node"]: (h["left"], h["right"], h["readout_tier"]) for h in b["hits"]}
        value_changes = sorted(n for n in set(va) | set(vb) if va.get(n) != vb.get(n))
        changed = (
            nodes(a, "hits") != nodes(b, "hits")
            or nodes(a, "usable") != nodes(b, "usable")
            or nodes(a, "usable_opposite") != nodes(b, "usable_opposite")
            or bool(value_changes)
        )
        rows.append(
            [
                *key,
                nodes(a, "hits"),
                nodes(b, "hits"),
                nodes(a, "usable"),
                nodes(b, "usable"),
                nodes(a, "usable_opposite"),
                nodes(b, "usable_opposite"),
                ";".join(value_changes),
                str(changed),
            ]
        )
    return rows


PAIR_COLUMNS = (
    "experiment",
    "fork",
    "left_class",
    "right_class",
    "v0.4_separating_nodes",
    "v0.5.1_separating_nodes",
    "v0.4_usable_assay_nodes",
    "v0.5.1_usable_assay_nodes",
    "v0.4_usable_assay_opposite_nodes",
    "v0.5.1_usable_assay_opposite_nodes",
    "nodes_whose_predicted_values_changed",
    "changed",
)


def compute(root: Path | None = None) -> dict:
    active = root or repo_root()
    frozen_text = (active / FROZEN_TSV).read_text(encoding="utf-8")
    frozen = evaluate(active, FROZEN_VERSION)
    if _tsv_text(frozen) != frozen_text:
        raise RuntimeError(
            f"{FROZEN_TSV} is no longer what the Stage-3 computation produces for "
            f"{FROZEN_VERSION}; the frozen reference cannot be trusted, so U8 "
            "refuses to compare against it"
        )
    adopted = evaluate(active, ADOPTED_VERSION)
    adopted_text = _tsv_text(adopted)
    tiers = _readout_tier(active)
    if frozen["readout_tiers"] != adopted["readout_tiers"]:
        raise RuntimeError("readout tiers differ between the two evaluations")

    prof_a = arm_profiles(_read_tsv(frozen_text), tiers)
    prof_b = arm_profiles(_read_tsv(adopted_text), tiers)
    per_arm = []
    for experiment in EXPERIMENTS:
        x = experiment.experiment_id
        changed = [k for k in PROFILE_FIELDS if prof_a[x][k] != prof_b[x][k]]
        per_arm.append(
            {
                "experiment": x,
                "protocol_status": experiment.protocol_status,
                "perturbations": experiment.perturbations,
                "frozen": prof_a[x],
                "adopted": prof_b[x],
                "changed_fields": changed,
            }
        )

    prem_a, prem_b = _premises(frozen), _premises(adopted)
    premises = [
        {
            "id": pa["id"],
            "cited_by": pa["cited_by"],
            FROZEN_VERSION: pa["value"],
            ADOPTED_VERSION: pb["value"],
            "unchanged": pa["value"] == pb["value"],
        }
        for pa, pb in zip(prem_a, prem_b, strict=True)
    ]
    all_hold = all(p["unchanged"] for p in premises)
    # The curated half of the ordering is the Experiment declarations; they are
    # one set of objects shared by both evaluations, so they cannot differ.
    ordering_status = CARRIED_OVER if all_hold else READJUDICATION_REQUIRED

    frozen_rules = parse_bnd_rules(resolve_model(FROZEN_VERSION, active).network_bnd)
    adopted_rules = parse_bnd_rules(resolve_model(ADOPTED_VERSION, active).network_bnd)
    rule_diff = _rule_diff(frozen_rules, adopted_rules)
    touched = _stage3_touched_nodes()
    state = _full_state_delta(active)
    structure = _structure_delta(active)
    pair_rows = _pair_rows(frozen, adopted)
    pairs_changed = [r for r in pair_rows if r[-1] == "True"]
    usable_pairs_changed = [r for r in pair_rows if r[6] != r[7] or r[8] != r[9]]

    activated, statuses = _scrna_can_alter_a_readout_tier(active)
    design_text = render(adopted, task=TASK)
    frozen_md = (active / FROZEN_MD).read_text(encoding="utf-8")
    # Bookkeeping: the only line of the rendered design allowed to differ is the
    # banner, which names the model and the regenerating task.
    md_diff = [
        (i, a, b)
        for i, (a, b) in enumerate(
            zip(render(frozen).splitlines(), design_text.splitlines(), strict=True)
        )
        if a != b
    ]
    if render(frozen) != frozen_md:
        raise RuntimeError(f"{FROZEN_MD} is not what Stage 3 renders for v0.4")

    cause = {
        "u5b_executable_rule_change": {
            "rule_diff": rule_diff,
            "stage3_marginals_changed": len(state["differing"]),
            "effect_on_ranking": "none" if not state["differing"] else "see differing",
        },
        "changed_model_structure": {
            "alias_classes_identical": structure["alias_classes_identical"],
            "absorbed_edges_only_in_frozen": structure["absorbed_edges_only_in_frozen"],
            "phenotype_inert_only_in_adopted": structure[
                "phenotype_inert_only_in_adopted"
            ],
            "enters_stage3": bool(
                set(structure["phenotype_inert_only_in_adopted"])
                & set().union(*touched.values())
            ),
        },
        "altered_alias_classes": not structure["alias_classes_identical"],
        "bookkeeping_only": [line for _, _, line in md_diff],
    }

    return {
        "frozen": frozen,
        "adopted": adopted,
        "adopted_tsv": adopted_text,
        "adopted_md": design_text,
        "per_arm": per_arm,
        "pair_rows": pair_rows,
        "summary": {
            "unit": "U8",
            "question": (
                "Does dropout_e2 remain the preferred prospective experiment after "
                f"moving from {FROZEN_VERSION} to {ADOPTED_VERSION}, under the same "
                "Stage-3 readout-tier computation?"
            ),
            "models": {
                v: {
                    "network_bnd": str(
                        resolve_model(v, active).network_bnd.relative_to(active)
                    ),
                    "network_bnd_sha256": _sha256(resolve_model(v, active).network_bnd),
                    "inputs_sha256": _design_lineage(v, active),
                }
                for v in (FROZEN_VERSION, ADOPTED_VERSION)
            },
            "d1_dependency": _d1(active),
            "scoring_contract": {
                "readout_tier_source": str(OBSERVATION_MAP),
                "readout_tier_source_sha256": _sha256(active / OBSERVATION_MAP),
                "readout_tiers_identical_across_models": True,
                "readout_tiers": {
                    n: t for n, (t, _) in sorted(frozen["readout_tiers"].items())
                },
                "candidate_score_yaml_read": False,
                "scrna_map": str(SCRNA_MAP),
                "scrna_map_sha256": _sha256(active / SCRNA_MAP),
                "scrna_activation_statuses": statuses,
                "scrna_can_promote_a_readout_tier": activated,
            },
            "frozen_artifacts": {
                str(p): _sha256(active / p)
                for p in (FROZEN_TSV, FROZEN_MD, FROZEN_TABLES, FROZEN_SELECTION)
            },
            "frozen_tsv_reproduced_by_fresh_v0_4_evaluation": True,
            "candidate_set": {
                "experiments": [e.experiment_id for e in EXPERIMENTS],
                "forks": {f.fork_id: [k.class_id for k in f.classes] for f in FORKS},
                "same_objects_for_both_models": True,
            },
            "stage3_touched_nodes": touched,
            "u6b_isolation": _u6b_isolation(active, adopted_rules),
            "three_reported_objects": {
                "frozen_v0_4_ranking": {
                    "ordering": [
                        {
                            "position": p,
                            "experiment": x,
                            "source": f"{FROZEN_SELECTION} {s}",
                        }
                        for p, x, s in FROZEN_ORDERING
                    ],
                    "candidate_set": sorted(
                        x for x, v in prof_a.items() if v["in_candidate_set"] == "True"
                    ),
                    "source": str(FROZEN_TSV),
                },
                "adopted_v0_5_1_ranking": {
                    "status": ordering_status,
                    "ordering": (
                        [
                            {"position": p, "experiment": x}
                            for p, x, _ in FROZEN_ORDERING
                        ]
                        if all_hold
                        else []
                    ),
                    "candidate_set": sorted(
                        x for x, v in prof_b.items() if v["in_candidate_set"] == "True"
                    ),
                    "source": str(OUT_DESIGN_TSV),
                },
                "per_arm_delta": {
                    "source": str(OUT_PER_ARM),
                    "arms_with_any_changed_field": [
                        a["experiment"] for a in per_arm if a["changed_fields"]
                    ],
                },
            },
            "dropout_e2_remains_first": all_hold,
            "premises": premises,
            "pair_separations_changed": len(pairs_changed),
            "usable_readout_separations_changed": len(usable_pairs_changed),
            "pairs_compared": len(pair_rows),
            "full_state_comparison": {
                "evaluations_compared": state["evaluations_compared"],
                "differing": state["differing"],
                "latent_identical": state["latent_identical"],
                "arms_identical": state["arms_identical"],
            },
            "structure": structure,
            "cause": cause,
            "not_done": [
                (
                    "design_alias 112-arm comparator not recomputed: plan §14 item 4 "
                    "calls reusing it a deliberate methodological change, not a "
                    "cross-check"
                ),
                "no MaBoSS run: Stage 3 is exact Boolean evaluation; U7 not needed",
            ],
        },
    }


def _per_arm_rows(per_arm: list[dict]) -> list[list[str]]:
    rows = []
    for arm in per_arm:
        rows.append(
            [
                arm["experiment"],
                arm["protocol_status"],
                str(arm["perturbations"]),
                *(arm["frozen"][k] for k in PROFILE_FIELDS),
                *(arm["adopted"][k] for k in PROFILE_FIELDS),
                ",".join(arm["changed_fields"]) or "none",
            ]
        )
    return rows


PER_ARM_COLUMNS = (
    "experiment",
    "protocol_status",
    "perturbations",
    *(f"v0.4_{k}" for k in PROFILE_FIELDS),
    *(f"v0.5.1_{k}" for k in PROFILE_FIELDS),
    "changed_fields",
)


def render_report(result: dict) -> str:
    s = result["summary"]
    three = s["three_reported_objects"]
    lines: list[str] = []
    a = lines.append
    a("# U8 — Stage-3 experiment rerank against adopted v0.5.1")
    a("")
    a(
        f"> **Generated file — do not edit.** Regenerate with `pixi run {TASK}`. "
        f"The Stage-3 computation of `src/dt_adoc/experiments/stage3_design.py`, "
        f"run unchanged against `{FROZEN_VERSION}` (the frozen reference, read "
        f"from `{FROZEN_TSV}`) and `{ADOPTED_VERSION}`. No MaBoSS run; no model "
        "or frozen artifact is modified."
    )
    a("")
    d1 = s["d1_dependency"]
    a("## Mandate: conditional on D1")
    a("")
    a(
        f"`AC01` is `{d1['AC01_class_verdict']}`, depending on "
        f"{', '.join(d1['depends_on_deviations'])}; without D1 it is "
        f"`{d1['counterfactual_verdict_without_D1']}` (`{d1['source']}`). "
        f"Status: `{d1['mandate']}`. {d1['reading']}"
    )
    a("")
    a("## Answer")
    a("")
    a(
        f"**`dropout_e2` remains first: {s['dropout_e2_remains_first']}.** "
        f"v0.5.1 ordering status: `{three['adopted_v0_5_1_ranking']['status']}`. "
        f"Premises unchanged: {sum(p['unchanged'] for p in s['premises'])} of "
        f"{len(s['premises'])}. Pair separations changed: "
        f"{s['pair_separations_changed']} of {s['pairs_compared']}; on a usable "
        f"readout: {s['usable_readout_separations_changed']}. Exact marginals "
        f"compared across every node, experiment and class: "
        f"{s['full_state_comparison']['evaluations_compared']}, differing: "
        f"{len(s['full_state_comparison']['differing'])}."
    )
    a("")
    a("## 1. Frozen v0.4 ranking (curated positions, quoted)")
    a("")
    a("| Position | Experiment | Source |")
    a("|---|---|---|")
    for o in three["frozen_v0_4_ranking"]["ordering"]:
        a(f"| {o['position']} | `{o['experiment']}` | {o['source']} |")
    a("")
    a(
        "Candidate set (separates a fork on a usable assay): "
        + ", ".join(f"`{x}`" for x in three["frozen_v0_4_ranking"]["candidate_set"])
        + "."
    )
    a("")
    a("## 2. v0.5.1 ranking")
    a("")
    adopted = three["adopted_v0_5_1_ranking"]
    if adopted["ordering"]:
        a(
            "Every computed premise of the frozen ordering is unchanged and the "
            "curated declarations are the same objects, so the ordering carries "
            "over without re-adjudication:"
        )
        a("")
        a("| Position | Experiment |")
        a("|---|---|")
        for o in adopted["ordering"]:
            a(f"| {o['position']} | `{o['experiment']}` |")
    else:
        a(
            "**`READJUDICATION_REQUIRED`.** At least one computed premise moved; "
            "no ordering is asserted here."
        )
    a("")
    a("Candidate set: " + ", ".join(f"`{x}`" for x in adopted["candidate_set"]) + ".")
    a("")
    a("## 3. Per-arm delta")
    a("")
    a(
        "| Experiment | Forks on a usable assay (v0.4 → v0.5.1) | Usable pairs | Changed fields |"
    )
    a("|---|---|---|---|")
    for arm in result["per_arm"]:
        f, b = arm["frozen"], arm["adopted"]
        a(
            f"| `{arm['experiment']}` | {f['forks_separated_usable_assay'] or '—'} → "
            f"{b['forks_separated_usable_assay'] or '—'} | "
            f"{len(_split(f['usable_assay_pairs']))} → {len(_split(b['usable_assay_pairs']))} | "
            f"{', '.join(arm['changed_fields']) or 'none'} |"
        )
    a("")
    a("## Premises of the frozen ordering, on both models")
    a("")
    a("| Premise | Cited by | Unchanged |")
    a("|---|---|---|")
    for p in s["premises"]:
        a(
            f"| `{p['id']}` | {p['cited_by']} | {'yes' if p['unchanged'] else '**NO**'} |"
        )
    a("")
    a("Values for both models are in `u8_rerank_summary.json`.")
    a("")
    a("## Cause attribution")
    a("")
    cause = s["cause"]
    for d in cause["u5b_executable_rule_change"]["rule_diff"]:
        a(
            f"* **U5b's executable rule change.** `{d['node']}`: "
            f"`{d[FROZEN_VERSION]}` → `{d[ADOPTED_VERSION]}`, retiring "
            + (
                ", ".join(f"`{x}→{d['node']}`" for x in d["dependencies_retired"])
                or "nothing"
            )
            + ". Stage-3 marginals it changes: "
            f"{cause['u5b_executable_rule_change']['stage3_marginals_changed']}."
        )
    st = cause["changed_model_structure"]
    a(
        "* **Changed model structure.** Edges absorbed only in v0.4: "
        + (
            ", ".join(f"`{x}→{y}`" for x, y in st["absorbed_edges_only_in_frozen"])
            or "none"
        )
        + "; phenotype-inert only in v0.5.1: "
        + (", ".join(f"`{x}`" for x in st["phenotype_inert_only_in_adopted"]) or "none")
        + f". Enters any Stage-3 class rewrite or arm: {st['enters_stage3']}."
    )
    a(f"* **Altered alias classes:** {cause['altered_alias_classes']}.")
    a(
        "* **Bookkeeping only:** the rendered design differs from v0.4's in "
        f"{len(cause['bookkeeping_only'])} line(s), the generated-file banner."
    )
    a("")
    a("## Scoring contract")
    a("")
    sc = s["scoring_contract"]
    a(
        f"Readout tiers from `{sc['readout_tier_source']}` only (sha256 "
        f"`{sc['readout_tier_source_sha256'][:12]}`), identical for both models; "
        f"`config/candidate_score.yaml` read: {sc['candidate_score_yaml_read']}. "
        f"scRNA activation statuses: {', '.join(f'`{x}`' for x in sc['scrna_activation_statuses'])}; "
        f"can promote a tier: {sc['scrna_can_promote_a_readout_tier']}."
    )
    a("")
    u = s["u6b_isolation"]
    a(
        f"U6b catalogue (`{u['catalog']}`) statuses "
        f"{', '.join(f'`{x}`' for x in u['catalog_statuses'])}; Stage-3 nodes "
        f"touching it: {', '.join(u['stage3_nodes_touching_catalog']) or 'none'}."
    )
    a("")
    return "\n".join(lines) + "\n"


def _tsv(columns: tuple[str, ...], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter="\t", lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return buf.getvalue()


def render_outputs(result: dict) -> dict[Path, str]:
    """Every artifact's text, in memory, so a test can compare without writing."""
    return {
        OUT_DESIGN_MD: result["adopted_md"],
        OUT_DESIGN_TSV: result["adopted_tsv"],
        OUT_PER_ARM: _tsv(PER_ARM_COLUMNS, _per_arm_rows(result["per_arm"])),
        OUT_PAIRS: _tsv(PAIR_COLUMNS, result["pair_rows"]),
        OUT_SUMMARY: json.dumps(result["summary"], indent=2, sort_keys=True) + "\n",
        OUT_REPORT: render_report(result),
    }


def build(root: Path | None = None) -> tuple[Path, ...]:
    active = root or repo_root()
    outputs = render_outputs(compute(active))
    assert tuple(outputs) == OUTPUTS
    (active / OUT_DIR).mkdir(parents=True, exist_ok=True)
    for relative, text in outputs.items():
        (active / relative).write_text(text, encoding="utf-8")
    return tuple(active / p for p in OUTPUTS)


if __name__ == "__main__":  # pragma: no cover
    for written in build():
        print(f"wrote {written}")
