"""Generate the calibration/discrimination candidate report.

Architecture, deliberately: **structured sources -> deterministic generator ->
Markdown**. The Markdown is an output and is never hand-edited; anything a
reader might want to correct belongs in a source file.

Exactly one new curated source exists,
``context/experiments/calibration_candidates.tsv``, and it carries only fields
that are expert judgement: what the experiment is, what it is for, which
readouts matter, which references support the expectation, feasibility, and the
curator's own value calls. Everything structural is **derived** here from files
that already exist, so it cannot drift away from the model:

* whether a candidate has a model image, and which named nodes do not exist
  (``models/.../network.bnd``);
* whether an interrogated input is **zero-degree** -- declared but read by no
  rule, so perturbing it cannot change anything;
* the rule-induced alias class of each interrogated node, and its coupling
  adjudication (``config/coupling_adjudication.tsv``);
* whether the candidate is already an implemented perturbation
  (``config/perturbations.yaml``);
* which Gate-3 rule variants it separates
  (``context/literature/reviews/gate3_candidate_variants_*.tsv``);
* whether it reaches maternal nodes, terminal adhesion only, or neither,
  computed by propagation over the committed network;
* whether its proximal readouts exist in the observation layer
  (``config/observation_model_map.tsv``, ``context/phase1-readouts.tsv``);
* the species and evidence level behind each cited reference
  (``context/literature/references.tsv``), so "human" and "transferred" are
  never asserted by hand.

Information value is reported on **separate axes** and is never collapsed into
one score. A candidate can be highly informative for the terminal interface
abstraction and close to useless for the maternal core -- anti-SPP1 is exactly
that, and a single number would hide it.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _topological_order,
    load_identifiability,
    parse_bnd_rules,
    repo_root,
    resolve_model,
)

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
CURATED = Path("context/experiments/calibration_candidates.tsv")
OUT_MD = Path("docs/experiments/calibration_candidates.md")
OUT_TSV = Path("docs/experiments/calibration_candidates_derived.tsv")

#: Nodes that are the maternal model proper, as opposed to the terminal
#: interface. Matches the compartment split used in
#: ``docs/gate3_scope_adjudication.md`` section 2.
MATERNAL_PREFIXES = ("E_", "S_")
TERMINAL_NODES = ("OUT_STABLE_ADHESION", "OUT_MATERNAL_ADHESION_COMPETENCE")


def _load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def _split(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _normalise(name: str) -> str:
    """Compare analyte names without punctuation or case.

    The observation map writes ``IGFBP-1`` and curators write ``IGFBP1``; a
    literal substring test silently reports the readout as unavailable, which
    is the wrong answer in the direction that matters.
    """
    return re.sub(r"[^a-z0-9]", "", name.lower())


@dataclass
class Sources:
    root: Path
    rules: dict[str, str]
    facts: Any
    coupling: dict[str, dict[str, str]]
    perturbations: list[dict[str, Any]]
    variants: list[dict[str, str]]
    references: dict[str, dict[str, str]]
    observed_proteins: set[str]
    planned_readouts: set[str]
    alias_class: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path | None = None) -> Sources:
        active = root or repo_root()
        facts = load_identifiability(MODEL_VERSION, active)
        spec = resolve_model(MODEL_VERSION, active)
        rules = parse_bnd_rules(spec.network_bnd)

        coupling = {
            row["node_id"]: row
            for row in _load_tsv(active / "config/coupling_adjudication.tsv")
        }
        perturbations = yaml.safe_load(
            (active / "config/perturbations.yaml").read_text(encoding="utf-8")
        )["perturbations"]
        variant_files = sorted(
            (active / "context/literature/reviews").glob(
                "gate3_candidate_variants_*.tsv"
            )
        )
        variants = _load_tsv(variant_files[-1]) if variant_files else []
        references = {
            row["ref_id"]: row
            for row in _load_tsv(active / "context/literature/references.tsv")
        }
        observed = {
            row["protein"].strip()
            for row in _load_tsv(active / "config/observation_model_map.tsv")
            if row.get("protein", "").strip()
        }
        planned = {
            row["readout"].strip()
            for row in _load_tsv(active / "context/phase1-readouts.tsv")
            if row.get("readout", "").strip()
        }

        alias: dict[str, tuple[str, ...]] = {}
        for members in facts.global_classes:
            for node in members:
                alias[node] = tuple(members)

        return cls(
            root=active,
            rules=rules,
            facts=facts,
            coupling=coupling,
            perturbations=perturbations,
            variants=variants,
            references=references,
            observed_proteins=observed,
            planned_readouts=planned,
            alias_class=alias,
        )

    def is_zero_degree(self, node: str) -> bool:
        """Declared as a node but read by no other rule.

        The reason an XAV939 or hCG perturbation currently has no model image:
        the input exists, and nothing downstream consults it.
        """
        if node not in self.rules:
            return False
        pattern = re.compile(rf"\b{re.escape(node)}\b")
        return not any(
            pattern.search(body) for other, body in self.rules.items() if other != node
        )

    def functional_effect(self, node: str) -> dict[str, list[str]]:
        """Maternal nodes this input actually MOVES, per recorded arm.

        Topological reach is not experimental information. ``IN_ANTI_SPP1``
        reaches ``E_RECEPTIVE_SURFACE`` through ``X_SPP1_LUMEN_FREE``, but that
        node is one disjunct of eight and the other seven are saturated under
        hormone treatment, so toggling it moves nothing maternal in any arm the
        repository records. Reporting the reach alone would overstate the
        experiment; this reports what actually changes.
        """
        if node not in self.rules or not node.startswith("IN_"):
            return {}
        order = _topological_order(
            self.rules, {n for n in self.rules if self.rules[n].strip() == n}
        )
        seeds, _states, mask = _latent_seeds(self.facts.latent)
        moved: dict[str, list[str]] = {}
        for arm in self.facts.arms:
            base = _evaluate(self.rules, order, seeds, mask, arm.inputs)
            flipped = _evaluate(
                self.rules,
                order,
                seeds,
                mask,
                {**arm.inputs, node: not arm.inputs.get(node, False)},
            )
            changed = sorted(
                n
                for n in self.rules
                if n.startswith(MATERNAL_PREFIXES)
                and (base[n] & mask) != (flipped[n] & mask)
            )
            if changed:
                moved[arm.arm_id] = changed
        return moved

    def downstream(self, node: str) -> set[str]:
        """Every node whose value can depend on ``node``, transitively."""
        children: dict[str, set[str]] = defaultdict(set)
        for target, body in self.rules.items():
            if target == node and self.rules[target].strip() == target:
                continue
            for name in self.rules:
                if name != target and re.search(rf"\b{re.escape(name)}\b", body):
                    children[name].add(target)
        seen: set[str] = set()
        stack = [node]
        while stack:
            current = stack.pop()
            for child in children.get(current, ()):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        return seen


def _evidence_profile(sources: Sources, ref_ids: list[str]) -> tuple[str, list[str]]:
    """Species/level summary, derived from references.tsv rather than asserted."""
    if not ref_ids:
        return "none_cited", []
    details: list[str] = []
    human = transferred = 0
    for ref_id in ref_ids:
        row = sources.references.get(ref_id)
        if row is None:
            details.append(f"{ref_id} (NOT IN references.tsv)")
            continue
        species = row.get("species", "").strip()
        details.append(
            f"{ref_id} {row.get('first_author', '')} {row.get('year', '')} [{species}]"
        )
        low = species.lower()
        if "human" in low:
            human += 1
        if "mouse" in low and "human" not in low:
            transferred += 1
    if human and not transferred:
        level = "direct_human"
    elif human and transferred:
        level = "human_plus_transferred"
    elif transferred:
        level = "transferred_only"
    else:
        level = "unclassified"
    return level, details


def derive(sources: Sources, row: dict[str, str]) -> dict[str, Any]:
    nodes = _split(row["interrogates_nodes"])
    present = [n for n in nodes if n in sources.rules]
    missing = [n for n in nodes if n not in sources.rules]
    zero_degree = [n for n in present if sources.is_zero_degree(n)]

    reach: set[str] = set()
    for node in present:
        reach |= sources.downstream(node) | {node}
    maternal_hit = sorted(
        n for n in reach if n.startswith(MATERNAL_PREFIXES) and n in sources.rules
    )
    terminal_hit = sorted(n for n in reach if n in TERMINAL_NODES)

    functional: dict[str, list[str]] = {}
    for node in present:
        for arm_id, changed in sources.functional_effect(node).items():
            functional.setdefault(arm_id, [])
            functional[arm_id] = sorted(set(functional[arm_id]) | set(changed))
    moves_maternal = bool(functional)
    inputs_present = [n for n in present if n.startswith("IN_")]

    if maternal_hit:
        scope = "maternal_and_downstream" if terminal_hit else "maternal_only"
    elif terminal_hit:
        scope = "terminal_adhesion_only"
    elif present:
        scope = "no_downstream_effect"
    else:
        scope = "no_model_image"

    couplings = {}
    aliases = {}
    for node in present:
        entry = sources.coupling.get(node)
        if entry:
            couplings[node] = entry["adjudication"]
        members = sources.alias_class.get(node, ())
        if len(members) > 1:
            aliases[node] = members

    implemented = [
        p["perturbation_id"]
        for p in sources.perturbations
        if p.get("target_node") in nodes
    ]

    separates = [
        v["variant_id"]
        for v in sources.variants
        if any(n and n in v.get("rule_change", "") for n in nodes)
        or any(n and n in v.get("added_nodes", "") for n in nodes)
    ]

    readouts = _split(row["proximal_readouts"])
    readout_status = {}
    for readout in readouts:
        key = _normalise(readout.split("/")[0])
        if any(key and key in _normalise(p) for p in sources.observed_proteins):
            readout_status[readout] = "in_observation_map"
        elif any(key and key in _normalise(p) for p in sources.planned_readouts):
            readout_status[readout] = "planned_only"
        else:
            readout_status[readout] = "NOT_IN_OBSERVATION_LAYER"

    level, ref_details = _evidence_profile(sources, _split(row["ref_ids"]))

    return {
        "nodes_present": present,
        "nodes_missing": missing,
        "zero_degree_nodes": zero_degree,
        "has_model_image": bool(present) and not all(n in zero_degree for n in present),
        "scope": scope,
        "maternal_nodes_reached": len(maternal_hit),
        "moves_maternal_in_a_recorded_arm": moves_maternal,
        "functional_maternal_effect": functional,
        "has_testable_input": bool(inputs_present),
        "terminal_nodes_reached": terminal_hit,
        "couplings": couplings,
        "aliases": aliases,
        "implemented_as": implemented,
        "separates_variants": sorted(set(separates)),
        "readout_status": readout_status,
        "evidence_level": level,
        "reference_details": ref_details,
    }


def diagnostics(rows: list[tuple[dict[str, str], dict[str, Any]]]) -> list[str]:
    """The regeneration checks. Each one is a thing that silently rots."""
    out: list[str] = []
    for row, d in rows:
        cid = row["candidate_id"]
        if d["nodes_missing"]:
            out.append(
                f"{cid}: names {len(d['nodes_missing'])} node(s) absent from the "
                f"network -- {', '.join(d['nodes_missing'])}"
            )
        if d["zero_degree_nodes"]:
            out.append(
                f"{cid}: interrogates zero-degree input(s) "
                f"{', '.join(d['zero_degree_nodes'])} -- declared but read by no "
                "rule, so the model predicts no effect"
            )
        if not d["has_model_image"] and row["status"] == "active":
            out.append(f"{cid}: ACTIVE but has no model image")
        unmeasurable = [
            r for r, s in d["readout_status"].items() if s == "NOT_IN_OBSERVATION_LAYER"
        ]
        if unmeasurable and row["status"] == "active":
            out.append(
                f"{cid}: proximal readout(s) not in the observation layer -- "
                f"{', '.join(unmeasurable)}"
            )
        if d["evidence_level"] == "transferred_only":
            out.append(f"{cid}: supported only by non-human evidence")
        if d["evidence_level"] == "none_cited" and row["status"] == "active":
            out.append(f"{cid}: ACTIVE but cites no reference")
        if (
            d["has_testable_input"]
            and not d["moves_maternal_in_a_recorded_arm"]
            and row["curator_maternal_value"] in {"high", "medium"}
        ):
            out.append(
                f"{cid}: curated maternal value is "
                f"'{row['curator_maternal_value']}' but the perturbation moves no "
                "maternal node in any recorded arm -- check this is not structural "
                "reach being mistaken for experimental information"
            )
        for detail in d["reference_details"]:
            if "NOT IN references.tsv" in detail:
                out.append(f"{cid}: cites an unknown reference -- {detail}")
    return out


def uncovered_couplings(
    sources: Sources, rows: list[tuple[dict[str, str], dict[str, Any]]]
) -> list[str]:
    """ARTIFICIALLY_COUPLED nodes that no active candidate interrogates."""
    covered: set[str] = set()
    for row, d in rows:
        if row["status"] == "active":
            covered.update(d["nodes_present"])
    return sorted(
        node
        for node, entry in sources.coupling.items()
        if entry["adjudication"] == "ARTIFICIALLY_COUPLED" and node not in covered
    )


def _fmt_list(values: list[str], empty: str = "none") -> str:
    return ", ".join(f"`{v}`" for v in values) if values else empty


def render(sources: Sources, rows: list[tuple[dict[str, str], dict[str, Any]]]) -> str:
    lines: list[str] = []
    a = lines.append

    # The banner carries no generation date. A wall-clock stamp made an
    # unchanged report rewrite itself on a new day, so a clean checkout went
    # dirty for nothing; pinned by
    # test_generated_date_determinism.ClockFrozenRegenerationTest.
    a("# ADOC Digital Twin — calibration / discrimination candidates")
    a("")
    a(
        f"> **Generated file — do not edit.** Regenerate with "
        f"`pixi run build-calibration-candidates`. Sources: the curated "
        f"`{CURATED}` plus the committed model `{MODEL_VERSION}` and the "
        "evidence layer."
    )
    a("")
    a(
        "This ranks usefulness for **mechanistic discrimination of the maternal "
        "DT**, not contraceptive efficacy. Information value is reported on "
        "separate axes and deliberately **not** collapsed into one score: a "
        "candidate can be strong for the terminal interface abstraction and weak "
        "for the maternal core, and a single number would hide exactly that."
    )
    a("")
    a(
        "Everything structural below is **derived** from the committed model and "
        "evidence files. Only judgement fields are curated. Where the two "
        "disagree, the derived column is right and the curated row needs fixing."
    )
    a("")

    a("## Summary")
    a("")
    a(
        "| Candidate | Compartment | Ambiguity tested | Proximal readouts | "
        "Maternal-DT info | Interface info | Embryo | Perturbations | Model status | Evidence |"
    )
    a("|---|---|---|---|---|---|---|---|---|---|")
    for row, d in rows:
        model_status = (
            "existing"
            if d["implemented_as"]
            else ("present" if d["has_model_image"] else "**absent**")
        )
        if d["zero_degree_nodes"]:
            model_status = "**zero-degree**"
        readouts = ", ".join(list(d["readout_status"])[:3]) or "—"
        a(
            f"| **{row['candidate_id']}** {row['title']} | {row['compartment']} | "
            f"{row['ambiguity_tested'][:80]}{'…' if len(row['ambiguity_tested']) > 80 else ''} | "
            f"{readouts} | {row['curator_maternal_value']} | "
            f"{row['curator_interface_value']} | {row['embryo_required']} | "
            f"{row['perturbation_count']} | {model_status} | {d['evidence_level']} |"
        )
    a("")

    a("## Candidates")
    a("")
    for row, d in rows:
        a(f"### {row['candidate_id']} — {row['title']}")
        a("")
        a(
            f"**Status:** `{row['status']}` · **Compartment:** {row['compartment']} · "
            f"**Perturbations required:** {row['perturbation_count']} · "
            f"**Embryo required:** {row['embryo_required']}"
        )
        a("")
        a(f"**Purpose.** {row['purpose']}")
        a("")
        a(f"**Experiment.** {row['experiment']}")
        a("")
        a(f"**Ambiguity tested.** {row['ambiguity_tested']}")
        a("")
        a(f"**Expected effect.** {row['expected_effect']}")
        a("")

        a("**Model image (derived).**")
        a("")
        a(f"* nodes present: {_fmt_list(d['nodes_present'])}")
        if d["nodes_missing"]:
            a(f"* **nodes NOT in the network: {_fmt_list(d['nodes_missing'])}**")
        if d["zero_degree_nodes"]:
            a(
                f"* **zero-degree (declared, read by no rule): "
                f"{_fmt_list(d['zero_degree_nodes'])}** — the model predicts no effect"
            )
        if row["interrogates_concepts"]:
            a(f"* concepts without a node: {row['interrogates_concepts']}")
        a(
            f"* reach: **{d['scope']}** "
            f"({d['maternal_nodes_reached']} maternal node(s) downstream"
            + (
                f", terminal: {_fmt_list(d['terminal_nodes_reached'])}"
                if d["terminal_nodes_reached"]
                else ""
            )
            + ")"
        )
        if d["implemented_as"]:
            a(f"* already implemented as: {_fmt_list(d['implemented_as'])}")
        if d["separates_variants"]:
            a(f"* Gate-3 variants it touches: {_fmt_list(d['separates_variants'])}")
        a("")

        if d["couplings"]:
            a("**Coupling adjudication (derived).**")
            a("")
            for node, verdict in sorted(d["couplings"].items()):
                members = d["aliases"].get(node, ())
                extra = (
                    f" — alias class of {len(members)}: {_fmt_list(list(members))}"
                    if members
                    else ""
                )
                a(f"* `{node}`: **{verdict}**{extra}")
            a("")

        a("**Proximal readouts (derived availability).**")
        a("")
        if d["readout_status"]:
            for readout, status in d["readout_status"].items():
                mark = "**" if status == "NOT_IN_OBSERVATION_LAYER" else ""
                a(f"* {readout}: {mark}{status}{mark}")
        else:
            a("* none specified")
        a("")

        a(f"**Evidence.** `{d['evidence_level']}`")
        a("")
        for detail in d["reference_details"]:
            a(f"* {detail}")
        if not d["reference_details"]:
            a("* no reference cited")
        a("")
        a(f"**Feasibility.** `{row['feasibility']}`")
        a("")
        a(f"**Still uncertain.** {row['open_uncertainty']}")
        a("")

    a("## Regeneration diagnostics")
    a("")
    checks = diagnostics(rows)
    if checks:
        a("Things the generator found wrong or worth knowing, this run:")
        a("")
        for item in checks:
            a(f"* {item}")
    else:
        a("No diagnostics raised.")
    a("")

    uncovered = uncovered_couplings(sources, rows)
    a("### Artificially coupled nodes with no active discriminating candidate")
    a("")
    if uncovered:
        a(
            f"{len(uncovered)} node(s) are adjudicated `ARTIFICIALLY_COUPLED` but no "
            "active candidate interrogates them:"
        )
        a("")
        a(_fmt_list(uncovered))
    else:
        a(
            "None — every artificially coupled node is interrogated by some active candidate."
        )
    a("")
    return "\n".join(lines) + "\n"


def build(root: Path | None = None) -> tuple[Path, Path]:
    sources = Sources.load(root)
    active = sources.root
    curated = _load_tsv(active / CURATED)
    rows = [(row, derive(sources, row)) for row in curated]

    md_path = active / OUT_MD
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render(sources, rows), encoding="utf-8")

    tsv_path = active / OUT_TSV
    with tsv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "candidate_id",
                "status",
                "compartment",
                "perturbation_count",
                "embryo_required",
                "curator_maternal_value",
                "curator_interface_value",
                "has_model_image",
                "scope",
                "nodes_present",
                "nodes_missing",
                "zero_degree_nodes",
                "maternal_nodes_reached",
                "implemented_as",
                "separates_variants",
                "unmeasurable_readouts",
                "evidence_level",
            ]
        )
        for row, d in rows:
            writer.writerow(
                [
                    row["candidate_id"],
                    row["status"],
                    row["compartment"],
                    row["perturbation_count"],
                    row["embryo_required"],
                    row["curator_maternal_value"],
                    row["curator_interface_value"],
                    d["has_model_image"],
                    d["scope"],
                    ";".join(d["nodes_present"]),
                    ";".join(d["nodes_missing"]),
                    ";".join(d["zero_degree_nodes"]),
                    d["maternal_nodes_reached"],
                    ";".join(d["implemented_as"]),
                    ";".join(d["separates_variants"]),
                    ";".join(
                        r
                        for r, s in d["readout_status"].items()
                        if s == "NOT_IN_OBSERVATION_LAYER"
                    ),
                    d["evidence_level"],
                    d["moves_maternal_in_a_recorded_arm"],
                ]
            )
    return md_path, tsv_path


if __name__ == "__main__":  # pragma: no cover
    md, tsv = build()
    print(f"wrote {md}")
    print(f"wrote {tsv}")
