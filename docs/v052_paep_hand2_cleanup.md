# v0.5.2 — PAEP readout gate (C1) and HAND2 routing (C5)

**Status: complete. Run 2 is valid under the prospectively corrected gate (§4).** v0.5.2 is emitted from v0.5.1. It is
not adopted by any analysis module; each module pins its own model version.

## 1. The two changes, and why

```
C1  OUT_EPITHELIAL_RECEPTIVE   = E_RECEPTIVE_SURFACE                 (was: ... and E_PAEP)
C5  E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC           (was: ... and not S_HAND2)
```

No other topology change from the 163-paper re-audit is in this version (§7).

**C1 — output semantics.**

- PAEP/glycodelin is a secretory-differentiation readout: mainly glandular,
  present on the luminal apical surface but not luminally specific
  (Stavreus-Evers 2006 Fig 1).
- It is used as a hormone/cAMP readout in organoids with no attachment assay
  (Turco 2017 Fig 3; Fitzgerald 2019 Fig 2).
- A bounded full-text search of all 139 library PDFs found no experiment that
  perturbs PAEP with an adhesion endpoint.
- So PAEP must not define the reported receptivity phenotype. `E_PAEP` remains
  an observable state, and the ADOC PAEP outlet still maps to it (`OM-001`).

**C5 — a semantic change to the model architecture** (owner decision
2026-09-28, recorded `SEMANTIC_OR_PROTOCOL`).

- v0.5.1 encoded HAND2 twice: a direct epithelial veto, and suppression of the
  stromal relay. v0.5.2 encodes HAND2 → stromal relay → epithelial
  proliferation.
- The evidence supports stromal paracrine mediation:
  - Li 2011 (mouse): stromal Hand2 suppresses the FGFs that mediate estrogen's
    epithelial mitogenic effect.
  - Murata 2019 (human stroma): HAND2 suppresses FGF9.
- It does not support a direct epithelial HAND2 edge.
- C5 is not a refactor. Under asynchronous updating, proliferation now stays on
  until the relay switches off, and that delay is intended.
- `S_FGF_MITOGENIC` keeps its name. The human relay identity is uncertain:
  Murata's FGF9 effect is stromal and vascular, not epithelial. It may later be
  generalised to `S_TO_E_PROLIFERATION_RELAY`.

Evidence, one row per claim with DOI, PDF sha256, the panels checked and what
each source does **not** support: `docs/v052_paep_hand2/evidence.tsv`.

## 2. Structure: what cannot move, and what can

- **Over the free variables, no node's composed function changes.** This is
  checked exhaustively over all 2^19 = 524,288 assignments
  (`v052_increment.structural_identity`). No condition can move an unperturbed
  fixed point.
- **The affected set is seven nodes**, exactly as pre-registered:
  - the two changed nodes;
  - `E_RECEPTIVE_SURFACE`;
  - `X_ADHESION_ROUTE_SPP1` and `X_ADHESION_ROUTE_REDUNDANT`;
  - `OUT_MATERNAL_ADHESION_COMPETENCE`;
  - `OUT_STABLE_ADHESION`.

  The other 52 nodes read none of them, so their law is unchanged.
- **Exactly three internal clamps separate the versions at steady state**
  (`separating_clamps.json`, exhaustive over every non-free node, ON and OFF):
  - `E_PAEP`=0 no longer abolishes receptivity (C1).
  - `E_RECEPTIVE_SURFACE`=1 no longer needs PAEP (C1).
  - `S_FGF_MITOGENIC`=1 now drives proliferation under progestin, and so blocks
    the receptive surface (C5's full-mediation semantics).

  No committed protocol or experiment arm clamps any of them.
  `S_FGF_MITOGENIC` is a catalogued executable drug target, so a future screen
  could.

## 3. Pre-registration history

| commit | what |
|---|---|
| `969d1fe` | original pre-registration, before v0.5.2 existed |
| `3318c7d` | v0.5.2 as run 1 used it; run 1 preserved in `run1_invalid/` |
| `dcee55c` | v0.5.2 re-emitted, text only (C5 semantics); `network.bnd` unchanged |
| `658056b` | addendum 01, prospective correction of the identity gate, before run 2 |
| `022fb97` | runner implementing addendum 01; run 2 ran against this commit |

- **Run 1 is INVALID under its frozen expectation 1** (`run1_invalid/README.md`).
  - The node-marginal differences were at most 7.7 × 10⁻¹⁶.
  - The per-state distributions were exactly identical.
  - The cause is floating-point summation order.
- **The owner ruled that the frozen rule stands.** Addendum 01 then:
  - tests exact identity on final-tick per-state distributions, plus node
    differences ≤ 1e-12;
  - snaps |d| ≤ 1e-12 to 0 before the estimands;
  - uses fresh seed blocks.

  Nothing else changed.
- **The interval is an empirical paired block-reproducibility band**, not a
  family-wise interval. This is the same wording correction the owner made for
  U5b, applied by the addendum.

## 4. Run 2 — validity (addendum 01)

Run 2 ran from 2026-09-28 22:47 to 2026-09-29 02:06, with 2 workers and a peak
of 31 GB. It used 20 blocks × 20,000 trajectories plus 20 × 2,000 on fresh
seeds, and v0.5.2 `network.bnd` `7a73529c…`. Its recorded `git_commit` is
`3fb7171`, because provenance is stamped at the end and the literature commit
landed mid-run. That commit descends from the runner commit `022fb97`, and
every generator file is hash-recorded.

| check | v052 vs v051 | C1-only | C5-only |
|---|---|---|---|
| 1. identity where the rules cannot differ (A1) | **held** | **held** | **held** |
| final per-state distributions bitwise equal | yes | yes | yes |
| max node difference in those cells | 2.0e-15 | 0 | 1.4e-15 |
| 2. unaffected family: `BEYOND_TOLERANCE` | 0 | 0 | 0 |
| 2. unaffected family: `INDETERMINATE` (too wide to certify) | 55 of 780 | 22 of 860 | 59 of 780 |
| 3. attribution direction | — | held | held |

- **Run 2 is reported under both rules.**
  - It passes addendum 01, which governs run 2.
  - It **fails the original exact-zero node-marginal criterion**: the largest
    node difference in the three identity cells is 2.0 × 10⁻¹⁵ (combined) and
    1.4 × 10⁻¹⁵ (C5-only). C1-only would pass it exactly, with a largest
    difference of 0.
  - The owner consulted Codex on which rule governs (`aih consult`,
    2026-09-29). It recommended the addendum, provided this dual statement is
    made.
- **Limits of the corrected gate.**
  - Bitwise-equal final-tick per-state distributions establish identical final
    aggregates, not bitwise-identical trajectories within a phase. The every-tick
    node check at ≤ 1e-12 narrows that gap but does not close it.
  - The summation-order diagnosis was verified for these comparisons only. It is
    not a general property of every rule change.
- **Expectation 2 is recorded as not met at this precision**, as the
  addendum requires. It is not held, but it is not a defect: no unaffected
  interval lies beyond tolerance, and the widest band end is 0.0078.
- **One primary interval is `UNSTABLE`:**
  `adhesion_challenge_hormone_treated:OUT_EPITHELIAL_RECEPTIVE:final_tick`.
  The two trajectory counts disagree there, so it is not interpreted. Its
  phase-averaged interval is stable.

## 5. Run 2 — how much v0.5.2 moves, at the declared horizons

These are paired differences, v0.5.2 minus v0.5.1, in occupancy units over the
seven hormone-exposed cells at 20,000 trajectories: phase-averaged, with final
tick in brackets. `B` counts `BEYOND_TOLERANCE` cells out of 7. The source is
`docs/v052_paep_hand2/transient_comparison.tsv`.

| node | v0.5.2 (C1+C5) | C1-only | C5-only |
|---|---|---|---|
| `E_ESTROGENIC_PROLIFERATION` | **+0.043 to +0.167** [+0.033 to +0.196], B 7 | ~0 | +0.043 to +0.167, B 7 |
| `OUT_EPITHELIAL_RECEPTIVE` | **−0.002 to +0.147** [−0.015 to +0.210], B 6 | +0.001 to +0.166, B 6 | −0.016 to −0.002, B 3 |
| `E_RECEPTIVE_SURFACE` | **−0.065 to −0.008** [−0.069 to −0.027], B 7 | ~0 | −0.065 to −0.008, B 7 |
| `X_ADHESION_ROUTE_SPP1` | −0.018 to 0.000, B 2 | ~0 | −0.018 to 0.000, B 2 |
| `X_ADHESION_ROUTE_REDUNDANT` | −0.013 to −0.001, B 3 | ~0 | −0.013 to −0.001, B 3 |
| `OUT_MATERNAL_ADHESION_COMPETENCE` | 0.000 to +0.005 [to +0.016], B 1 | 0.000 to +0.006, B 2 | −0.001 to 0.000, B 0 |
| `OUT_STABLE_ADHESION` | 0.000 to +0.0004 [to +0.0015], B 0 | 0.000 to +0.0005, B 0 | 0.000, B 0 |

Reading it:

- **C5 changes asynchronous transients by design.** Epithelial proliferation
  stays on longer, by up to 0.17 phase-averaged and 0.20 at the final tick,
  because it now waits for the stromal relay to switch off. The added
  proliferation vetoes the receptive surface, which falls by up to 0.065, and
  the two adhesion routes drop slightly with it. None of this is a defect. It
  is what representing the relay explicitly means.
- **C1 alone moves the epithelial readout up, by up to 0.17,** because the
  readout no longer waits for `E_PAEP`. It leaves every other affected node
  within about 0.0008, except the adhesion-competence output.
- **The two partly cancel on `OUT_EPITHELIAL_RECEPTIVE`.** In
  `hormone_treated_maternal` the combined change is −0.002.
- **The final adhesion endpoint does not materially change.**
  `OUT_STABLE_ADHESION` moves by at most +0.0004 phase-averaged (+0.0015 at the
  final tick), within tolerance in every cell. `OUT_MATERNAL_ADHESION_COMPETENCE`
  moves by at most +0.005 phase-averaged, and beyond tolerance in one cell
  only. Both outputs are near zero in both versions at the declared horizons.
- **No steady state moves** (§2). These are finite-horizon differences in
  dimensionless MaBoSS time: not days, and not probabilities that any
  epithelium is receptive.

## 6. Literature: what was verified, and what the audit gets wrong

The re-audit (`context/literature/reviews/maboss_163_reaudit_v3_2026-09-28.md`,
`SRC-006`) is owner input for reconciliation, committed unedited. Its 163-PDF
archive and five reader outputs are not in this repository, so its confidence
scores are not reproducible here. Everything this unit relies on was re-checked
in the primary PDFs on 2026-09-28:

- **What was checked:** `context/literature/active_evidence_manifest.tsv` lists
  exact title, DOI, sha256 and verification level per paper.
- **Figure level:** 24 primaries, panels inspected and significance marks read.
- **Text level only:** Li 2011, Murata 2019, Riesewijk 2003, Heng 2011, Heng
  2015.
- **Newly registered:** REF-092 to REF-096, the primaries C1 cites.

Audit statements the primary PDFs do **not** support as written:

| audit | what the PDF shows |
|---|---|
| Riesewijk 2003 supports PRL/IGFBP1 non-equivalence | the paper contains no PRL at all |
| Wang 2020 shows PRL/IGFBP1 timing differences | PRL is essentially undetected (occupancy, not timing); epithelial IGFBP1 exceeds stromal at mid-secretory |
| Gnecco 2019 is "strong" kinetic evidence for IGFBP1 before PRL | holds in the perfused arm only; ambiguous in the static arm; the authors do not state it |
| stromal PAEP | rests only on Muñoz-Blat 2025 ED Fig 3b (mRNA), which the audit does not cite |
| PAEP "not luminal" | Stavreus-Evers Fig 1g-h shows it on the luminal surface: not luminal-specific |
| αVβ3/αVβ5 allocation (D4) | Heng 2011/2015 are DAG1 papers; PC6 → β5 rests on Paule 2012 Fig 4 alone; Chung 2016 shows β5 blockade ≥ β3 on attachment |
| anti-SPP1 "delay, not block" (C4) | Kang 2014 used epithelial siRNA, not an antibody; the 48 h convergence is "data not shown" |
| Gnecco 2023 supports mechanical permissiveness | it has no embryo experiment |
| XAV939 §2.1 "excluding a canonical stromal WNT veto" | logically reversed: decidualization under XAV939 excludes a WNT *requirement* |
| D5 human progesterone dependence of IHH | not found in the checked sources; Fitzgerald is n = 2 donors, with the day-12 prose contradicting its figure |
| Lessey & Young 2019 review | the local PDF is a textbook chapter, not the cited review |
| LIF/IL11 convergence (D3) cited to four papers | only Marwood 2009 carries it; Cullinan, Yap and Chung each lack IL11 or STAT3 |

## 7. Deferred, unchanged by this unit

These remain future explicit units or uncertainty families, and none is
implemented here:

- the MUC1 abundance/glycoform/clearance split (`TI-06`);
- the CD98/CD9 split;
- LIF/IL11/STAT3 de-aliasing;
- the αVβ3/αVβ5 split (`TI-03`);
- IHH/PGR replacement;
- the mechanical-permissiveness split;
- independent PRL/IGFBP1 rules (`TI-04`);
- a generalised stromal relay;
- XAV939, hCG and embryo-conditioned-signal wiring;
- named replacements of `X_*` relays;
- any rate constant from qualitative timing.

The audit's §10 experiment ordering (minus-XAV939 and minus-cAMP first) is not
adopted. The U8 rerank, with `dropout_e2` first, stands.
