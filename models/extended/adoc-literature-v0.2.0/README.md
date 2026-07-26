# ADOC Literature Extension v0.2.0

This directory contains a standalone MaBoSS literature extension built on the
immutable baseline `models/baseline/adoc-core-v0.1.0/`.

## Scope

- Maternal-only executable logic.
- Embryo presence, trophectoderm competence, hCG, and generic embryo-conditioned
  signals remain external inputs.
- No trophoblast, immune, endothelial, or unsupported environmental subnetwork
  is modeled internally.
- No patient personalization is encoded here. Any future patient-contextualized
  model must be created as a versioned child variant rather than by editing this
  directory in place.

## Promoted maternal mechanisms

- Epithelial `E_LIF -> E_GP130_STAT3` attachment gate.
- Epithelial barrier and permissive-surface logic: `E_PODXL`, `E_PC6`,
  `E_DAG1_FULL`, `E_DAG1_CLEAVED`, `E_MUC1_BARRIER`, `E_MUC1_SLEX`.
- Epithelial positive support routes: `E_HBEGF`, `E_ITGAVB3_5`,
  `E_CD98_CD9`, `E_ANXA2_ACTIN`, `E_CDH1_APICAL`.
- Stromal decidual and matrix routes: `S_NR2F2`, `S_BMP2`, `S_HAND2`,
  `S_DECIDUALIZED`, `S_SPP1`, `S_TAZ_ECM`.
- Interface abstractions: `X_SPP1_LUMEN_FREE`, `X_ADHESION_ROUTE_SPP1`,
  `X_ADHESION_ROUTE_REDUNDANT`, `X_ANTIADHESIVE_ROUTE`,
  `X_MECHANICAL_STRESS_RELAY`, `X_MECHANICAL_PERMISSIVE_ECM`,
  `E_RECEPTIVE_SURFACE`.

## Condition semantics

The required condition files are challenge-ready assay abstractions:

- embryo presence, competence, and contact inputs are ON for every condition
  except `embryo_absent.cfg` and `embryo_incompetent.cfg`;
- hormone and perturbation inputs vary by file;
- hCG and embryo-conditioned-signal inputs remain available as external inputs
  but are left OFF in the required condition suite because the assigned
  qualitative checks do not require them;
- excess ER stress and excessive stiffness act as bounded adverse modifiers
  through `X_MECHANICAL_STRESS_RELAY` rather than as deterministic kill
  switches.

## Phase 1C runtime notes

- The default comparator keeps `S_HAND2` as a recorded relay/readout node; the
  stricter `NR2F2 -> BMP2 -> HAND2` consequence is available only as an
  explicit rule-variant selection.
- The default comparator keeps `E_CDH1_APICAL` contact-gated to avoid an
  undocumented self-reinforcing loop; alternate uncertainty variants may add
  maternal priming only when explicit external embryo cues remain present.
- Anti-SPP1 neutralizes `X_SPP1_LUMEN_FREE` only. The redundant positive route
  remains executable in the default and alternate comparator variants.
- `OUT_MATERNAL_ADHESION_COMPETENCE` is evaluated from mechanistic receptive,
  decidual, interface, and mechanical states rather than from downstream
  PAEP/PRL/IGFBP1 reporting outputs, so sequential continuation does not depend
  on carrying those readout nodes through joint memory.

## Validation commands

Structural parsing:

```bash
python - <<'PY'
from pathlib import Path
import tomllib
root = Path("models/extended/adoc-literature-v0.2.0")
tomllib.loads((root / "provenance.toml").read_text())
for path in [root / "network.bnd", root / "baseline.cfg", *sorted((root / "conditions").glob("*.cfg"))]:
    text = path.read_text()
    assert text.strip(), path
print("structural files present")
PY
```

Minimal runtime smoke when the pixi MaBoSS runtime is available:

```bash
pixi run python - <<'PY'
from pathlib import Path
import json
import maboss

root = Path("models/extended/adoc-literature-v0.2.0")
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
    "OUT_EPITHELIAL_RECEPTIVE",
    "OUT_STROMAL_DECIDUALIZED",
    "X_MECHANICAL_PERMISSIVE_ECM",
    "OUT_MATERNAL_ADHESION_COMPETENCE",
    "OUT_STABLE_ADHESION",
]].to_dict(), sort_keys=True))
PY
```

## Claim boundary

- This is an executable literature extension, not a calibrated patient digital
  twin.
- MaBoSS probabilities are simulated trajectory frequencies under this model,
  not clinical probabilities.
- The included perturbation conditions are model-internal contrasts only.
