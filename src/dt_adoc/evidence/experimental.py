"""Per-experiment evidence for every regulatory edge of a model version.

``context/evidence/edge_experimental_evidence.tsv`` is the canonical store: one
row per independent experimental evidence piece for one specific edge. An edge
appears in many rows, and one publication appears in several rows when it
reports different experiments, systems or perturbations. The rubric and the
vocabularies are in ``docs/evidence_grading.md``; the edge-level aggregation and
the confidence filter are specified in its section 7 and are not implemented
here or anywhere else yet.

This module extends, rather than replaces, the relation-level infrastructure of
``dt_adoc.evidence.assertions``:

* the seed set is that module's migration logic applied to the target model
  version: the evidence register's topic fan-out, minus every retraction and
  plus every attachment in ``config/edge_citation_adjudications.tsv``. A seed
  records its lineage in ``migrated_from``: the v0.3.0 ``assertion_id`` it was
  migrated from, or ``seeded:<model version>`` where that table has no such
  assertion because the edge entered the family after v0.3.0 (LE096). Both are
  checked, so ``migrated_from`` can never name a parent that does not exist;
* curator-owned columns survive regeneration (the ``_merge_curation`` contract
  of the v0.3.0 table), keyed on a stable ``evidence_piece_id``;
* the v0.3.0 table itself is left untouched as the historical paper-level
  store.

Which edges exist is decided by the executable network, not by the historical
edge catalog. ``edge_context`` parses ``network.bnd`` with the topology parser,
reconciles the computed dependencies against the version's committed
``topology.tsv``, and fails on any disagreement. Retired edges keep their rows
as history with ``edge_status = retired``.

Regeneration only ever adds missing seed rows and refreshes the generated
columns. It never deletes a row, never renames an id and never overwrites a
curated cell, so curation cannot be lost by rebuilding.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from dt_adoc.evidence.citation_adjudications import (
    check_applicability,
    load_with_addenda,
    partition,
)
from dt_adoc.model.topology import (
    SIGN_VALUES,
    derive_dependencies,
    parse_bnd_rules,
)

DEFAULT_MODEL_VERSION = "adoc-literature-superset-v0.6.0"
EVIDENCE_TABLE_PATH = Path("context/evidence/edge_experimental_evidence.tsv")
EDGE_ROLES_PATH = Path("context/evidence/edge_roles.tsv")
EVIDENCE_REGISTER_PATH = Path("context/evidence-register.tsv")
REFERENCES_PATH = Path("context/literature/references.tsv")
CITATION_ADJUDICATIONS_PATH = Path("config/edge_citation_adjudications.tsv")
#: Citation directives decided after the Phase 2B closure froze the file above.
#: They live outside the frozen paths and are read by this pipeline only: the
#: historical v0.3.0 generator in ``dt_adoc.evidence.assertions`` must keep
#: replaying against the frozen registry alone, or a decision made in 2026
#: would retroactively change what the migration is recorded as having done.
#: Ordered oldest first; add a dated file rather than editing an existing one.
POST_CLOSURE_ADJUDICATION_PATHS = (
    Path("context/evidence/post_closure_citation_adjudications_2026-11-18.tsv"),
)
TOPOLOGY_EXEMPTIONS_PATH = Path("config/topology_parity_exemptions.tsv")
NODE_ENTITY_MAP_PATH = Path("config/node_entity_map.tsv")
V030_ASSERTIONS_PATH = Path(
    "models/superset/adoc-literature-superset-v0.3.0/edge_evidence_assertions.tsv"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def model_dir(model_version: str, root: Path) -> Path:
    return root / "models" / "superset" / model_version


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

#: Columns regenerated from the model version and the bibliography on every
#: build. A hand edit to one of these is overwritten, by design.
GENERATED_COLUMNS = (
    "edge_id",
    "source",
    "target",
    "sign",
    "boolean_rule",
    "compartment",
    "edge_status",
    "edge_role",
    "model_version",
    "publication",
    "doi",
)

#: Columns a curator owns. Regeneration never overwrites a value here.
CURATED_COLUMNS = (
    "evidence_piece_id",
    "reference_id",
    "source_observation_id",
    "source_location",
    "source_verification",
    "independence_group",
    "migrated_from",
    "species",
    "experimental_model",
    "cell_source",
    "cell_line",
    "cell_type",
    "model_details",
    "experiment_type",
    "perturbation",
    "perturbation_target",
    "perturbation_direction",
    "measured_effect",
    "response_direction",
    "readout_quantitation",
    "functional_endpoint",
    "controls",
    "rescue_experiment",
    "biological_replicates",
    "experimental_limitations",
    "experimental_strength",
    "human_ADOC_relevance",
    "edge_support",
    "overall_confidence",
    "confidence_rationale",
    "limitations_rationale",
    "curation_status",
    "curated_on",
)

#: Column order of the written table: interaction, provenance, system,
#: experiment, assessment.
COLUMNS = (
    # A. regulatory interaction
    "edge_id",
    "source",
    "target",
    "sign",
    "boolean_rule",
    "compartment",
    "edge_status",
    "edge_role",
    "model_version",
    # B. publication and provenance
    "evidence_piece_id",
    "reference_id",
    "source_observation_id",
    "publication",
    "doi",
    "source_location",
    "source_verification",
    "independence_group",
    "migrated_from",
    # C. experimental system
    "species",
    "experimental_model",
    "cell_source",
    "cell_line",
    "cell_type",
    "model_details",
    # D. experimental evidence
    "experiment_type",
    "perturbation",
    "perturbation_target",
    "perturbation_direction",
    "measured_effect",
    "response_direction",
    "readout_quantitation",
    "functional_endpoint",
    "controls",
    "rescue_experiment",
    "biological_replicates",
    "experimental_limitations",
    # E. evidence assessment
    "experimental_strength",
    "human_ADOC_relevance",
    "edge_support",
    "overall_confidence",
    "confidence_rationale",
    "limitations_rationale",
    "curation_status",
    "curated_on",
)
assert set(COLUMNS) == set(GENERATED_COLUMNS) | set(CURATED_COLUMNS)

EDGE_STATUS_VALUES = ("active", "retired")
EDGE_ROLE_VALUES = (
    "biological_regulatory",
    "external_input",
    "phenotype_definition",
    "structural_relay",
)
SOURCE_VERIFICATION_VALUES = (
    "full_text_verified",
    "full_text_partial",
    "abstract_only",
    "secondary_summary",
    "unavailable",
    "not_examined",
)
EXPERIMENTAL_MODEL_VALUES = (
    "in_vivo",
    "primary_culture",
    "organoid",
    "assembloid_or_coculture",
    "cell_line",
    "tissue_explant",
    "tissue_section",
    "in_vitro_biochemical",
    "computational",
    "review",
    "not_reported",
    "not_examined",
)
CELL_SOURCE_VALUES = (
    "donor_derived_primary",
    "immortalized_primary_like",
    "cancer_derived",
    "embryonic",
    "animal_in_vivo",
    "animal_primary",
    "not_applicable",
    "not_reported",
    "not_examined",
)
EXPERIMENT_TYPE_VALUES = (
    "knockout",
    "conditional_knockout",
    "knockdown",
    "overexpression",
    "pharmacological_inhibition",
    "pharmacological_activation",
    "recombinant_protein",
    "blocking_antibody",
    "hormone_treatment",
    "chip",
    "reporter_assay",
    "binding_assay",
    "rna_seq",
    "single_cell_rna_seq",
    "expression_profiling",
    "immunostaining",
    "western_blot",
    "elisa",
    "adhesion_assay",
    "biophysical_measurement",
    "computational_inference",
    "review_statement",
    "not_examined",
)
#: ``rescue_experiment`` records which specificity route the experiment used.
#: The rubric lists four, and all four must be writable: representing only
#: rescue forced a two-independent-siRNA experiment -- which the rubric calls
#: strong -- to be graded down for lacking something it never needed.
RESCUE_VALUES = (
    "rescue",
    "two_independent_reagents",
    "gain_and_loss",
    "orthogonal_method",
    "none",
    "not_applicable",
    "not_reported",
    "not_examined",
)

#: The routes that satisfy ``experimental_strength='strong'``.
SPECIFICITY_ROUTES = (
    "rescue",
    "two_independent_reagents",
    "gain_and_loss",
    "orthogonal_method",
)

#: Which way the regulator was moved, and which way the target responded. An
#: edge carries a sign, so support for it is a statement about *both*: lowering
#: an inhibitor must raise its target. Without these two columns a knockdown of
#: KLF12 followed by less LIF validated as direct support for the inhibitory
#: edge LE091, which is the opposite of what that edge claims.
PERTURBATION_DIRECTION_VALUES = (
    "increase",
    "decrease",
    "not_applicable",
    "not_examined",
)
RESPONSE_DIRECTION_VALUES = (
    "increase",
    "decrease",
    "no_change",
    "not_applicable",
    "not_examined",
)

#: The values that actually state a direction. ``not_applicable`` and
#: ``not_examined`` are the two ways of recording that none was observed, and
#: neither may stand in for one on a row that perturbed something.
DIRECTIONS_PERTURBED = ("increase", "decrease")
DIRECTIONS_OBSERVED = ("increase", "decrease", "no_change")

#: Experiment types that observe without perturbing. The rubric grades
#: association as ``weak``; a row whose every type is one of these cannot be
#: ``moderate`` or ``strong``, whatever else it records. Controlled molecular
#: experiments the rubric does allow at ``moderate`` -- ChIP, reporter, binding
#: assays -- are deliberately absent.
ASSOCIATION_ONLY_EXPERIMENT_TYPES = (
    "expression_profiling",
    "rna_seq",
    "single_cell_rna_seq",
    "immunostaining",
    "western_blot",
    "elisa",
    "computational_inference",
    "review_statement",
)

#: Systems in which a human result can be `direct` for the ADOC: donor tissue
#: and what is grown straight from it. A cancer or immortalised line is not
#: here, and neither is anything grown from one.
DIRECT_ELIGIBLE_MODELS = (
    "primary_culture",
    "organoid",
    "assembloid_or_coculture",
    "tissue_explant",
    "tissue_section",
    "in_vivo",
)

READOUT_QUANTITATION_VALUES = (
    "quantitative",
    "semi_quantitative",
    "qualitative",
    "not_reported",
    "not_examined",
)
STRENGTH_VALUES = ("strong", "moderate", "weak", "insufficient", "unassessed")
RELEVANCE_VALUES = ("direct", "close", "indirect", "poor", "unknown", "unassessed")
SUPPORT_VALUES = (
    "direct",
    "partial",
    "contradictory",
    "not_demonstrated",
    "unassessed",
)
CONFIDENCE_VALUES = ("high", "medium", "low", "unsupported", "unassessed")
CURATION_STATUS_VALUES = ("verified", "provisional", "unreviewed", "disputed")

#: Multi-valued (semicolon-separated) controlled columns.
MULTI_VALUED = {
    "experimental_model": EXPERIMENTAL_MODEL_VALUES,
    "cell_source": CELL_SOURCE_VALUES,
    "experiment_type": EXPERIMENT_TYPE_VALUES,
}
SINGLE_VALUED = {
    "edge_status": EDGE_STATUS_VALUES,
    "edge_role": EDGE_ROLE_VALUES,
    "source_verification": SOURCE_VERIFICATION_VALUES,
    "rescue_experiment": RESCUE_VALUES,
    "readout_quantitation": READOUT_QUANTITATION_VALUES,
    "perturbation_direction": PERTURBATION_DIRECTION_VALUES,
    "response_direction": RESPONSE_DIRECTION_VALUES,
    "experimental_strength": STRENGTH_VALUES,
    "human_ADOC_relevance": RELEVANCE_VALUES,
    "edge_support": SUPPORT_VALUES,
    "overall_confidence": CONFIDENCE_VALUES,
    "curation_status": CURATION_STATUS_VALUES,
}

#: Free-text cells an examined row must fill. They may say ``not_reported``,
#: which records that the source was read and does not state it, but they may
#: not be blank: these are what the grade is read off.
DESCRIPTIVE_COLUMNS = (
    "cell_type",
    "perturbation",
    "perturbation_target",
    "measured_effect",
    "functional_endpoint",
    "controls",
    "biological_replicates",
    "experimental_limitations",
)

#: Values that look filled in but assert nothing. ``controls`` is prose, so a
#: non-empty check alone accepted ``none`` as adequate controls.
_NULLISH = frozenset(
    {
        "none",
        "no",
        "n/a",
        "na",
        "-",
        "--",
        "nil",
        "not reported",
        "not_reported",
        "not stated",
        "not applicable",
        "not_applicable",
        "not examined",
        "not_examined",
        "unknown",
    }
)


def _asserts_nothing(value: str) -> bool:
    """Is this prose cell a null in disguise?

    Compared on letters and digits alone: an exact-match test accepted
    ``None.`` as adequate controls because of the full stop.
    """
    return re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip() in {
        re.sub(r"[^a-z0-9]+", " ", token).strip() for token in _NULLISH
    }


#: ``experiment_type`` values that perturb the regulator. The rubric's
#: ``edge_support='direct'`` and ``experimental_strength='strong'`` both require
#: one; observing, profiling or binding assays do not qualify.
PERTURBATION_EXPERIMENT_TYPES = (
    "knockout",
    "conditional_knockout",
    "knockdown",
    "overexpression",
    "pharmacological_inhibition",
    "pharmacological_activation",
    "recombinant_protein",
    "blocking_antibody",
    "hormone_treatment",
)

ASSESSMENT_COLUMNS = (
    "experimental_strength",
    "human_ADOC_relevance",
    "edge_support",
    "overall_confidence",
)

#: Ordinal ranks used by the ceiling rule and by sorting.
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1, "unsupported": 0, "unassessed": -1}
STRENGTH_RANK = {
    "strong": 3,
    "moderate": 2,
    "weak": 1,
    "insufficient": 0,
    "unassessed": -1,
}

_EVIDENCE_PIECE_ID = re.compile(
    r"^EVP-(?P<edge>[A-Z]+-?\d+[A-Z]?)-(?P<src>[A-Z0-9]+)-(?P<n>\d{2})$"
)

#: Organisms a ``species`` entry may name. Closed, so an organism the validator
#: does not know cannot slip past the relevance rule as if it were human: an
#: unlisted species is an error, and a non-human one is written
#: ``other_nonhuman`` with the organism in ``model_details``.
ORGANISM_VALUES = (
    "human",
    "mouse",
    "rat",
    "rabbit",
    "guinea_pig",
    "baboon",
    "macaque",
    "bovine",
    "porcine",
    "ovine",
    "other_nonhuman",
    "not_applicable",
)

#: ``species`` is a semicolon list of ``organism`` or ``compartment: organism``
#: entries, one per relevant compartment (``maternal: human; embryo: mouse``).
_SPECIES_ENTRY = re.compile(
    r"^(?:(?P<compartment>[a-z][a-z_ ]*):\s*)?(?P<organism>[a-z_]+)$"
)

#: ``migrated_from`` is either the v0.3.0 assertion a seed was migrated from, or
#: ``seeded:<model version>`` for a seed whose edge the v0.3.0 table never had,
#: or empty for a row a curator added. Anything else is an error.
_SEEDED_LINEAGE = re.compile(r"^seeded:(?P<version>adoc-literature-superset-v[0-9.]+)$")


class EvidenceTableError(RuntimeError):
    """The canonical table, its inputs, or the model's topology disagree."""


# --------------------------------------------------------------------------
# TSV io (LF line endings; see tests/unit/test_line_endings.py)
# --------------------------------------------------------------------------


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [
            {key: (value or "") for key, value in row.items()}
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def render_tsv(rows: Sequence[Mapping[str, object]], columns: Sequence[str]) -> str:
    """The exact text ``write_tsv_lf`` writes, for currentness checks."""
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(columns),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue()


def write_tsv_lf(
    path: Path, rows: Sequence[Mapping[str, object]], columns: Sequence[str]
) -> None:
    """Write a TSV with LF endings and a fixed column order.

    ``dt_adoc.reporting.tables.write_tsv`` emits CRLF (csv's default), which
    would grow the repository's pinned CRLF inventory; new tables are LF.
    """
    for row in rows:
        for column in columns:
            value = str(row.get(column, ""))
            if "\t" in value or "\n" in value or "\r" in value:
                raise EvidenceTableError(
                    f"{path}: column {column!r} of row {row.get('evidence_piece_id') or row.get('edge_id')} "
                    "contains a tab or a line break"
                )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_tsv(rows, columns), encoding="utf-8", newline="")


# --------------------------------------------------------------------------
# Edge context: what the executable network computes
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class EdgeContext:
    edge_id: str
    source: str
    target: str
    sign: str
    boolean_rule: str
    compartment: str
    edge_status: str
    provenance_status: str
    model_version: str


def _edge_compartment(source: str, target: str, compartments: Mapping[str, str]) -> str:
    src = compartments.get(source, "not_in_model")
    tgt = compartments.get(target, "not_in_model")
    return src if src == tgt else f"{src}->{tgt}"


def edge_context(
    model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> dict[str, EdgeContext]:
    """Every active and retired edge of ``model_version``, keyed by edge id.

    Active means computed by ``network.bnd``. The computed dependency set must
    equal the active rows of the committed ``topology.tsv`` and agree on sign;
    otherwise this raises rather than guessing which one is right.
    """
    root = root or repo_root()
    directory = model_dir(model_version, root)
    rules = parse_bnd_rules(directory / "network.bnd")
    derived = derive_dependencies(rules)
    topology = read_tsv(directory / "topology.tsv")
    curated = {row["edge_id"]: row for row in read_tsv(directory / "edge_evidence.tsv")}
    compartments = {
        row["node_id"]: row["compartment"]
        for row in read_tsv(directory / "node_dictionary.tsv")
    }

    errors: list[str] = []
    active_topology: dict[tuple[str, str], dict[str, str]] = {}
    contexts: dict[str, EdgeContext] = {}
    for row in topology:
        pair = (row["source"], row["target"])
        status = row["provenance_status"]
        key = row["edge_id"] or row["exemption_id"]
        if not key:
            errors.append(f"topology row {pair} has neither edge_id nor exemption_id")
            continue
        if key in contexts:
            errors.append(f"topology key {key} appears twice")
            continue
        if status == "retired":
            sign = curated.get(row["edge_id"], {}).get("sign", "")
            if not sign:
                errors.append(f"retired edge {key} has no curated sign")
            contexts[key] = EdgeContext(
                edge_id=key,
                source=pair[0],
                target=pair[1],
                sign=sign,
                boolean_rule=rules.get(pair[1], ""),
                compartment=_edge_compartment(pair[0], pair[1], compartments),
                edge_status="retired",
                provenance_status=status,
                model_version=model_version,
            )
            continue
        active_topology[pair] = row
        sign = derived.get(pair)
        if sign is None:
            errors.append(
                f"topology.tsv lists {pair} ({key}) as {status} but network.bnd does not compute it"
            )
            continue
        if sign != row["derived_sign"]:
            errors.append(
                f"{key}: topology.tsv sign {row['derived_sign']!r} but network.bnd gives {sign!r}"
            )
        if row["edge_id"] and curated.get(row["edge_id"], {}).get("sign") != sign:
            errors.append(
                f"{key}: edge_evidence.tsv sign disagrees with the executable rule ({sign})"
            )
        contexts[key] = EdgeContext(
            edge_id=key,
            source=pair[0],
            target=pair[1],
            sign=sign,
            boolean_rule=rules[pair[1]],
            compartment=_edge_compartment(pair[0], pair[1], compartments),
            edge_status="active",
            provenance_status=status,
            model_version=model_version,
        )
    missing = sorted(set(derived) - set(active_topology))
    if missing:
        errors.append(
            f"network.bnd computes dependencies absent from topology.tsv: {missing}"
        )
    if errors:
        raise EvidenceTableError("; ".join(errors))
    return contexts


def active_edges(contexts: Mapping[str, EdgeContext]) -> list[EdgeContext]:
    return [context for context in contexts.values() if context.edge_status == "active"]


# --------------------------------------------------------------------------
# Roles
# --------------------------------------------------------------------------

ROLE_COLUMNS = ("edge_id", "source", "target", "edge_role", "rationale")


def load_roles(root: Path | None = None) -> dict[str, dict[str, str]]:
    root = root or repo_root()
    path = root / EDGE_ROLES_PATH
    if not path.exists():
        return {}
    rows = read_tsv(path)
    roles: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["edge_id"] in roles:
            raise EvidenceTableError(f"{path}: edge {row['edge_id']} classified twice")
        roles[row["edge_id"]] = row
    return roles


def validate_roles(
    roles: Mapping[str, Mapping[str, str]], contexts: Mapping[str, EdgeContext]
) -> list[str]:
    errors: list[str] = []
    active = {context.edge_id: context for context in active_edges(contexts)}
    for edge_id, context in active.items():
        row = roles.get(edge_id)
        if row is None:
            errors.append(
                f"active edge {edge_id} ({context.source} -> {context.target}) has no role"
            )
            continue
        if (row["source"], row["target"]) != (context.source, context.target):
            errors.append(
                f"edge_roles.tsv names {edge_id} as {row['source']} -> {row['target']}, "
                f"the model computes {context.source} -> {context.target}"
            )
        if row["edge_role"] not in EDGE_ROLE_VALUES:
            errors.append(f"edge {edge_id} has unknown role {row['edge_role']!r}")
        if not row["rationale"].strip():
            errors.append(f"edge {edge_id} role has no rationale")
    for edge_id in sorted(set(roles) - set(active)):
        errors.append(
            f"edge_roles.tsv classifies {edge_id}, which is not an active edge"
        )
    return errors


# --------------------------------------------------------------------------
# Migration seeds
# --------------------------------------------------------------------------


def compact(identifier: str) -> str:
    """``REF-008`` -> ``REF008``; ``SOFIA-HT-001`` -> ``SOFIAHT001``."""
    return re.sub(r"[^A-Z0-9]", "", identifier.upper())


def piece_id(edge_id: str, source_id: str, serial: int) -> str:
    return f"EVP-{edge_id}-{compact(source_id)}-{serial:02d}"


@dataclass(frozen=True)
class Seed:
    edge_id: str
    reference_id: str
    source_observation_id: str
    migrated_from: str

    @property
    def source_id(self) -> str:
        return self.reference_id or self.source_observation_id

    @property
    def piece_id(self) -> str:
        return piece_id(self.edge_id, self.source_id, 1)


def migration_seeds(
    model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> list[Seed]:
    """The paper-level citations of every curated edge of ``model_version``.

    The same fan-out as ``dt_adoc.evidence.assertions.migrate_edge_evidence``:
    register topic references, minus retractions, plus attachments, and one
    in-house seed per ``SOFIA-*`` evidence id. Retractions therefore never come
    back through regeneration.
    """
    root = root or repo_root()
    edge_rows = read_tsv(model_dir(model_version, root) / "edge_evidence.tsv")
    register = {
        row["evidence_id"]: row for row in read_tsv(root / EVIDENCE_REGISTER_PATH)
    }
    references = [row["ref_id"] for row in read_tsv(root / REFERENCES_PATH)]

    def topic_references(evidence_id: str) -> list[str]:
        return [
            token.strip()
            for token in register.get(evidence_id, {}).get("location", "").split(";")
            if token.strip().startswith("REF-")
        ]

    baseline = {
        row["edge_id"]: topic_references(row["evidence_id"].strip())
        for row in edge_rows
    }
    adjudications = load_with_addenda(
        root / CITATION_ADJUDICATIONS_PATH,
        [root / path for path in POST_CLOSURE_ADJUDICATION_PATHS],
        [row["edge_id"] for row in edge_rows],
        references,
    )
    check_applicability(adjudications, baseline)
    retracted, attachments = partition(adjudications)
    parents = v030_assertion_ids(root)

    def lineage(edge_id: str, source_id: str) -> str:
        parent = f"ASRT-{edge_id}-{source_id}"
        return parent if parent in parents else f"seeded:{model_version}"

    seeds: list[Seed] = []
    for row in edge_rows:
        edge_id = row["edge_id"]
        evidence_id = row["evidence_id"].strip()
        if evidence_id.startswith("SOFIA-"):
            # The in-house observation is this edge's own seed, but it is not a
            # reason to ignore the citation file. `continue` used to end the
            # edge here, so an `attach` directive naming a SOFIA-seeded edge was
            # discarded without a word -- and `check_applicability` had already
            # passed that same directive as valid and needed, because the
            # register genuinely does not provide the reference. The generator
            # therefore contradicted its own validator, and the only visible
            # symptom was a row that never appeared. An attachment names one
            # explicit (edge, reference) pair, so nothing about an in-house seed
            # makes it inapplicable; both are emitted. Retractions are honoured
            # here too, for the same reason.
            seeds.append(Seed(edge_id, "", evidence_id, lineage(edge_id, evidence_id)))
            for ref in attachments.get(edge_id, ()):
                if (edge_id, ref) not in retracted:
                    seeds.append(Seed(edge_id, ref, "", lineage(edge_id, ref)))
            continue
        refs = list(baseline[edge_id])
        refs.extend(ref for ref in attachments.get(edge_id, ()) if ref not in refs)
        for ref in refs:
            if (edge_id, ref) not in retracted:
                seeds.append(Seed(edge_id, ref, "", lineage(edge_id, ref)))
    return seeds


def v030_assertion_ids(root: Path | None = None) -> set[str]:
    """Ids of the historical paper-level store that seeds may name as parents."""
    root = root or repo_root()
    path = root / V030_ASSERTIONS_PATH
    return {row["assertion_id"] for row in read_tsv(path)} if path.exists() else set()


def lineage_errors(
    rows: Sequence[Mapping[str, str]], seeds: Sequence[Seed]
) -> list[str]:
    """Check ``migrated_from`` against the computed seed set, which is the only
    authority on what was migrated.

    An earlier version validated each row's lineage on its own: an ``ASRT-``
    value had to exist in the v0.3.0 table and name the row's edge and source,
    and a ``seeded:`` value had to name a version curating that edge. Both tests
    pass for rows that are not migration seeds at all, so a hand-written row for
    a reference outside an edge's fan-out could claim to have been seeded. Exact
    identity with the seed set is the invariant; a resembling shape is not.
    """
    expected = {seed.piece_id: seed.migrated_from for seed in seeds}
    errors: list[str] = []
    by_id = {row.get("evidence_piece_id", ""): row for row in rows}
    for pid, lineage in sorted(expected.items()):
        row = by_id.get(pid)
        if row is None:
            errors.append(f"migration seed {pid} is missing; rebuild the table")
        elif row.get("migrated_from", "") != lineage:
            errors.append(
                f"{pid}: migrated_from {row.get('migrated_from', '')!r} is not the "
                f"lineage of this seed ({lineage!r})"
            )
    for pid, row in sorted(by_id.items()):
        value = row.get("migrated_from", "")
        if value and pid not in expected:
            errors.append(
                f"{pid}: carries lineage {value!r} but is not a migration seed; a "
                "curator-added row leaves migrated_from empty"
            )
    return errors


def node_entities(
    model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> dict[str, set[str]]:
    """``{node_id: {entity}}`` from ``config/node_entity_map.tsv``.

    The map is the repository's existing statement of which molecules a node
    stands for (Stage 4b admission reads the same file). A node with no entity
    is a derived state: nothing in a laboratory is that node, so it cannot be
    perturbed directly. Input nodes are absent from the map and are handled by
    the caller, because an input node *is* the experimental manipulation.
    """
    root = root or repo_root()
    entities: dict[str, set[str]] = {}
    for row in read_tsv(root / NODE_ENTITY_MAP_PATH):
        if row["model_version"] != model_version:
            continue
        entity = row["entity"].strip()
        entities.setdefault(row["node_id"], set())
        if entity:
            entities[row["node_id"]].add(entity)
    return entities


def perturbation_target_errors(
    row: Mapping[str, str],
    *,
    context: EdgeContext,
    entities: Mapping[str, set[str]],
    role: str,
) -> list[str]:
    """Is the thing that was perturbed this edge's own source regulator?

    Checking only that *some* perturbation was performed let an experiment that
    manipulated something else entirely count as direct support: progesterone
    treatment for ``E_PGR -> E_IHH`` (a proxy for the receptor node, which the
    rubric calls partial), or an siRNA against an unrelated gene. The target is
    therefore named in its own column and resolved against the node it must be.
    """
    target = row.get("perturbation_target", "").strip()
    source = context.source
    if not target or _asserts_nothing(target):
        return [
            (
                "edge_support='direct' requires perturbation_target to name what "
                f"was perturbed; it is {row.get('perturbation_target', '')!r}"
            )
        ]
    declared = entities.get(source, set())
    if target == source:
        # Only legitimate where the node itself is the manipulation: an
        # experimental, environmental or embryo-side input.
        if role == "external_input":
            return []
        return [
            (
                f"perturbation_target={target!r} names the model node rather than "
                "a molecule; a derived or regulatory node is perturbed through one "
                f"of its entities ({sorted(declared) or 'none declared'})"
            )
        ]
    if not declared:
        return [
            (
                f"edge_support='direct' is not available for {source}: it is a "
                "derived state with no entity in config/node_entity_map.tsv, so it "
                "cannot be perturbed itself. Evidence through a proxy is 'partial'"
            )
        ]
    if target not in declared:
        return [
            (
                f"perturbation_target={target!r} is not an entity of the edge "
                f"source {source} ({sorted(declared)}); perturbing something else "
                "is not direct support for this relation"
            )
        ]
    return []


def direction_errors(row: Mapping[str, str], *, sign: str, support: str) -> list[str]:
    """Do the recorded directions say what the edge's sign claims?

    An activation edge claims the two move together; an inhibition edge claims
    they move oppositely. So the pattern a result shows is checkable against
    the sign the model executes, and this is the one check here that can catch
    evidence pointing the wrong way along a real edge.

    Rows that record no direction (observational work, a proxy regulator) are
    not forced to invent one: the check applies only when both directions are
    recorded. What it refuses is a *recorded* pattern that contradicts the
    grade placed on it.
    """
    moved = row.get("perturbation_direction", "")
    responded = row.get("response_direction", "")
    # Nothing recorded. Whether a row was *entitled* to record nothing is the
    # caller's question (a perturbational row is not); here there is simply no
    # pattern to compare against the sign.
    if moved not in DIRECTIONS_PERTURBED or responded not in DIRECTIONS_OBSERVED:
        return []
    if sign not in SIGN_VALUES:
        return []

    if responded == "no_change":
        if support in ("direct", "partial"):
            return [
                (
                    f"response_direction='no_change' cannot be {support!r} support: "
                    "a target that did not move supports no direction. Record it as "
                    "'contradictory' if the rule requires a response here"
                )
            ]
        return []

    together = moved == responded
    claims_together = sign == "activation"
    consistent = together == claims_together
    expected = "the same direction" if claims_together else "opposite directions"
    if support in ("direct", "partial") and not consistent:
        return [
            (
                f"the recorded directions contradict the edge: {sign} means "
                f"{expected}, but the regulator was {moved}d and the target "
                f"{responded}d, yet this row is {support!r} support"
            )
        ]
    if support == "contradictory" and consistent:
        return [
            (
                f"the recorded directions agree with the {sign} edge (regulator "
                f"{moved}d, target {responded}d), so this row is not a "
                "contradiction of it"
            )
        ]
    return []


def system_coherence_errors(row: Mapping[str, str], *, relevance: str) -> list[str]:
    """Is the system internally consistent, and eligible for the relevance?

    ``experimental_model`` and ``cell_source`` describe the same cells from two
    angles, so they can disagree: a cell line that is also donor-derived
    primary tissue is not a thing, and it validated as ``direct`` because each
    column was only checked on its own.

    That contradiction only exists while the row describes *one* population.
    Both columns are multi-valued because real systems have several parts: a
    cancer line co-cultured with primary trophoblast spheroids, or a paper that
    stains donor tissue and then runs an adhesion assay in Ishikawa cells. Read
    as one population, those rows are a mislabel; read as what they are, they
    are the commonest configuration in this literature, and refusing them
    forced the curator to delete the primary half of the system from the
    record. The pairing is therefore an error only when a single model is
    declared. Nothing is loosened by this: relevance ``direct`` separately
    requires every declared model to be donor-derived, and ``cancer_derived``
    or ``immortalized_primary_like`` in ``cell_source`` separately bars both
    ``direct`` and ``close``, so a row containing a line still cannot climb.
    """
    models = set(_tokens(row.get("experimental_model", "")))
    sources = set(_tokens(row.get("cell_source", "")))
    errors: list[str] = []
    line_sources = {"cancer_derived", "immortalized_primary_like"}

    if (
        len(models) == 1
        and "cell_line" in models
        and "donor_derived_primary" in sources
    ):
        errors.append(
            "experimental_model 'cell_line' is the only system declared and "
            "contradicts cell_source 'donor_derived_primary'; a line is not "
            "donor-derived primary material. Name the other part of the system "
            "(for example 'cell_line;assembloid_or_coculture') if there is one"
        )
    if "cell_line" in models and not (sources & line_sources):
        errors.append(
            "experimental_model 'cell_line' requires a cell_source of "
            f"{sorted(line_sources)}, not {sorted(sources)}"
        )
    if sources & line_sources and not models & {"cell_line", "in_vitro_biochemical"}:
        errors.append(
            f"cell_source {sorted(sources & line_sources)} requires "
            "experimental_model 'cell_line' (or 'in_vitro_biochemical')"
        )

    if relevance == "direct":
        ineligible = models - set(DIRECT_ELIGIBLE_MODELS)
        if ineligible:
            errors.append(
                f"relevance 'direct' requires a donor-derived system "
                f"{list(DIRECT_ELIGIBLE_MODELS)}, but experimental_model names "
                f"{sorted(ineligible)}"
            )
        elif "donor_derived_primary" not in sources and "in_vivo" not in models:
            errors.append(
                "relevance 'direct' requires donor-derived primary material or an "
                f"in-vivo system, but cell_source is {sorted(sources)}"
            )
    return errors


def independence_errors(rows: Sequence[Mapping[str, str]]) -> list[str]:
    """One publication is one study for replication counting.

    Several experiments from one paper are separate rows, but they are not
    independent replications of each other. The edge-level rule promotes a
    ``medium`` edge only on two independent groups, so letting two rows of the
    same reference carry different groups would let one paper promote an edge
    by itself. Two *different* references may share a group (one cohort
    reported twice); that direction is allowed and is the point of the column.
    """
    groups: dict[str, set[str]] = {}
    for row in rows:
        # One in-house observation is one study for the same reason one paper
        # is: several rows may describe it, but they are not replications of
        # each other. Every id a row carries is counted, not the first of them:
        # `reference_id or source_observation_id` silently stopped checking the
        # observation as soon as a reference was present. A valid row carries
        # exactly one id, so that was unreachable through the table -- but this
        # function is called directly, and the invariant should not depend on a
        # rule enforced elsewhere.
        group = row.get("independence_group", "").strip()
        if not group:
            continue
        for column in ("reference_id", "source_observation_id"):
            source = row.get(column, "").strip()
            if source:
                groups.setdefault(source, set()).add(group)
    return [
        f"source {source} carries {len(found)} independence groups "
        f"({sorted(found)}); one publication or observation is one study"
        for source, found in sorted(groups.items())
        if len(found) > 1
    ]


def retracted_pairs(
    model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> set[tuple[str, str]]:
    root = root or repo_root()
    edge_rows = read_tsv(model_dir(model_version, root) / "edge_evidence.tsv")
    references = [row["ref_id"] for row in read_tsv(root / REFERENCES_PATH)]
    adjudications = load_with_addenda(
        root / CITATION_ADJUDICATIONS_PATH,
        [root / path for path in POST_CLOSURE_ADJUDICATION_PATHS],
        [row["edge_id"] for row in edge_rows],
        references,
    )
    retracted, _ = partition(adjudications)
    return retracted


def seed_row(seed: Seed) -> dict[str, str]:
    """A visibly unexamined paper-level row. Every assessment is ``unassessed``."""
    row = dict.fromkeys(COLUMNS, "")
    row.update(
        {
            "edge_id": seed.edge_id,
            "evidence_piece_id": piece_id(seed.edge_id, seed.source_id, 1),
            "reference_id": seed.reference_id,
            "source_observation_id": seed.source_observation_id,
            "source_verification": "not_examined",
            "independence_group": seed.source_id,
            "migrated_from": seed.migrated_from,
            "experimental_model": "not_examined",
            "cell_source": "not_examined",
            "experiment_type": "not_examined",
            "perturbation_target": "",
            "perturbation_direction": "not_examined",
            "response_direction": "not_examined",
            "readout_quantitation": "not_examined",
            "rescue_experiment": "not_examined",
            "experimental_strength": "unassessed",
            "human_ADOC_relevance": "unassessed",
            "edge_support": "unassessed",
            "overall_confidence": "unassessed",
            "curation_status": "unreviewed",
        }
    )
    return row


# --------------------------------------------------------------------------
# Build: merge seeds into the curated table, refresh generated columns
# --------------------------------------------------------------------------


def _publication_fields(
    row: Mapping[str, str],
    references: Mapping[str, Mapping[str, str]],
    register: Mapping[str, Mapping[str, str]],
) -> tuple[str, str]:
    reference = references.get(row.get("reference_id", ""))
    if reference is not None:
        return (
            f"{reference['first_author']} {reference['year']}".strip(),
            reference.get("doi", ""),
        )
    observation = register.get(row.get("source_observation_id", ""))
    if observation is not None:
        return (
            f"ADOC in-house ({observation['evidence_id']}; {observation['location']})",
            "",
        )
    return "", ""


def load_table(
    root: Path | None = None, path: Path | None = None
) -> list[dict[str, str]]:
    root = root or repo_root()
    target = path or root / EVIDENCE_TABLE_PATH
    if not target.exists():
        return []
    rows = read_tsv(target)
    if rows and set(rows[0]) != set(COLUMNS):
        raise EvidenceTableError(
            f"{target} columns differ from the schema: missing "
            f"{sorted(set(COLUMNS) - set(rows[0]))}, unexpected {sorted(set(rows[0]) - set(COLUMNS))}"
        )
    return rows


def _natural_edge_key(edge_id: str) -> tuple:
    match = re.match(r"^([A-Z]+)-?(\d+)([A-Z]?)$", edge_id)
    if not match:
        return (edge_id, 0, "")
    prefix, number, suffix = match.groups()
    return (0 if prefix == "LE" else 1, prefix, int(number), suffix)


def _support_order(row: Mapping[str, str]) -> int:
    return {
        "direct": 0,
        "partial": 0,
        "contradictory": 1,
        "not_demonstrated": 2,
        "unassessed": 3,
    }.get(row.get("edge_support", ""), 4)


def sort_key(row: Mapping[str, str]) -> tuple:
    """Edge, supporting before contradictory, strongest first, then publication."""
    return (
        _natural_edge_key(row["edge_id"]),
        _support_order(row),
        -CONFIDENCE_RANK.get(row.get("overall_confidence", ""), -1),
        -STRENGTH_RANK.get(row.get("experimental_strength", ""), -1),
        row.get("reference_id") or row.get("source_observation_id", ""),
        row["evidence_piece_id"],
    )


@dataclass(frozen=True)
class Derivation:
    """Everything the generated columns are computed from."""

    model_version: str
    contexts: Mapping[str, EdgeContext]
    roles: Mapping[str, Mapping[str, str]]
    references: Mapping[str, Mapping[str, str]]
    register: Mapping[str, Mapping[str, str]]

    @classmethod
    def load(cls, model_version: str, root: Path) -> Derivation:
        return cls(
            model_version=model_version,
            contexts=edge_context(model_version, root),
            roles=load_roles(root),
            references={row["ref_id"]: row for row in read_tsv(root / REFERENCES_PATH)},
            register={
                row["evidence_id"]: row
                for row in read_tsv(root / EVIDENCE_REGISTER_PATH)
            },
        )

    def generated(self, row: Mapping[str, str]) -> dict[str, str]:
        """The value of every ``GENERATED_COLUMNS`` cell for ``row``."""
        context = self.contexts[row["edge_id"]]
        role = self.roles.get(row["edge_id"], {}).get("edge_role", "")
        publication, doi = _publication_fields(row, self.references, self.register)
        return {
            "edge_id": row["edge_id"],
            "source": context.source,
            "target": context.target,
            "sign": context.sign,
            "boolean_rule": context.boolean_rule,
            "compartment": context.compartment,
            "edge_status": context.edge_status,
            "edge_role": role if context.edge_status == "active" else "",
            "model_version": self.model_version,
            "publication": publication,
            "doi": doi,
        }


def build_table(
    existing: Sequence[Mapping[str, str]],
    *,
    model_version: str = DEFAULT_MODEL_VERSION,
    root: Path | None = None,
) -> list[dict[str, str]]:
    """Merge-regenerate the canonical table. Pure: writes nothing."""
    root = root or repo_root()
    derivation = Derivation.load(model_version, root)
    contexts = derivation.contexts

    rows = [dict(row) for row in existing]
    # Restoration is keyed on the seed's own id, not on (edge, source). Keying
    # it on the pair let a curator's second row for the same paper
    # (``...-02``) stand in for the migrated seed (``...-01``), so the seed was
    # never restored and its lineage was lost from the table.
    present = {row.get("evidence_piece_id", "") for row in rows}
    for seed in migration_seeds(model_version, root):
        if seed.piece_id not in present:
            rows.append(seed_row(seed))
            present.add(seed.piece_id)

    unknown = sorted({row["edge_id"] for row in rows} - set(contexts))
    if unknown:
        raise EvidenceTableError(
            f"evidence rows name edges that {model_version} neither computes nor "
            f"retires: {unknown}. They are kept, not dropped; fix the edge id."
        )

    for row in rows:
        row.update(derivation.generated(row))
        for column in COLUMNS:
            row.setdefault(column, "")
    rows.sort(key=sort_key)
    return rows


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def confidence_ceiling(strength: str, relevance: str, support: str) -> str:
    """The highest per-piece ``overall_confidence`` the three axes allow."""
    if support not in ("direct", "partial") or strength in (
        "insufficient",
        "unassessed",
    ):
        return "unsupported"
    if strength == "strong" and relevance == "direct" and support == "direct":
        return "high"
    if strength in ("strong", "moderate") and relevance in (
        "direct",
        "close",
        "indirect",
    ):
        return "medium"
    return "low"


def contradiction_weight(strength: str, relevance: str) -> str:
    """What a contradicting piece would weigh had it supported the edge."""
    return confidence_ceiling(strength, relevance, "direct")


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _tokens(value: str) -> list[str]:
    return [token.strip() for token in value.split(";") if token.strip()]


def parse_species(value: str) -> tuple[set[str], list[str]]:
    """Organisms named by a ``species`` cell, and any malformed entries."""
    organisms: set[str] = set()
    errors: list[str] = []
    for entry in _tokens(value):
        match = _SPECIES_ENTRY.match(entry)
        if match is None or match["organism"] not in ORGANISM_VALUES:
            errors.append(
                f"species entry {entry!r} is not '<organism>' or '<compartment>: <organism>' "
                f"with organism in {list(ORGANISM_VALUES)}"
            )
            continue
        organisms.add(match["organism"])
    return organisms, errors


def validate_rows(
    rows: Sequence[Mapping[str, str]],
    *,
    model_version: str = DEFAULT_MODEL_VERSION,
    root: Path | None = None,
) -> ValidationReport:
    root = root or repo_root()
    report = ValidationReport()
    errors = report.errors
    derivation = Derivation.load(model_version, root)
    contexts = derivation.contexts
    roles = derivation.roles
    errors.extend(validate_roles(roles, contexts))
    references = set(derivation.references)
    observations = set(derivation.register)
    retracted = retracted_pairs(model_version, root)
    curated_edges = {
        row["edge_id"]
        for row in read_tsv(model_dir(model_version, root) / "edge_evidence.tsv")
    }
    entities = node_entities(model_version, root)
    errors.extend(lineage_errors(rows, migration_seeds(model_version, root)))
    errors.extend(independence_errors(rows))

    if [row.get("evidence_piece_id") for row in rows] != [
        row.get("evidence_piece_id") for row in sorted(rows, key=sort_key)
    ]:
        errors.append(
            "rows are not in canonical order (edge, support, strength, publication)"
        )

    seen: dict[str, int] = {}
    for row in rows:
        pid = row.get("evidence_piece_id", "")
        where = pid or f"row for {row.get('edge_id')}"
        seen[pid] = seen.get(pid, 0) + 1
        if row.get("edge_id") in contexts:
            # Generated cells must equal their derivation, so a stale or
            # hand-edited model or bibliography column cannot pass.
            for column, expected in derivation.generated(row).items():
                if row.get(column, "") != expected:
                    errors.append(
                        f"{where}: generated column {column}={row.get(column, '')!r} "
                        f"differs from its derivation {expected!r}; rebuild the table"
                    )
        match = _EVIDENCE_PIECE_ID.match(pid)
        source_id = row.get("reference_id") or row.get("source_observation_id", "")
        if not match:
            errors.append(f"{where}: evidence_piece_id is not EVP-<edge>-<source>-<nn>")
        elif match["edge"] != row["edge_id"] or match["src"] != compact(source_id):
            errors.append(
                f"{where}: id does not encode its edge {row['edge_id']} and source {source_id}"
            )

        if row["edge_id"] not in contexts:
            errors.append(f"{where}: unknown edge {row['edge_id']}")
        if bool(row.get("reference_id")) == bool(row.get("source_observation_id")):
            errors.append(
                f"{where}: exactly one of reference_id and source_observation_id is required"
            )
        if row.get("reference_id") and row["reference_id"] not in references:
            errors.append(
                f"{where}: reference {row['reference_id']} is not in references.tsv"
            )
        if (
            row.get("source_observation_id")
            and row["source_observation_id"] not in observations
        ):
            errors.append(
                f"{where}: observation {row['source_observation_id']} is not in the evidence register"
            )
        if not row.get("independence_group", "").strip():
            errors.append(f"{where}: independence_group is empty")

        for column, allowed in SINGLE_VALUED.items():
            value = row.get(column, "")
            if column == "edge_role" and row.get("edge_status") == "retired":
                continue
            if value not in allowed:
                errors.append(f"{where}: {column}={value!r} not in {list(allowed)}")
        for column, allowed in MULTI_VALUED.items():
            tokens = _tokens(row.get(column, ""))
            if not tokens or any(token not in allowed for token in tokens):
                errors.append(
                    f"{where}: {column}={row.get(column)!r} has values outside {list(allowed)}"
                )

        status = row.get("curation_status", "")
        assessment = [row.get(column, "") for column in ASSESSMENT_COLUMNS]
        if status == "unreviewed":
            if any(value != "unassessed" for value in assessment):
                errors.append(
                    f"{where}: unreviewed rows must leave every assessment 'unassessed'"
                )
            if row.get("source_verification") not in ("not_examined", "unavailable"):
                errors.append(
                    f"{where}: unreviewed rows are 'not_examined' or 'unavailable'"
                )
            continue

        # Examined rows.
        if any(value == "unassessed" for value in assessment):
            errors.append(
                f"{where}: examined ({status}) but an assessment axis is 'unassessed'"
            )
        # Provenance and the two rationales carry the whole traceability claim,
        # so a null wearing a word ('none', 'N/A', 'not_reported') is as bad as
        # a blank: it reads as filled in and says nothing.
        for column in (
            "confidence_rationale",
            "limitations_rationale",
            "source_location",
            "curated_on",
        ):
            value = row.get(column, "")
            if not value.strip():
                errors.append(f"{where}: examined row has empty {column}")
            elif _asserts_nothing(value):
                errors.append(
                    f"{where}: {column}={value!r} asserts nothing; an examined row "
                    "states where the result is and why the grade is what it is"
                )
        if row.get("source_verification") in ("not_examined", "unavailable"):
            errors.append(
                f"{where}: examined row cannot have source_verification={row.get('source_verification')!r}"
            )
        if (
            status == "verified"
            and row.get("source_verification") != "full_text_verified"
        ):
            errors.append(
                f"{where}: 'verified' requires source_verification=full_text_verified"
            )
        for column in (
            "experimental_model",
            "cell_source",
            "experiment_type",
            "rescue_experiment",
        ):
            if "not_examined" in _tokens(row.get(column, "")):
                errors.append(f"{where}: examined row still has {column}=not_examined")
        # Missingness is written, never left blank: an empty cell is
        # indistinguishable from "nobody filled it in", and these are the cells
        # the grade is supposed to rest on. `not_reported` says the source was
        # read and does not state it.
        for column in DESCRIPTIVE_COLUMNS:
            if not row.get(column, "").strip():
                errors.append(
                    f"{where}: examined row leaves {column} blank; write what the "
                    "source states, or 'not_reported'"
                )

        strength, relevance, support, overall = assessment
        # Prerequisites the rubric states for the two strongest axis values.
        perturbations = set(_tokens(row.get("experiment_type", ""))) & set(
            PERTURBATION_EXPERIMENT_TYPES
        )
        replicates = row.get("biological_replicates", "").strip()
        if replicates and replicates != "not_reported" and not replicates.isdigit():
            errors.append(
                f"{where}: biological_replicates={replicates!r} is neither a count nor "
                "'not_reported'"
            )
        # `strong` means the regulator itself was perturbed, whatever the
        # support grade: a strong experiment on something else is not strong
        # evidence *here*, and `partial` used to let it through.
        if support == "direct" or strength == "strong":
            claim = "edge_support='direct'" if support == "direct" else "'strong'"
            if not perturbations:
                errors.append(
                    f"{where}: {claim} requires the regulator itself to "
                    f"be perturbed, but experiment_type={row.get('experiment_type')!r} "
                    "names no perturbation"
                )
            if row["edge_id"] in contexts:
                errors.extend(
                    f"{where}: {message}"
                    for message in perturbation_target_errors(
                        row,
                        context=contexts[row["edge_id"]],
                        entities=entities,
                        role=roles.get(row["edge_id"], {}).get("edge_role", ""),
                    )
                )
        if row["edge_id"] in contexts:
            errors.extend(
                f"{where}: {message}"
                for message in direction_errors(
                    row, sign=contexts[row["edge_id"]].sign, support=support
                )
            )
        errors.extend(
            f"{where}: {message}"
            for message in system_coherence_errors(row, relevance=relevance)
        )
        # Association without perturbation is `weak` in the rubric; a row whose
        # every experiment type only observes cannot climb above it.
        types = set(_tokens(row.get("experiment_type", "")))
        if (
            types
            and types <= set(ASSOCIATION_ONLY_EXPERIMENT_TYPES)
            and strength in ("strong", "moderate")
        ):
            errors.append(
                f"{where}: experiment_type {sorted(types)} only observes, so "
                f"experimental_strength cannot be {strength!r}; association is 'weak'"
            )
        # A perturbational row must state both directions concretely. Excusing
        # only `not_examined` left `not_applicable` as a way out of the sign
        # check entirely, because direction_errors treats both as "nothing
        # recorded": a knockdown that supports an edge is never a case where
        # direction does not apply.
        #
        # `not_demonstrated` is the exception, and the only one. It records that
        # the source does not test this relation, which is usually because the
        # encoded target was never measured -- a paper that perturbs LIF and
        # never assays GP130 or phospho-STAT3, or that silences PC5/6 and never
        # assays dystroglycan. Demanding a concrete response there asks the
        # curator to invent a measurement that does not exist. Nothing is
        # weakened by the exemption: `not_demonstrated` forces
        # `overall_confidence='unsupported'` a few lines below, so no grade can
        # be reached through it, and the sign check it guards
        # (`direction_errors`) only ever fires on direct, partial or
        # contradictory support. `contradictory` -- the case where direction
        # carries the whole claim -- is deliberately still required to state it.
        if perturbations and support != "not_demonstrated":
            for column, concrete in (
                ("perturbation_direction", DIRECTIONS_PERTURBED),
                ("response_direction", DIRECTIONS_OBSERVED),
            ):
                if row.get(column) not in concrete:
                    errors.append(
                        f"{where}: a perturbation is recorded, so {column} must be "
                        f"one of {list(concrete)}, not {row.get(column)!r}"
                    )
        if strength == "strong":
            if row.get("rescue_experiment") not in SPECIFICITY_ROUTES:
                errors.append(
                    f"{where}: experimental_strength='strong' requires one of the "
                    f"specificity routes {list(SPECIFICITY_ROUTES)}, but "
                    f"rescue_experiment={row.get('rescue_experiment')!r}"
                )
            if _asserts_nothing(row.get("controls", "")):
                errors.append(
                    f"{where}: experimental_strength='strong' requires reported "
                    f"controls, but controls={row.get('controls')!r} asserts none"
                )
            if row.get("readout_quantitation") not in (
                "quantitative",
                "semi_quantitative",
            ):
                errors.append(
                    f"{where}: experimental_strength='strong' requires a quantitative "
                    f"readout, but readout_quantitation="
                    f"{row.get('readout_quantitation')!r}"
                )
            if not replicates.isdigit() or int(replicates) < 2:
                errors.append(
                    f"{where}: experimental_strength='strong' requires reported "
                    f"biological replication (two or more), but "
                    f"biological_replicates={replicates!r}"
                )
            if not perturbations:
                errors.append(
                    f"{where}: experimental_strength='strong' requires a perturbation "
                    f"of the regulator, but experiment_type={row.get('experiment_type')!r} "
                    "names none"
                )
        ceiling = confidence_ceiling(strength, relevance, support)
        if CONFIDENCE_RANK.get(overall, -1) > CONFIDENCE_RANK[ceiling]:
            errors.append(
                f"{where}: overall_confidence {overall!r} exceeds the ceiling {ceiling!r} of "
                f"strength={strength}, relevance={relevance}, support={support}"
            )
        if (
            support in ("contradictory", "not_demonstrated")
            and overall != "unsupported"
        ):
            errors.append(
                f"{where}: edge_support={support} requires overall_confidence=unsupported"
            )
        if row.get("source_verification") in (
            "abstract_only",
            "secondary_summary",
            "full_text_partial",
        ):
            if CONFIDENCE_RANK.get(overall, -1) > CONFIDENCE_RANK["low"]:
                errors.append(
                    f"{where}: graded from {row['source_verification']}; capped at 'low'"
                )
            if status == "verified":
                errors.append(
                    f"{where}: cannot be 'verified' from {row['source_verification']}"
                )

        organisms, species_errors = parse_species(row.get("species", ""))
        errors.extend(f"{where}: {message}" for message in species_errors)
        if not organisms:
            errors.append(f"{where}: examined row has empty species")
        elif relevance == "direct" and organisms != {"human"}:
            errors.append(
                f"{where}: relevance 'direct' requires every compartment to be human, "
                f"species is {row.get('species')!r}"
            )
        elif relevance == "close" and "human" not in organisms:
            errors.append(
                f"{where}: relevance 'close' requires a human compartment, species is {row.get('species')!r}"
            )
        sources = _tokens(row.get("cell_source", ""))
        if "cancer_derived" in sources and relevance in ("direct", "close"):
            errors.append(
                f"{where}: cancer-derived cells cannot have relevance {relevance!r}"
            )
        if "immortalized_primary_like" in sources and relevance == "direct":
            errors.append(f"{where}: immortalized cells cannot have relevance 'direct'")

        source_id = row.get("reference_id", "")
        # A retraction says the paper bears on this relation neither way: the
        # recorded bases are that the node is absent from the full text, or
        # that the study is out of scope. Allowing `contradictory` here let a
        # source adjudicated irrelevant mark the edge contradicted, which the
        # edge-level rule weighs as heavily as support. `not_demonstrated` is
        # exactly what a retraction means and stays available.
        if (row["edge_id"], source_id) in retracted and support in (
            "direct",
            "partial",
            "contradictory",
        ):
            errors.append(
                f"{where}: {source_id} is retracted from {row['edge_id']} in "
                f"config/edge_citation_adjudications.tsv, so it cannot bear on the "
                f"relation as {support!r}; only 'not_demonstrated' is available"
            )

    for pid, count in seen.items():
        if count > 1:
            errors.append(f"evidence_piece_id {pid} appears {count} times")
    missing_history = sorted(curated_edges - {row["edge_id"] for row in rows})
    if missing_history:
        errors.append(
            f"curated edges with no evidence row (history lost?): {missing_history}"
        )
    report.summary = summarize_rows(rows, contexts)
    return report


def summarize_rows(
    rows: Iterable[Mapping[str, str]], contexts: Mapping[str, EdgeContext]
) -> dict[str, object]:
    rows = list(rows)
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row["curation_status"]] = by_status.get(row["curation_status"], 0) + 1
    active = {context.edge_id for context in active_edges(contexts)}
    examined = [row for row in rows if row["curation_status"] != "unreviewed"]
    return {
        "row_count": len(rows),
        "rows_by_curation_status": dict(sorted(by_status.items())),
        "active_edge_count": len(active),
        "retired_edge_count": sum(
            1 for c in contexts.values() if c.edge_status == "retired"
        ),
        "active_edges_with_rows": len(active & {row["edge_id"] for row in rows}),
        "active_edges_with_examined_rows": len(
            active & {row["edge_id"] for row in examined}
        ),
        "publications_examined": len(
            {row["reference_id"] for row in examined if row["reference_id"]}
        ),
        "publications_cited": len(
            {row["reference_id"] for row in rows if row["reference_id"]}
        ),
    }


def build_and_write(
    *, model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> tuple[list[dict[str, str]], ValidationReport]:
    """Regenerate, validate, and write only if validation passes."""
    root = root or repo_root()
    rows = build_table(load_table(root), model_version=model_version, root=root)
    report = validate_rows(rows, model_version=model_version, root=root)
    if report.ok:
        write_tsv_lf(root / EVIDENCE_TABLE_PATH, rows, COLUMNS)
    return rows, report


def check(
    *, model_version: str = DEFAULT_MODEL_VERSION, root: Path | None = None
) -> list[str]:
    """Errors if the committed table is invalid or is not what a rebuild writes.

    Writes nothing. A rebuild merges curated cells, so a difference means a
    seed is missing, a generated column is stale, or the order is not canonical.
    """
    root = root or repo_root()
    path = root / EVIDENCE_TABLE_PATH
    if not path.exists():
        return [f"{path} does not exist; run `pixi run build-edge-evidence`"]
    committed = load_table(root)
    errors = list(
        validate_rows(committed, model_version=model_version, root=root).errors
    )
    rebuilt = render_tsv(
        build_table(committed, model_version=model_version, root=root), COLUMNS
    )
    if path.read_text(encoding="utf-8") != rebuilt:
        errors.append(f"{path} is not current; run `pixi run build-edge-evidence`")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        prog="python -m dt_adoc.evidence.experimental",
        description="Regenerate (merge) or check the canonical per-experiment evidence table.",
    )
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--model-version", default=DEFAULT_MODEL_VERSION)
    args = parser.parse_args(argv)
    if args.command == "build":
        _, report = build_and_write(model_version=args.model_version)
        print(
            json.dumps(
                {
                    "written": report.ok,
                    "errors": report.errors,
                    "summary": report.summary,
                },
                indent=2,
            )
        )
        return 0 if report.ok else 1
    errors = check(model_version=args.model_version)
    print(json.dumps({"current": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
