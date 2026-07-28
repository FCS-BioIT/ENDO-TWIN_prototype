# ADOC Literature Superset v0.3.0

This directory contains the Phase 1D literature-superset family for the ADOC
maternal adhesion model.

## Scope

- Starts from the immutable executable parent `models/extended/adoc-literature-v0.2.0/`.
- Adds only the bounded executable extensions supported by explicit candidate
  logic hints:
  - `E_KLF12_HIGH` as an optional inhibitory context for epithelial `LIF`;
  - `S_FGF_MITOGENIC` as a HAND2-restrained stromal mitogenic relay;
  - `E_ESTROGENIC_PROLIFERATION` as an anti-receptive epithelial state that
    suppresses the receptive surface.
- Keeps unsupported, spatial, embryo-side, or unparameterized biology explicit
  in the catalogs and unresolved-mechanism tables instead of making it silently
  executable.

## Claim Boundary

- Structural and bounded executable architecture only.
- No patient personalization is encoded here.
- MaBoSS probabilities remain simulated trajectory frequencies, not clinical
  probabilities.
- Drug-target and ensemble catalogs remain `structural_only` and do not imply
  validated efficacy.

## Family Artifacts

- `complete_nodes.tsv`, `complete_edges.tsv`: full provenance-preserving node
  and edge catalogs with candidate-to-implementation crosswalk fields.
- `modules.tsv`, `module_activity_report.tsv`: module catalog and structural
  activity status.
- `rule_variants.tsv`, `unresolved_mechanisms.tsv`: explicit executable and
  non-executable alternatives.
- `interface_contract.tsv`: external inputs and unsupported biology kept at the
  boundary.
- `drug_target_catalog.tsv`, `ensemble_definition.tsv`: bounded screening-ready
  architecture metadata only.
- `network.bnd`, `baseline.cfg`, `conditions/*.cfg`: executable superset
  runtime artifacts.
- `node_dictionary.tsv`, `edge_evidence.tsv`, `phenotype_contract.tsv`:
  executable model contract tables.

## Validation Commands

Structural generation and validation:

```bash
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -m dt_adoc.model.superset_family --write
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -B -m dt_adoc.model.superset_family --validate
```

Minimal MaBoSS smoke when the Pixi runtime is available:

```bash
pixi run python - <<'PY'
from pathlib import Path
import json
import maboss

root = Path("models/superset/adoc-literature-superset-v0.3.0")
condition = root / "conditions" / "hormone_treated.cfg"
sim = maboss.load(str(root / "network.bnd"), str(root / "baseline.cfg"), cmaboss=True)
for raw in condition.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("//"):
        continue
    lhs, rhs = line.rstrip(";").split("=", 1)
    node = lhs.strip().replace(".istate", "")
    sim.network.set_istate(node, [0.0, 1.0] if rhs.strip() == "TRUE" else [1.0, 0.0])
res = sim.run()
print(json.dumps(res.get_last_nodes_probtraj().iloc[-1][[
    "X_MECHANICAL_STRESS_RELAY",
    "X_INTERFACE_SPP1_RELAY",
    "X_INTERFACE_REDUNDANT_RELAY",
    "X_INTERFACE_ANTIADHESIVE_RELAY",
    "OUT_EPITHELIAL_RECEPTIVE",
    "OUT_STROMAL_DECIDUALIZED",
    "OUT_MATERNAL_ADHESION_COMPETENCE",
    "OUT_STABLE_ADHESION",
]].to_dict(), sort_keys=True))
PY
```

## Generated File Hashes

- `models/superset/adoc-literature-superset-v0.3.0/complete_nodes.tsv`: `be5d0dfb402b372028a11a39cef26ed1bd25453300b5cf1a5c5a817703e537d7`
- `models/superset/adoc-literature-superset-v0.3.0/complete_edges.tsv`: `b1402b5dab09ad2e3d7f5833624f6130a15798e50479e59983a82396dd735bdc`
- `models/superset/adoc-literature-superset-v0.3.0/modules.tsv`: `c410fb7f374550e8e442d4f48c038e4779fdcfe5a57c3ce3511d22143bdf9b9e`
- `models/superset/adoc-literature-superset-v0.3.0/module_activity_report.tsv`: `64955b58854a1ee5e1209bde9a3bf60eb5b77fc4b53da3f5e8ff7db9e53d89bd`
- `models/superset/adoc-literature-superset-v0.3.0/rule_variants.tsv`: `e8adcb76837ae31e04174a18ac112fde65369221cf89e0acbe8a650661fc15e1`
- `models/superset/adoc-literature-superset-v0.3.0/interface_contract.tsv`: `5b8e8fa2570bbbe1e1c6559becb6c706d0807b77326e20f8c051bbef71a724c0`
- `models/superset/adoc-literature-superset-v0.3.0/drug_target_catalog.tsv`: `6f15497fbe7b93dc85d8c749d1a0883bdaa3b2834f576faf1aacb1f03fdbbc14`
- `models/superset/adoc-literature-superset-v0.3.0/executable_model_manifest.tsv`: `4babbec18087a44e077610c8230a9952392c81bdf7fbb51853bcbfaa9bcd3da8`
- `models/superset/adoc-literature-superset-v0.3.0/ensemble_definition.tsv`: `17f0261f711f5634e2fd7bd2241415fbfc5b5c2eab7743f7e532a1a5ea0b9f65`
- `models/superset/adoc-literature-superset-v0.3.0/unresolved_mechanisms.tsv`: `94ea4d8ff6e7be104c89d95efb0abb75f56056190338adf958a1824d255cf630`
- `models/superset/adoc-literature-superset-v0.3.0/literature_superset_network.mmd`: `36faeb50c4e0e0ee9617fac956b5286e397858b2a5a2c99bf1c603e1c5af1ff0`
- `models/superset/adoc-literature-superset-v0.3.0/executable_modules_network.mmd`: `505e99f5c23bb7c6f3cae1a21743c38bd7741e053c6dc0dfde15876290ac7f27`
- `models/superset/adoc-literature-superset-v0.3.0/network.bnd`: `ecb6b7d3de295a6c8778ffa4f6b4cb8b87bcf6da9f9b200a24e601090f7f9456`
- `models/superset/adoc-literature-superset-v0.3.0/baseline.cfg`: `6959907700d48d3072e2fa26f605c21798f7bf512e5779e570d3bdef23bf9842`
- `models/superset/adoc-literature-superset-v0.3.0/node_dictionary.tsv`: `14deb16c90088a0e5eac161d3495012ae72bf8f155d0b883136fd3da90c8b067`
- `models/superset/adoc-literature-superset-v0.3.0/edge_evidence.tsv`: `e6d4a1d563ffc85bf32618a092d197bac43172d577b0d7aca02c0cf180a062b3`
- `models/superset/adoc-literature-superset-v0.3.0/topology.tsv`: `c542f94a240d90baa346b0e4b2f2c7d4ee504b637f9ac6ddc70b15b24f7b09fe`
- `models/superset/adoc-literature-superset-v0.3.0/phenotype_contract.tsv`: `4df11861ae82612876dd28d4269a5d06f39a941b29d029d4bb8fe72e63dd22d5`
