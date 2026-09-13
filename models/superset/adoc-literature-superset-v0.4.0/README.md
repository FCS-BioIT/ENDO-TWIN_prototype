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

root = Path("models/superset/adoc-literature-superset-v0.4.0")
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

- `models/superset/adoc-literature-superset-v0.4.0/complete_nodes.tsv`: `efacf3b7437e3a381ef2a5cfeb08f8ea552ca9d5a30af1b2247066eb15c67d9a`
- `models/superset/adoc-literature-superset-v0.4.0/complete_edges.tsv`: `ac39e95012688d8de7314a7486056fa3eab93f1784f523c8dbd00be309b14e00`
- `models/superset/adoc-literature-superset-v0.4.0/modules.tsv`: `1cea79e6548c613112d52b3ca23d77a28eb635db0bb6c0ec8f1711387fe0f764`
- `models/superset/adoc-literature-superset-v0.4.0/module_activity_report.tsv`: `70856e7f307d3c2fddff712e13fe6593b3c49c5980b653006c9f646d13fe1914`
- `models/superset/adoc-literature-superset-v0.4.0/rule_variants.tsv`: `a5e6be6afb3d0f95c51d12ac06a128ed9f8789791b6d6556fcc39b94a535a839`
- `models/superset/adoc-literature-superset-v0.4.0/interface_contract.tsv`: `052414ce3fe3e535ddfc18a14f3e7005ee0f33d368659a2cd52da966d9332090`
- `models/superset/adoc-literature-superset-v0.4.0/drug_target_catalog.tsv`: `6f15497fbe7b93dc85d8c749d1a0883bdaa3b2834f576faf1aacb1f03fdbbc14`
- `models/superset/adoc-literature-superset-v0.4.0/executable_model_manifest.tsv`: `4dc757b58247ab24843b6442620a39fec8e82c88ab3cb804d27a893aef4ffbbf`
- `models/superset/adoc-literature-superset-v0.4.0/ensemble_definition.tsv`: `63452a3d6b8ac7832b7981656c2bfa19bff898090116f8e19cdf88c3692d1944`
- `models/superset/adoc-literature-superset-v0.4.0/unresolved_mechanisms.tsv`: `94ea4d8ff6e7be104c89d95efb0abb75f56056190338adf958a1824d255cf630`
- `models/superset/adoc-literature-superset-v0.4.0/literature_superset_network.mmd`: `6f03110cb630491630a3351e05d87d9cf07a4aec4a97b0298665b076806c24c8`
- `models/superset/adoc-literature-superset-v0.4.0/executable_modules_network.mmd`: `2f62c046bb2137f280dbd52688ab3d0f7673709ac8df7d7e83f782610b7112c1`
- `models/superset/adoc-literature-superset-v0.4.0/network.bnd`: `09e3b26aeb4e2f3b0339ef852764f5de4b922984df0b0a1014c91b4a17a36637`
- `models/superset/adoc-literature-superset-v0.4.0/baseline.cfg`: `4d42bdcbcfcceaedaafeeb96fe76400700175c969cec15bff9e02f360ff4f41c`
- `models/superset/adoc-literature-superset-v0.4.0/node_dictionary.tsv`: `a566d2abba87f8b019857a33b34a03d63ba5310aeb285f59412aaf91de516828`
- `models/superset/adoc-literature-superset-v0.4.0/edge_evidence.tsv`: `cac102405fb7a0ccf15a4254fa37c427bfa8902e5bd5fd4550c0720b53a42fe4`
- `models/superset/adoc-literature-superset-v0.4.0/topology.tsv`: `a4d630ae9e302dd32e30853c6457d95940aa61f879b2b81274ccb4b5a344221c`
- `models/superset/adoc-literature-superset-v0.4.0/phenotype_contract.tsv`: `4df11861ae82612876dd28d4269a5d06f39a941b29d029d4bb8fe72e63dd22d5`
