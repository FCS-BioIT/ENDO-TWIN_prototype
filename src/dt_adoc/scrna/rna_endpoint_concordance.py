"""RNA <-> MaBoSS endpoint concordance for the RNA-observable model nodes.

The ADOC scRNA-seq is an END-OF-TREATMENT measurement, so it is used here as a
READOUT of the model, never as an initial condition. For each node the committed
observation map records as RNA-observable, this module sets the adopted model's
predicted CNT -> HT endpoint change beside the observed within-donor RNA
movement and classifies the pair. It is evaluation, not calibration: nothing
here feeds back into `network.bnd`, and a discordance is a result.

EVERYTHING IS READ FROM COMMITTED ARTIFACTS. No expression object is loaded,
no MaBoSS run is made, and no threshold, gene list or movement rule is new:

- per-unit RNA quantities and their within-donor bootstrap intervals come from
  `docs/scrna/node_support_evidence.tsv`, the pre-registered node-support audit,
  read through `observation_corrections.live_evidence_rows`: rows a post-closure
  map correction supersedes (`E_PC6`'s PCSK6) are dropped and the correction's
  post-hoc rows (PCSK5) take their place;
- the per-donor movement call is `node_support.member_verdict`, the audit's
  frozen rule (non-overlapping 95% intervals AND >= two-fold), unchanged; for a
  corrected node the same rule runs over the corrected program
  (`observation_corrections.live_member_verdict`);
- the endpoint prediction is the fixed point of the ADOPTED
  `adoc-literature-superset-v0.5.1` rules under the HT inputs and each candidate
  CNT encoding, cross-checked against the committed v0.4.0 MaBoSS run, which is
  function-identical on every RNA-observable node;
- the observation class is the committed map's, with the declared post-closure
  corrections applied (`docs/scrna_corrections/scrna_observation_map_corrected.tsv`).

The RNA effects stay RNA quantities (log2 fold of a pseudobulk share). They are
never presented as MaBoSS probabilities, and the MaBoSS values are never
presented as expression.

Three guards keep a verdict inside what the assay can say:

- rows whose feature observes abundance and not the model state
  (`proxy_abundance_not_activity`), and rows whose committed resolution text says
  the modelled state is not resolved (`STATE_NOT_RESOLVED`), are REPORTED, NOT
  SCORED;
- agreement on a CONSTRUCTION analyte is `circular_agreement`, never
  `concordant`;
- "no material response" requires every voting gene's fold interval to lie
  inside the two-fold margin in 3/3 donors; a non-move that is not that precise
  is `indeterminate` and cannot carry a discordance.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from dt_adoc.scrna import node_support as N
from dt_adoc.scrna import node_support_contract as C
from dt_adoc.scrna import node_support_expectations as X
from dt_adoc.scrna import observation_corrections as O

REPO = Path(__file__).resolve().parents[3]
MODEL_VERSION = "adoc-literature-superset-v0.5.1"
BND = REPO / f"models/superset/{MODEL_VERSION}/network.bnd"
EVIDENCE = REPO / "docs/scrna/node_support_evidence.tsv"
FINDINGS = REPO / "docs/scrna/node_support_findings.json"
RAW_SENSITIVITY = REPO / "docs/scrna/node_support_raw_sensitivity.json"
MABOSS_RUN = REPO / "docs/concordance/run_settings.json"
OUT_DIR = REPO / "docs/rna_endpoint_concordance"
TABLE = OUT_DIR / "concordance.tsv"
FIGURE = OUT_DIR / "concordance.png"

#: The maternal arms of the committed MaBoSS run that bracket the scRNA
#: comparison. The scRNA has no embryo, so no adhesion-challenge arm applies.
MABOSS_ARMS = {
    "cnt_unstimulated": "basal_maternal",
    "cnt_e2_only": "e2_primed_maternal",
    "ht": "hormone_treated_maternal",
}

#: Direct transcripts re-derived on raw UMIs by the committed sensitivity.
RAW_VERIFIED_GENES = {"E_PAEP": "PAEP", "E_HBEGF": "HBEGF"}

#: Observation-class inconsistencies found in the committed artifacts. Flagged,
#: not fixed: the map is the authority for this unit.
CLASSIFICATION_FLAGS = {
    "S_HAND2": (
        "map records direct_transcript; the node-support pre-registration's "
        "Appendix A prints it as a regulon/activity proxy. The map is used."
    ),
    "S_NR2F2": (
        "map records regulon_activity, but its only feature is NR2F2 itself and "
        "its own resolution text says regulatory activity is NOT resolved; in "
        "practice a single transcript."
    ),
}

NOT_SCORED = "proxy_abundance_not_activity"

#: Rows the map does not class as abundance proxies but whose own committed
#: `measurement_resolution` says the MODELLED state is not resolved by the
#: measurement. They are reported, not scored, on the same ground as the
#: abundance proxies. Each entry quotes the map; `verify_not_resolved_grounds`
#: fails if the quoted text leaves it.
STATE_NOT_RESOLVED = {
    "E_MUC1_SLEX": (
        "it does NOT distinguish a cell that carries surface sLeX from one that "
        "merely could make it"
    ),
    "S_FGF_MITOGENIC": "receptor engagement is not resolved",
    "S_NR2F2": "regulatory activity is NOT resolved by this measurement",
}

#: The map's `evidence_role` for analytes that BUILT the model state. Agreement
#: on such a row is circular and is never counted as concordance (the map's
#: claim ceilings say so, e.g. E_PAEP "can never be cited as concordance for
#: it"). Disagreement remains informative: construction cannot manufacture it.
CONSTRUCTION = "construction"

#: The equivalence margin for "materially flat": the audit's pre-registered
#: materiality convention (two-fold), applied to the whole interval of the fold.
FLAT_MARGIN_LOG2 = C.LOG2_FOLD_MIN
DONORS = C.DONORS


class ConcordanceError(RuntimeError):
    """The concordance table cannot be derived from the committed inputs."""


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------


def load_stats(path: Path = EVIDENCE) -> dict[str, N.UnitStats]:
    """Rebuild the audit's per-unit statistics from one evidence table."""
    with path.open(newline="", encoding="utf-8") as handle:
        return stats_from_rows(csv.DictReader(handle, delimiter="\t"))


def live_stats() -> dict[str, N.UnitStats]:
    """Per-unit statistics over the live evidence: frozen rows, minus superseded
    ones, plus the declared corrections' rows."""
    return stats_from_rows(O.live_evidence_rows(REPO))


def stats_from_rows(rows) -> dict[str, N.UnitStats]:
    stats: dict[str, N.UnitStats] = {}
    for row in rows:
        if row["compartment"] not in C.PRIMARY_COMPARTMENTS:
            continue
        unit = N.Unit(row["donor"], row["condition"], row["compartment"])
        if unit.unit_id != row["unit_id"]:
            raise ConcordanceError(f"unit id mismatch: {row['unit_id']}")
        s = stats.setdefault(
            unit.unit_id,
            N.UnitStats(
                unit=unit,
                n_cells=int(row["n_cells"]),
                exposure=float(row["exposure"]),
                f={},
                d={},
                f_ci={},
                d_ci={},
                min_nonzero={},
            ),
        )
        key = f"{row['level']}:{row['name']}"
        s.f[key] = float(row["f"])
        s.d[key] = float(row["d"])
        s.f_ci[key] = (float(row["f_ci_lo"]), float(row["f_ci_hi"]))
        s.d_ci[key] = (float(row["d_ci_lo"]), float(row["d_ci_hi"]))
    if len(stats) != len(DONORS) * len(C.CONDITIONS) * len(C.PRIMARY_COMPARTMENTS):
        raise ConcordanceError(f"expected 12 primary units, found {len(stats)}")
    return stats


def predictions(bnd: Path = BND) -> dict[str, dict[str, bool]]:
    """Endpoint states of the adopted model under HT and each CNT encoding."""
    rules = X.load_rules(bnd)
    moved = X.relay_invariance(rules)
    assessable = {r["model_node"] for r in X.rna_assessable_rows()}
    if moved.keys() & assessable:
        raise ConcordanceError(
            f"relay setting changes an RNA-observable node: {sorted(moved)}"
        )
    return X.states(rules)


def maboss_values(path: Path = MABOSS_RUN) -> dict[tuple[str, str], dict]:
    """Per-node P(ON), seed-mean, from the committed maternal MaBoSS arms."""
    run = json.loads(path.read_text(encoding="utf-8"))
    return {
        (arm["arm_id"], arm["horizon_class"]): arm["node_by_seed"]
        for arm in run["arms"]
        if arm["arm_id"] in MABOSS_ARMS.values()
    }


def raw_verified() -> dict[str, dict[str, str]]:
    """Per-donor raw-UMI calls for the genes the committed sensitivity read."""
    raw = json.loads(RAW_SENSITIVITY.read_text(encoding="utf-8"))
    return {
        gene: raw["comparison"][gene]["per_donor"]
        for gene in RAW_VERIFIED_GENES.values()
    }


# --------------------------------------------------------------------------
# Derivation
# --------------------------------------------------------------------------


def log2_fold(gene: str, donor: str, compartment: str, stats) -> tuple[float, bool]:
    """The audit's pseudocounted log2 fold and interval separation, one gene."""
    key = f"gene:{gene}"
    cnt = stats[N.Unit(donor, "CNT", compartment).unit_id]
    ht = stats[N.Unit(donor, "HT", compartment).unit_id]
    lo_c, hi_c = cnt.f_ci[key]
    lo_h, hi_h = ht.f_ci[key]
    pseudo_c = (cnt.f[key] * cnt.exposure + 1) / (cnt.exposure + 1)
    pseudo_h = (ht.f[key] * ht.exposure + 1) / (ht.exposure + 1)
    return math.log2(pseudo_h / pseudo_c), hi_c < lo_h or hi_h < lo_c


def fold_bounds(gene: str, donor: str, compartment: str, stats) -> tuple[float, float]:
    """Smallest and largest log2 fold the two within-donor intervals admit."""
    key = f"gene:{gene}"
    cnt = stats[N.Unit(donor, "CNT", compartment).unit_id]
    ht = stats[N.Unit(donor, "HT", compartment).unit_id]

    def pseudo(value: float, exposure: float) -> float:
        return (value * exposure + 1) / (exposure + 1)

    lo_c, hi_c = (pseudo(v, cnt.exposure) for v in cnt.f_ci[key])
    lo_h, hi_h = (pseudo(v, ht.exposure) for v in ht.f_ci[key])
    return math.log2(lo_h / hi_c), math.log2(hi_h / lo_c)


def donor_state(
    call: str, program: list[str], donor: str, compartment: str, stats
) -> str:
    """Refine the audit's call: a non-move is FLAT only if shown to be.

    `no_material_move` covers both a precisely measured sub-two-fold change and
    an imprecise one whose intervals overlap. Only the first is evidence of no
    response: every voting gene's fold interval must lie inside the two-fold
    margin. Anything else is `indeterminate`, which is not evidence of absence.
    """
    if call != "no_material_move":
        return call if call in ("moves_up", "moves_down") else ""
    for gene in program:
        key = f"gene:{gene}"
        # Undetected in either arm: the pseudocount pins the fold near zero,
        # which is a floor, not a measured non-response.
        if any(
            stats[N.Unit(donor, arm, compartment).unit_id].f[key] == 0
            for arm in C.CONDITIONS
        ):
            return "indeterminate"
        lo, hi = fold_bounds(gene, donor, compartment, stats)
        if not (-FLAT_MARGIN_LOG2 < lo and hi < FLAT_MARGIN_LOG2):
            return "indeterminate"
    return "flat_within_two_fold"


def verify_not_resolved_grounds(rows: dict[str, dict[str, str]]) -> None:
    for node, quote in STATE_NOT_RESOLVED.items():
        if quote not in rows[node]["measurement_resolution"]:
            raise ConcordanceError(f"{node}: map no longer says {quote!r}")


def _arrow(before: bool, after: bool) -> str:
    return X.direction(before, after)


def _mean(values: list[float]) -> str:
    return f"{sum(values) / len(values):.6f}"


def _verdict(states: dict[str, str], wanted: str, construction: bool = False) -> str:
    """The conservative 3/3 rule over refined per-donor states."""
    against = "moves_down" if wanted == "moves_up" else "moves_up"
    values = list(states.values())
    if any(v == "" for v in values):
        return "uninformative"
    if all(v == wanted for v in values):
        return "circular_agreement" if construction else "concordant"
    if all(v == against for v in values):
        return "discordant_opposite"
    if all(v == "flat_within_two_fold" for v in values):
        return "no_response_within_two_fold"
    return "mixed_or_inconclusive"


AGREEMENT = ("concordant", "circular_agreement")

SCORED_VERDICTS = (
    "concordant",
    "circular_agreement",
    "discordant_opposite",
    "no_response_within_two_fold",
    "mixed_or_inconclusive",
)


def class_verdict(verdicts: list[str]) -> str:
    """An alias class's reading over its SCORED members only."""
    scored = [v for v in verdicts if v in SCORED_VERDICTS]
    if not scored:
        return "no_scored_members"
    if len(scored) < 2:
        return "uninformative"
    # A member moving as predicted while a sibling demonstrably does not is a
    # divergence BETWEEN members, so circular agreement still counts on that
    # side: construction cannot make one member move and its sibling not.
    # Only movement AGAINST the prediction is a demonstrated discordance. A
    # member shown flat within two-fold is not called discordant: with three
    # donors and no powered equivalence criterion, "no response" is recorded as
    # what was measured, and a class reading built on it says so in its name.
    agrees = any(v in AGREEMENT for v in scored)
    opposite = any(v == "discordant_opposite" for v in scored)
    flat = any(v == "no_response_within_two_fold" for v in scored)
    if agrees and opposite:
        return "alias_challenged"
    if agrees and flat:
        return "members_diverge_one_within_two_fold"
    if all(v == "discordant_opposite" for v in scored):
        return "jointly_discordant_rule_challenged"
    if all(v == "no_response_within_two_fold" for v in scored):
        return "jointly_no_response_within_two_fold"
    if all(v in AGREEMENT for v in scored):
        return "consistent_not_confirmed"
    return "mixed_or_inconclusive"


def build() -> list[dict[str, str]]:
    stats = live_stats()
    states = predictions()
    maboss = maboss_values()
    raw = raw_verified()
    committed = json.loads(FINDINGS.read_text(encoding="utf-8"))["alias_classes"]
    rows_by_node = {
        r["model_node"]: r for r in X.rna_assessable_rows(O.corrected_map_path(REPO))
    }
    verify_not_resolved_grounds(rows_by_node)

    records: list[dict[str, str]] = []
    for node, row in rows_by_node.items():
        obs = row["measurement_observability"]
        compartment = C.COMPARTMENT_OF_NODE[row["compartment"]]
        ht = states["HT"][node]
        pred_unstim = _arrow(states["unstimulated"][node], ht)
        pred_e2 = _arrow(states["e2_primed_only"][node], ht)
        member = O.live_member_verdict(node, compartment, stats, root=REPO)
        per_donor = member.get("per_donor", {})
        program = member.get("program", [])

        construction = row["evidence_role"] == CONSTRUCTION
        states_by_donor = {
            d: donor_state(per_donor[d], program, d, compartment, stats)
            for d in per_donor
        }
        folds = []
        below_two_fold = False
        if per_donor:
            for gene in program:
                parts = []
                for donor in DONORS:
                    value, separated = log2_fold(gene, donor, compartment, stats)
                    parts.append(f"{donor}{value:+.2f}{'*' if separated else ''}")
                folds.append(f"{gene}[{' '.join(parts)}]")

        if node == "E_KLF12_HIGH":
            # Continuous values only: no per-donor movement call is recorded,
            # so nothing in this row reads as a KLF12 state.
            per_donor = {}
            states_by_donor = {}
            verdict = "descriptive_only"
            reason = (
                "hand-set free variable, predicted unchanged by construction; "
                "RNA shown as a continuous quantity only. No binary state or "
                "threshold is derived (Phase 2B closed as NO_SUITABLE_REFERENCE)."
            )
        elif obs == NOT_SCORED:
            verdict = "reported_not_scored"
            reason = (
                "the RNA feature measures transcript abundance, not the "
                "modelled state; it can neither confirm nor refute it."
            )
        elif node in STATE_NOT_RESOLVED:
            verdict = "reported_not_scored"
            reason = (
                "the map records that this measurement does not resolve the "
                f"modelled state: '{STATE_NOT_RESOLVED[node]}'."
            )
        elif pred_unstim != pred_e2:
            verdict = "uninformative"
            reason = (
                f"prediction depends on the unresolved CNT arm: {pred_unstim} if "
                f"untreated, {pred_e2} if E2-only."
            )
        elif pred_e2 == "no change":
            verdict = "uninformative"
            reason = "model predicts no CNT -> HT change."
        elif not per_donor:
            verdict = "uninformative"
            reason = f"no per-donor call: {member.get('reason', 'unavailable')}."
        else:
            wanted = "moves_up" if pred_e2 == "OFF -> ON" else "moves_down"
            verdict = _verdict(states_by_donor, wanted, construction)
            reason = {
                "concordant": "predicted direction, material and separated, 3/3 donors",
                "circular_agreement": (
                    "predicted direction in 3/3 donors, but this is a CONSTRUCTION "
                    "analyte: the measurement built the state, so agreement is "
                    "circular and is not counted as concordance"
                ),
                "discordant_opposite": "material movement against the prediction, 3/3 donors",
                "no_response_within_two_fold": (
                    "every voting gene's fold interval lies within two-fold in "
                    "3/3 donors where a switch is predicted; recorded as a "
                    "measurement, NOT as a demonstrated discordance (no powered "
                    "equivalence criterion exists for three donors)"
                ),
                "mixed_or_inconclusive": (
                    "donors disagree, or a non-move is not precise enough to "
                    "exclude a two-fold change (indeterminate)"
                ),
                "uninformative": "a donor could not be called",
            }[verdict]
            if construction and verdict in (
                "discordant_opposite",
                "no_response_within_two_fold",
            ):
                reason += "; construction analyte, but disagreement is not circular"
            if len(program) == 1 and verdict not in AGREEMENT:
                values = [log2_fold(program[0], d, compartment, stats) for d in DONORS]
                below_two_fold = all(
                    sep and (v > 0) == (wanted == "moves_up") for v, sep in values
                )

        gene = RAW_VERIFIED_GENES.get(node)
        if gene and raw[gene] == per_donor:
            layer = "raw_umi_verified"
        elif gene:
            raise ConcordanceError(f"{node}: raw-UMI calls disagree with corrected")
        else:
            layer = "layer_caveated"

        klass = row["v04_function_class"].strip()
        committed_class = (
            committed[klass]["class_verdict"]
            if klass in committed
            else ("not_alias_tested" if klass else "")
        )
        ht_decl = maboss[(MABOSS_ARMS["ht"], "declared")][node]
        records.append(
            {
                "model_node": node,
                "compartment": compartment,
                "observation_type": obs,
                "rna_features_voting": ";".join(program),
                "rna_features_committed": row["measurement_features"],
                "predicted_cnt_to_ht": pred_e2 if pred_unstim == pred_e2 else "",
                "predicted_if_cnt_untreated": pred_unstim,
                "predicted_if_cnt_e2_only": pred_e2,
                "maboss_v040_converged_p_on_cnt_untreated": _mean(
                    maboss[(MABOSS_ARMS["cnt_unstimulated"], "converged")][node]
                ),
                "maboss_v040_converged_p_on_cnt_e2_only": _mean(
                    maboss[(MABOSS_ARMS["cnt_e2_only"], "converged")][node]
                ),
                "maboss_v040_converged_p_on_ht": _mean(
                    maboss[(MABOSS_ARMS["ht"], "converged")][node]
                ),
                "maboss_v040_declared_p_on_ht_descriptive": _mean(ht_decl),
                "biological_unit": "donor; within-donor CNT vs HT, one library per arm",
                "n_donors": str(len(DONORS)),
                **{f"call_{d}": per_donor.get(d, "") for d in DONORS},
                **{f"rna_state_{d}": states_by_donor.get(d, "") for d in DONORS},
                "rna_log2_fold_by_gene": " ".join(folds),
                "verdict": verdict,
                "reason": reason,
                "consistent_direction_below_two_fold": str(below_two_fold).lower(),
                "layer_status": layer,
                "observability_limitation": row["measurement_resolution"],
                "claim_ceiling": row["claim_ceiling"],
                "evidence_role": row["evidence_role"],
                "phenotype_inert_v04": row["phenotype_inert"],
                "alias_class": klass,
                "alias_class_members": row["v04_class_members"] if klass else "",
                "alias_class_verdict": "",
                "node_support_audit_class_verdict": committed_class,
                "classification_flag": CLASSIFICATION_FLAGS.get(node, ""),
            }
        )

    by_class: dict[str, list[str]] = {}
    for r in records:
        if r["alias_class"]:
            by_class.setdefault(r["alias_class"], []).append(r["verdict"])
    for r in records:
        if r["alias_class"]:
            r["alias_class_verdict"] = class_verdict(by_class[r["alias_class"]])
    return records


def write_table(records: list[dict[str, str]], path: Path = TABLE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, list(records[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(records)


def read_table(path: Path = TABLE) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


# --------------------------------------------------------------------------
# Figure -- drawn from concordance.tsv and nothing else
# --------------------------------------------------------------------------

CALL_STYLE = {
    "moves_up": ("#256abf", "up", "#ffffff"),
    "moves_down": ("#c0392b", "down", "#ffffff"),
    "flat_within_two_fold": ("#d6d5d0", "flat <2x", "#0b0b0b"),
    "indeterminate": ("#f0efec", "indet.", "#52514e"),
    "": ("#fcfcfb", "n/a", "#8a8984"),
}


VERDICT_LABEL = {
    "no_response_within_two_fold": "no response within 2x (not discordance)",
    "discordant_opposite": "discordant (opposite)",
    "mixed_or_inconclusive": "mixed / inconclusive",
    "circular_agreement": "circular agreement (construction)",
    "reported_not_scored": "reported, not scored",
    "descriptive_only": "descriptive only",
}


def render(path: Path = TABLE, out: Path = FIGURE) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    matplotlib.rcParams["svg.hashsalt"] = "dt-adoc"
    rows = read_table(path)
    rows.sort(
        key=lambda r: (r["alias_class"] or "~", r["compartment"], r["model_node"])
    )
    n = len(rows)
    fig, ax = plt.subplots(figsize=(11.5, 0.34 * n + 1.6), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    columns = [f"rna_state_{d}" for d in DONORS]
    for i, r in enumerate(rows):
        y = n - 1 - i
        for j, col in enumerate(columns):
            fill, label, ink = CALL_STYLE[r[col]]
            hatch = None
            if r["verdict"] == "reported_not_scored":
                # Not scored: the RNA call is shown, but recessive, so it does
                # not read as evidence about the model state.
                fill, ink, hatch = "#fcfcfb", "#52514e", "////"
            if r["verdict"] == "descriptive_only":
                label = "cont. only"
            ax.add_patch(
                Rectangle(
                    (j + 0.04, y + 0.06),
                    0.92,
                    0.88,
                    facecolor=fill,
                    edgecolor="#d6d5d0" if hatch else "#fcfcfb",
                    hatch=hatch,
                    linewidth=0.8 if hatch else 2,
                )
            )
            ax.text(
                j + 0.5,
                y + 0.5,
                label,
                ha="center",
                va="center",
                fontsize=7.5,
                color=ink,
            )
        ax.text(
            3.15,
            y + 0.5,
            r["predicted_cnt_to_ht"] or "encoding-dependent",
            va="center",
            fontsize=7.5,
            color="#52514e",
        )
        ax.text(
            4.9,
            y + 0.5,
            VERDICT_LABEL.get(r["verdict"], r["verdict"]),
            va="center",
            fontsize=7.5,
            color="#0b0b0b",
            fontweight="bold"
            if r["verdict"]
            in ("concordant", "circular_agreement", "discordant_opposite")
            and r["verdict"] in SCORED_VERDICTS
            else "normal",
        )
        tag = f"{r['model_node']}  [{r['observation_type']}]"
        ax.text(
            -0.1, y + 0.5, tag, ha="right", va="center", fontsize=7.5, color="#0b0b0b"
        )
        if i == 0 or rows[i - 1]["alias_class"] != r["alias_class"]:
            ax.axhline(y + 1, color="#52514e", linewidth=0.6)
            ax.text(
                7.75,
                y + 0.68,
                r["alias_class"] or "no alias class",
                va="center",
                fontsize=7.5,
                color="#52514e",
                fontweight="bold",
            )
            if r["alias_class_verdict"]:
                ax.text(
                    7.75,
                    y + 0.25,
                    r["alias_class_verdict"].replace("_", " "),
                    va="center",
                    fontsize=6.5,
                    color="#52514e",
                )
    for j, d in enumerate(DONORS):
        ax.text(j + 0.5, n + 0.3, d, ha="center", fontsize=8, color="#52514e")
    ax.text(3.15, n + 0.3, "predicted CNT->HT", fontsize=8, color="#52514e")
    ax.text(4.9, n + 0.3, "verdict", fontsize=8, color="#52514e")
    ax.text(7.75, n + 0.3, "alias class", fontsize=8, color="#52514e")
    ax.set_xlim(-0.1, 9.8)
    ax.set_ylim(-0.2, n + 0.8)
    ax.axis("off")
    ax.legend(
        handles=[
            Patch(facecolor=CALL_STYLE[k][0], edgecolor="#52514e", label=lab)
            for k, lab in [
                ("moves_up", "moves up (>=2-fold, intervals separated)"),
                ("moves_down", "moves down"),
                ("flat_within_two_fold", "flat: fold interval within 2x"),
                ("indeterminate", "not moved, not shown flat"),
            ]
        ]
        + [
            Patch(
                facecolor="#fcfcfb",
                hatch="////",
                edgecolor="#8a8984",
                label="reported, not scored (assay does not resolve the state)",
            )
        ],
        loc="upper left",
        bbox_to_anchor=(-0.45, -0.005),
        ncol=4,
        frameon=False,
        fontsize=7.5,
    )
    ax.set_title(
        f"ADOC endpoint scRNA vs {MODEL_VERSION}: predicted CNT->HT change\n"
        "per-donor RNA state (node-support movement rule; flat = fold interval within 2x); "
        "drawn from concordance.tsv only",
        fontsize=9,
        loc="left",
        color="#0b0b0b",
    )
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=fig.get_facecolor(), metadata={"Software": None})
    plt.close(fig)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--render-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.render_only:
        write_table(build())
    render()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
