"""Model-versioned runtime registry for DT_ADOC."""

from __future__ import annotations

import copy
import functools
from dataclasses import dataclass
from pathlib import Path

import tomllib

from dt_adoc.model.provenance import repo_root
from dt_adoc.model.superset_family import (
    MODEL_KEY as SUPERSET_MODEL_ID,
)
from dt_adoc.model.superset_family import (
    MODEL_VERSION as SUPERSET_VERSION,
)


@dataclass(frozen=True)
class MemoryPolicySpec:
    policy_id: str
    node_ids: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class RuleVariantSpec:
    variant_id: str
    node_logic_overrides: dict[str, str]
    notes: str


@dataclass(frozen=True)
class ModelRuntimeSpec:
    model_version: str
    model_id: str
    model_root: Path
    network_bnd: Path
    baseline_cfg: Path
    condition_dir: Path
    node_dictionary: Path
    edge_evidence: Path
    phenotype_contract: Path
    provenance: Path
    output_root: Path
    default_smoke_protocols: tuple[str, ...]
    default_memory_policy: str
    memory_policies: dict[str, MemoryPolicySpec]
    rule_variants: dict[str, dict[str, RuleVariantSpec]]
    default_rule_variants: dict[str, str]


@functools.lru_cache(maxsize=256)
def _parsed_toml(text: str) -> dict[str, object]:
    """The parse of ``text``, keyed by the text itself.

    Never by path or modification time: the caller reads the file every time
    and passes what it read, so an edited file is a new key however fast it
    was edited, and a restored one finds its old parse. A parse error is not
    cached, so it is raised again on every call, as before.
    """
    return tomllib.loads(text)


def _provenance_payload(path: Path) -> dict[str, object]:
    # A deep copy, so a caller that mutates its payload cannot change another's.
    return copy.deepcopy(_parsed_toml(path.read_text(encoding="utf-8")))


def _baseline_model(root: Path) -> ModelRuntimeSpec:
    model_root = root / "models" / "baseline" / "adoc-core-v0.1.0"
    provenance = model_root / "provenance.toml"
    payload = _provenance_payload(provenance)
    model_version = str(payload.get("baseline_version", payload.get("model_version")))
    return ModelRuntimeSpec(
        model_version=model_version,
        model_id=str(payload.get("model_id", payload.get("family_id", "adoc_core"))),
        model_root=model_root,
        network_bnd=model_root / "network.bnd",
        baseline_cfg=model_root / "baseline.cfg",
        condition_dir=model_root / "conditions",
        node_dictionary=model_root / "node_dictionary.tsv",
        edge_evidence=model_root / "edge_evidence.tsv",
        phenotype_contract=model_root / "phenotype_contract.tsv",
        provenance=provenance,
        output_root=root / "output" / "smoke",
        default_smoke_protocols=(
            "basal",
            "e2_priming",
            "hormone_treated",
            "hormone_treated_mifepristone",
            "hormone_treated_anti_spp1",
            "washout",
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_washout",
        ),
        default_memory_policy="all_non_inputs",
        memory_policies={},
        rule_variants={},
        default_rule_variants={},
    )


def _literature_model(root: Path) -> ModelRuntimeSpec:
    model_root = root / "models" / "extended" / "adoc-literature-v0.2.0"
    provenance = model_root / "provenance.toml"
    payload = _provenance_payload(provenance)
    model_version = str(payload.get("baseline_version", payload.get("model_version")))
    return ModelRuntimeSpec(
        model_version=model_version,
        model_id=str(
            payload.get("model_id", payload.get("family_id", "adoc_literature"))
        ),
        model_root=model_root,
        network_bnd=model_root / "network.bnd",
        baseline_cfg=model_root / "baseline.cfg",
        condition_dir=model_root / "conditions",
        node_dictionary=model_root / "node_dictionary.tsv",
        edge_evidence=model_root / "edge_evidence.tsv",
        phenotype_contract=model_root / "phenotype_contract.tsv",
        provenance=provenance,
        output_root=root / "output" / "smoke" / model_version,
        default_smoke_protocols=(
            "basal_maternal",
            "e2_primed_maternal",
            "hormone_treated_maternal",
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_excess_er_stress",
            "adhesion_challenge_high_ecm_stiffness",
            "adhesion_challenge_washout",
        ),
        default_memory_policy="minimal_stable_joint",
        memory_policies={
            "minimal_stable_joint": MemoryPolicySpec(
                policy_id="minimal_stable_joint",
                node_ids=(
                    "E_SECRETORY_STATE",
                    "E_IHH",
                    "E_LIF",
                    "E_GP130_STAT3",
                    "E_RECEPTIVE_SURFACE",
                    "S_NR2F2",
                    "S_BMP2",
                    "S_DECIDUALIZED",
                    "S_TAZ_ECM",
                    "X_INTERFACE_SPP1_RELAY",
                    "X_INTERFACE_REDUNDANT_RELAY",
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                    "X_MECHANICAL_STRESS_RELAY",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Comparator memory excludes outputs, direct readouts, route-derived nodes, fixed placeholders, and embryo inputs.",
            ),
            "extended_maternal_joint": MemoryPolicySpec(
                policy_id="extended_maternal_joint",
                node_ids=(
                    "E_PGR",
                    "E_IHH",
                    "E_SECRETORY_STATE",
                    "E_LIF",
                    "E_GP130_STAT3",
                    "E_PODXL",
                    "E_PC6",
                    "E_DAG1_FULL",
                    "E_DAG1_CLEAVED",
                    "E_MUC1_BARRIER",
                    "E_MUC1_SLEX",
                    "E_HBEGF",
                    "E_SPP1_EXPR",
                    "E_ITGAVB3_5",
                    "E_CD98_CD9",
                    "E_ANXA2_ACTIN",
                    "E_CDH1_APICAL",
                    "E_RECEPTIVE_SURFACE",
                    "S_PGR",
                    "S_PKA",
                    "S_NR2F2",
                    "S_BMP2",
                    "S_HAND2",
                    "S_DECIDUALIZED",
                    "S_SPP1",
                    "S_TAZ_ECM",
                    "X_SPP1_LUMEN_FREE",
                    "X_INTERFACE_SPP1_RELAY",
                    "X_INTERFACE_REDUNDANT_RELAY",
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                    "X_MECHANICAL_STRESS_RELAY",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Extended maternal memory keeps upstream maternal mechanism states but excludes outputs, direct readouts, and derived route nodes.",
            ),
            "marginal_comparator": MemoryPolicySpec(
                policy_id="marginal_comparator",
                node_ids=(
                    "E_SECRETORY_STATE",
                    "E_LIF",
                    "E_GP130_STAT3",
                    "E_RECEPTIVE_SURFACE",
                    "S_DECIDUALIZED",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Named comparator for independent node-marginal continuation.",
            ),
        },
        rule_variants={
            "cdh1": {
                "embryo_contact_induced": RuleVariantSpec(
                    variant_id="embryo_contact_induced",
                    node_logic_overrides={"E_CDH1_APICAL": "IN_EMBRYO_CONTACT"},
                    notes="Current bounded comparator: explicit contact gate only.",
                ),
                "maternal_receptive_state_dependent": RuleVariantSpec(
                    variant_id="maternal_receptive_state_dependent",
                    node_logic_overrides={
                        "E_CDH1_APICAL": "E_SECRETORY_STATE and (IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL)"
                    },
                    notes="Provisional uncertainty variant combining maternal secretory priming with external embryo cues.",
                ),
                "maternal_priming_with_contact_reinforcement": RuleVariantSpec(
                    variant_id="maternal_priming_with_contact_reinforcement",
                    node_logic_overrides={
                        "E_CDH1_APICAL": "(E_SECRETORY_STATE and (IN_HCG or IN_EMBRYO_CONDITIONED_SIGNAL)) or IN_EMBRYO_CONTACT"
                    },
                    notes="Provisional uncertainty variant adding explicit contact reinforcement without a self-loop.",
                ),
            },
            "mifepristone": {
                "pgr_only_inhibition": RuleVariantSpec(
                    variant_id="pgr_only_inhibition",
                    node_logic_overrides={},
                    notes="Default comparator: inhibition propagates through E_PGR and S_PGR only.",
                ),
                "pgr_plus_direct_interface_inhibition": RuleVariantSpec(
                    variant_id="pgr_plus_direct_interface_inhibition",
                    node_logic_overrides={
                        "X_INTERFACE_REDUNDANT_RELAY": "X_INTERFACE_REDUNDANT_RELAY and not IN_MIFEPRISTONE"
                    },
                    notes="Alternative uncertainty variant with added direct interface suppression.",
                ),
            },
            "xav939": {
                "permissive": RuleVariantSpec(
                    variant_id="permissive",
                    node_logic_overrides={"E_SECRETORY_STATE": "IN_E2 and E_PGR"},
                    notes="Default comparator does not require XAV939 to enter the compact secretory state.",
                ),
                "required": RuleVariantSpec(
                    variant_id="required",
                    node_logic_overrides={
                        "E_SECRETORY_STATE": "IN_E2 and E_PGR and IN_XAV939"
                    },
                    notes="Stricter alternate rule requires XAV939 in the epithelial secretory gate.",
                ),
            },
            "ihh": {
                "compact_current_bridge": RuleVariantSpec(
                    variant_id="compact_current_bridge",
                    node_logic_overrides={},
                    notes="Default comparator keeps the compact IHH to NR2F2 to BMP2 bridge.",
                ),
                "strict_nr2f2_bmp2_hand2": RuleVariantSpec(
                    variant_id="strict_nr2f2_bmp2_hand2",
                    node_logic_overrides={
                        "S_HAND2": "S_BMP2",
                        "S_DECIDUALIZED": "S_PGR and S_PKA and S_HAND2",
                    },
                    notes="Stricter relay variant makes HAND2 functionally required downstream of BMP2.",
                ),
            },
            "mechanics": {
                "shared_stress_relay": RuleVariantSpec(
                    variant_id="shared_stress_relay",
                    node_logic_overrides={
                        "X_MECHANICAL_STRESS_RELAY": "X_MECHANICAL_STRESS_RELAY",
                        "X_MECHANICAL_PERMISSIVE_ECM": "S_DECIDUALIZED and S_TAZ_ECM and not ((IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS) and X_MECHANICAL_STRESS_RELAY)",
                    },
                    notes="Default bounded comparator uses one shared uncertainty relay for both adverse inputs.",
                ),
                "separate_input_common_downstream": RuleVariantSpec(
                    variant_id="separate_input_common_downstream",
                    node_logic_overrides={
                        "X_MECHANICAL_STRESS_RELAY": "IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS",
                        "X_MECHANICAL_PERMISSIVE_ECM": "S_DECIDUALIZED and S_TAZ_ECM and not X_MECHANICAL_STRESS_RELAY",
                    },
                    notes="Alternate comparator keeps one downstream relay but resolves the adverse inputs explicitly at the relay node.",
                ),
            },
        },
        default_rule_variants={
            "cdh1": "embryo_contact_induced",
            "mifepristone": "pgr_only_inhibition",
            "xav939": "permissive",
            "ihh": "compact_current_bridge",
            "mechanics": "shared_stress_relay",
        },
    )


def _superset_model(root: Path, version: str = SUPERSET_VERSION) -> ModelRuntimeSpec:
    """Build a runtime spec for any superset version on disk.

    The generator emits exactly one version, but earlier supersets stay on disk
    as immutable parents and must remain resolvable -- committed figures and
    their sidecars name them.
    """
    model_root = root / "models" / "superset" / version
    provenance = model_root / "provenance.toml"
    payload = _provenance_payload(provenance)
    return ModelRuntimeSpec(
        model_version=version,
        model_id=str(
            payload.get("model_id", payload.get("family_id", SUPERSET_MODEL_ID))
        ),
        model_root=model_root,
        network_bnd=model_root / "network.bnd",
        baseline_cfg=model_root / "baseline.cfg",
        condition_dir=model_root / "conditions",
        node_dictionary=model_root / "node_dictionary.tsv",
        edge_evidence=model_root / "edge_evidence.tsv",
        phenotype_contract=model_root / "phenotype_contract.tsv",
        provenance=provenance,
        output_root=root / "output" / "smoke" / version,
        default_smoke_protocols=(
            "basal_maternal",
            "e2_primed_maternal",
            "hormone_treated_maternal",
            "adhesion_challenge_basal",
            "adhesion_challenge_hormone_treated",
            "adhesion_challenge_hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_anti_spp1",
            "adhesion_challenge_excess_er_stress",
            "adhesion_challenge_high_ecm_stiffness",
            "adhesion_challenge_washout",
        ),
        default_memory_policy="minimal_stable_joint",
        memory_policies={
            "minimal_stable_joint": MemoryPolicySpec(
                policy_id="minimal_stable_joint",
                node_ids=(
                    "E_SECRETORY_STATE",
                    "E_IHH",
                    "E_LIF",
                    "E_GP130_STAT3",
                    "E_RECEPTIVE_SURFACE",
                    "S_NR2F2",
                    "S_BMP2",
                    "S_HAND2",
                    "S_FGF_MITOGENIC",
                    "E_ESTROGENIC_PROLIFERATION",
                    "S_DECIDUALIZED",
                    "S_TAZ_ECM",
                    "X_INTERFACE_SPP1_RELAY",
                    "X_INTERFACE_REDUNDANT_RELAY",
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                    "X_MECHANICAL_STRESS_RELAY",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Phase 1D default memory retains maternal executable states but excludes outputs and deferred nodes.",
            ),
            "extended_maternal_joint": MemoryPolicySpec(
                policy_id="extended_maternal_joint",
                node_ids=(
                    "E_PGR",
                    "E_IHH",
                    "E_SECRETORY_STATE",
                    "E_LIF",
                    "E_KLF12_HIGH",
                    "E_GP130_STAT3",
                    "E_PODXL",
                    "E_PC6",
                    "E_DAG1_FULL",
                    "E_DAG1_CLEAVED",
                    "E_MUC1_BARRIER",
                    "E_MUC1_SLEX",
                    "E_HBEGF",
                    "E_SPP1_EXPR",
                    "E_ITGAVB3_5",
                    "E_CD98_CD9",
                    "E_ANXA2_ACTIN",
                    "E_CDH1_APICAL",
                    "E_ESTROGENIC_PROLIFERATION",
                    "E_RECEPTIVE_SURFACE",
                    "S_PGR",
                    "S_PKA",
                    "S_NR2F2",
                    "S_BMP2",
                    "S_HAND2",
                    "S_FGF_MITOGENIC",
                    "S_DECIDUALIZED",
                    "S_SPP1",
                    "S_TAZ_ECM",
                    "X_SPP1_LUMEN_FREE",
                    "X_INTERFACE_SPP1_RELAY",
                    "X_INTERFACE_REDUNDANT_RELAY",
                    "X_INTERFACE_ANTIADHESIVE_RELAY",
                    "X_MECHANICAL_STRESS_RELAY",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Extended maternal memory includes the Phase 1D proliferation and contextual inputs where executable.",
            ),
            "marginal_comparator": MemoryPolicySpec(
                policy_id="marginal_comparator",
                node_ids=(
                    "E_SECRETORY_STATE",
                    "E_LIF",
                    "E_GP130_STAT3",
                    "E_RECEPTIVE_SURFACE",
                    "S_DECIDUALIZED",
                    "X_MECHANICAL_PERMISSIVE_ECM",
                ),
                notes="Bounded marginal comparator for the Phase 1D superset.",
            ),
        },
        rule_variants={},
        default_rule_variants={},
    )


def available_models(root: Path | None = None) -> dict[str, ModelRuntimeSpec]:
    active_root = root or repo_root()
    models = {
        "adoc-core-v0.1.0": _baseline_model(active_root),
        "adoc-literature-v0.2.0": _literature_model(active_root),
    }
    superset_dir = active_root / "models" / "superset"
    if superset_dir.is_dir():
        for candidate in sorted(superset_dir.iterdir()):
            if (candidate / "provenance.toml").is_file():
                models[candidate.name] = _superset_model(active_root, candidate.name)
    return models


def resolve_model(
    model_version: str | None = None, root: Path | None = None
) -> ModelRuntimeSpec:
    registry = available_models(root)
    selected = model_version or "adoc-core-v0.1.0"
    try:
        spec = registry[selected]
    except KeyError as exc:
        known = ", ".join(sorted(registry))
        raise ValueError(
            f"unknown model_version {selected!r}; expected one of: {known}"
        ) from exc
    validate_model_runtime_spec(spec, root=root)
    return spec


def validate_model_runtime_spec(
    spec: ModelRuntimeSpec,
    *,
    root: Path | None = None,
    expected_model_version: str | None = None,
) -> None:
    active_root = root or repo_root()
    if (
        expected_model_version is not None
        and spec.model_version != expected_model_version
    ):
        raise ValueError(
            f"model runtime metadata/files disagreement: expected {expected_model_version}, got {spec.model_version}"
        )
    payload = _provenance_payload(spec.provenance)
    observed_version = str(
        payload.get("baseline_version", payload.get("model_version", ""))
    )
    if observed_version != spec.model_version:
        raise ValueError(
            f"model runtime metadata/files disagreement: provenance model_version={observed_version!r} but registry selected {spec.model_version!r}"
        )
    for path in (
        spec.model_root,
        spec.network_bnd,
        spec.baseline_cfg,
        spec.condition_dir,
        spec.node_dictionary,
        spec.edge_evidence,
        spec.phenotype_contract,
        spec.provenance,
    ):
        if not path.exists():
            raise ValueError(
                f"model runtime metadata/files disagreement: missing {path.relative_to(active_root)}"
            )
    if (
        spec.model_version != "adoc-core-v0.1.0"
        and spec.node_dictionary.parent != spec.model_root
    ):
        raise ValueError(
            "silent baseline-node-catalog reuse for literature model is not allowed"
        )


def resolve_memory_policy(
    *,
    model_version: str,
    policy_id: str,
    root: Path | None = None,
) -> MemoryPolicySpec:
    spec = resolve_model(model_version, root)
    try:
        return spec.memory_policies[policy_id]
    except KeyError as exc:
        raise ValueError(
            f"unsupported memory-node policy {policy_id!r} for model_version {model_version!r}"
        ) from exc


def resolve_rule_variants(
    *,
    model_version: str,
    variant_selection: dict[str, str] | None = None,
    root: Path | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    spec = resolve_model(model_version, root)
    selected = dict(spec.default_rule_variants)
    if variant_selection:
        selected.update(variant_selection)
    merged: dict[str, str] = {}
    for family, variant_id in selected.items():
        family_variants = spec.rule_variants.get(family)
        if family_variants is None:
            raise ValueError(
                f"unsupported rule-variant family {family!r} for model_version {model_version!r}"
            )
        try:
            variant = family_variants[variant_id]
        except KeyError as exc:
            known = ", ".join(sorted(family_variants))
            raise ValueError(
                f"unsupported rule variant {variant_id!r} for family {family!r}; expected one of: {known}"
            ) from exc
        merged.update(variant.node_logic_overrides)
    return selected, merged


def validate_manifest_model_version(
    manifest: dict[str, object],
    *,
    expected_model_version: str,
) -> None:
    model_payload = manifest.get("model")
    if not isinstance(model_payload, dict):
        raise TypeError("run manifest is missing a model section")
    observed = model_payload.get("model_version")
    if observed != expected_model_version:
        raise ValueError(
            f"wrong manifest model version: expected {expected_model_version!r}, observed {observed!r}"
        )
