# Which ADOC results can the digital twin reproduce?

Status: **diagnostic assessment, 2026-07-29.** Claim level: `structural` + `reproducible`.
No model, rule, protocol or calibration file was changed to produce it.

The fielded record is
[`docs/results_reproducibility_matrix.tsv`](results_reproducibility_matrix.tsv) —
**60 rows over 55 distinct published results**, machine-validated by
`tests/unit/test_results_matrix.py`. This document is the narrative; the TSV is
authoritative.

Model assessed: **`adoc-literature-superset-v0.3.0`** (58 nodes, 96 executable
dependencies), the latest full network. Source commit is recorded per run in
`output/reproducibility/run_settings.json`.

---

## The headline, stated plainly

**Of 55 published results, 3 are qualitatively reproduced, 1 partially, 1 is
contradicted, 0 are quantitatively reproduced, and 51 are not assessable at all.**
(Counts are over the 60 matrix rows. CORRECTED 2026-09-11: R43a moved from
contradicted to not assessable, so these read 2/50 in earlier revisions.)

That is not a failure of the twin. **42 of the 55 results are bound by topology
and 36 by the need for continuous or spatial modelling** — tissue architecture,
barrier permeability, extracellular vesicles, embryo lineage identity and
position, cell-type proportions. A Boolean logical model has no geometry, no
volume, no flux and no cell populations, so those results are *permanently out
of scope for this model class*, not pending work. Reporting them as "not
reproduced" without that attribution would be misleading in the opposite
direction.

The honest summary is narrower and more useful: **the twin engages 8 of the
paper's 55 results, and of those 8, exactly one comparison has a genuinely
held-out magnitude.** Its *direction* is not held out: both
`IN_MIFEPRISTONE ⊣ PGR` edges were constructed citing `SOFIA-HT-002`, the same
study's methods. See the mifepristone paragraph below.

## Summary counts

| Category | Count | Basis |
|---|---:|---|
| Results reviewed | **55** | every result in the manuscript, published article and supplementary |
| Matrix rows | **60** | 5 results carry a declared/converged horizon pair |
| Results with a DT node and a simulated value | **8** | R12, R15, R41, R42, R43, R44, R54, R55 |
| **Newly assessable because of the new metadata** | **0** | see below — the metadata changed 5 comparisons and enabled none |
| Qualitatively reproduced (direction only) | **3** | R41b, R42, R44 |
| Partially reproduced (direction only) | **1** | R43b — the held-out arm |
| **Quantitatively reproduced** | **0** | structurally impossible; see "Why never quantitative" |
| Contradictory | **1** | R41a, at the declared horizon, + the one structural falsification below (IGFBP-1/PRL onset order), which is **unaffected**. CORRECTED 2026-09-11: R43a was also counted here and is **not assessable**. (Re-corrected 2026-09-12: the phase `hormone_treated_mifepristone` **exists** and is executable — the earlier wording "has no mifepristone phase" was false — but nothing continued from it, so the embryo challenge was seeded from the hormone-treated state. SUPERSEDED 2026-09-13: that wiring defect is repaired and the executed chain now runs the maternal mifepristone phase, so the regimen matches. R43a remains not assessable for an independent reason that the repair exposed rather than caused — at the declared horizon the arm has no stable value, with an across-seed spread the size of the value itself, including exact zeros.) Separately, an *unrelated* structural-falsification claim about the mifepristone residual, made elsewhere in this repository, has been withdrawn; see `concordance_analysis.md`. |
| Circular by construction | **4 rows / 2 results** | R12, R15 — the model's only two measured nodes |
| Needs network extension (topology-bound) | **42** | no node exists |
| Needs continuous/spatial modelling (PhysiBoSS2) | **36** | geometry, transport, populations |
| Experimentally unidentifiable | **13** | assay design forecloses it regardless of modelling |

Categories overlap: a result may be both topology- and geometry-bound.

## Why "quantitatively reproduced" is never available

Five independent blockers, each sufficient alone:

1. **No calibrated time.** `config/calibration.yaml`: `calibrated_physical_time: false`;
   `provenance.toml`: `maboss_time_units = "relative_only"`. Every simulated value
   is indexed by a dimensionless parameter, so it cannot quantitatively reproduce
   a quantity measured at day 3 or day 6.
2. **No magnitude-fitted term exists.** `adhesion_objective` was the only one
   and was demoted to `diagnostic_ordinal` on 2026-09-16
   (`docs/gate3_scope_adjudication.md` §3); no replacement was manufactured.
   Agreeing with a fitted term would have been calibration rather than
   reproduction, and `search.exact_probability_matching_forbidden: true` already
   forbade pursuing it. The blocker is now stronger, not weaker: there is no
   fitted quantity to agree with.
3. **At the decided horizon the comparison is binary.** Of 405 converged
   (protocol, node) readouts, **345 are exactly 0 or 1**. A 0-or-1 match is not a
   magnitude.
4. **Where a magnitude survives, it is two typed-in numbers.** The converged
   adhesion value is `1 − (1 − 0.70)(1 − 0.40) = 0.82` exactly, from the two
   hand-set relay `istate`s configured in `baseline.cfg`; the simulated 0.820340
   is the Monte Carlo estimate of it. (Corrected 2026-09-11: an earlier revision
   wrote the formula with 0.70072 and 0.39987, which are realised trajectory
   frequencies, not the configured values.) Every one of the 60 still-graded
   converged readouts is a static relay draw or an algebraic function of them.
5. **Where a magnitude exists, it disagrees.** Converged 0.820 against an observed
   9/19 = 0.474, whose Wilson 95% CI is [0.27, 0.68]. Held-out mifepristone:
   model 0.000000 against observed 1/8 = 0.125.

A sixth blocker sits on the observation side: the observed magnitudes have no
defensible denominator. `max_independent_units_paep_observed` is 3 (2 if the
cell-source groups are patients) and `max_independent_units_prl` is
`not_determinable`.

`tests/unit/test_results_matrix.py::test_quantitatively_reproduced_count_is_zero`
makes this a number under test rather than a promise.

## The horizon: every number is labelled, and here is why

The declared protocol horizon reads the adhesion endpoints **roughly 4000×
earlier than their logical fixed point** ([`docs/endpoint_convergence_finding.md`](endpoint_convergence_finding.md)).
More trajectories do not fix it: 0.000300 at 2 000, 0.000206 at 20 000, 0.000353
at 100 000 — all ~2300× below the converged 0.820. The interval tightens around
the wrong value.

So every simulated cell in the TSV carries `horizon_class ∈ {declared, converged}`
plus `max_time`, `time_tick`, `trajectory_count`, `seeds` and `mc_sd_across_seeds`.
A declared value and a converged value for the same arm are **two rows**, never
one number.

Two consequences the matrix states rather than hides:

- **The declared horizon is the repository's live configuration.** `config/protocols.yaml`
  still declares `relative_duration: 1.0` for the challenge phases. The
  converged horizon is a run-time override. "Declared" is what the repository
  actually does today.
- **The converged horizon is not the calibrated one.** `config/calibration.yaml`
  was fitted against short-horizon values and is superseded by any horizon
  change. Every converged row compared against those counts is compared against
  **superseded fits**, and says so.

All horizons are dimensionless MaBoSS relative-time units. Never a day count.

## What the new metadata actually did

**It enabled nothing and changed five comparisons.** Recording that honestly
matters, because the temptation is to present corrected metadata as unlocking
new reproduction.

| Correction | Direction |
|---|---|
| Day 0 confirmed pre-hormone (`SOFIA-ANNO-005`) | **Strengthened** OM-002's comparator from *assumed* to *supported*. Did not change its 3/5 support. |
| Day 3 = 24 h, day 6 = 96 h (`SOFIA-COMM-004`) | **Documentation only.** Wall-clock hours never become a MaBoSS horizon. Its one real effect is negative: it sharpens OM-004's rejection from "the data disagree" to "no protocol represents that state". |
| Cocktail identity `E2 + MPA + cAMP + XAV939` | **Weakening.** Combined with `IN_XAV939` being a zero-degree node, the simulated hormone response contains **no XAV939 contribution at all**. |
| Zero = measured non-detect | **Weakening.** OM-002's two failures become genuine directional failures rather than censoring artifacts, and the four paired day-6 zeros become a possible-dropout defect. |
| **PRL entirely BOTTOM** (`SOFIA-COMM-006`) | **Clearly weakening.** Detection 0/3, 1/3, 3/3 → **0/6, 1/6, 3/6**; the complete-separation claim retracted; day-6 basal values span 1.30–1465.44 pg/mL *within one outlet on one day*. |

## Two corrections applied 2026-09-15, neither of which clears a row

**The eleven scRNA rows said the repository does not hold the paper's annotated
object. It does.** R17 through R27 inclusive each carried the note *"The
repository does NOT hold the paper's 28,212-cell annotated object. SOFIA-RDS-001
is a different 61,843-cell intermediate."* That predates the acquisition of
ArrayExpress **E-MTAB-15842** `seurat_object.rds` — 28,212 cells, sha256
`504a674d…`, recorded as `EXT-SCRNA-001` in
[`config/external_data_manifest.tsv`](../config/external_data_manifest.tsv) and
used throughout the KLF12 workstream. The claim is withdrawn in all eleven rows.

**Correcting it removes one blocker and clears none of them**, and the eleven
rows now say which limitations survive and why, by type:

| rows | surviving limitations |
|---|---|
| R20, R21, R22, R23 | topology, assay design, calibration |
| R17 | topology (`missing_provenance` dropped — it named the object) |
| R19, R24 | topology |
| R27 | topology, assay design |
| R25 | calibration, assay design (never carried either topology or provenance) |
| R18, R26 | topology, continuous/spatial — formalism-limited whatever the provenance |

R20–R23 are the only four with comparators, which is what makes them the
re-adjudication candidates, and the comparators do not carry them: `OM-009` and
`OM-010` are `activation_status: reported_only`, `calibration_role: diagnostic`,
`confidence: low`, and their claim ceilings read **"Diagnostic only. Not usable
to validate …"**. **Newly assessable: still 0.** What this buys is an accurate
record of which blockers are real, not a row that became comparable.

**The converged rows' `max_time` read a stale 30.0.** The executed horizon is
`CONVERGED_PHASE_HORIZON = 25.0` per phase
(`src/dt_adoc/concordance/simulate.py`), and
`docs/concordance/run_settings.json` records
`provenance.converged_phase_horizon: 25.0`. R43b's own note already said so.
All seven converged rows now read 25.0. **No simulated value, comparison or
verdict changes**: `docs/endpoint_convergence_finding.md` records the endpoint
as stable from 20 to 60, so nothing numeric turned on it. This is metadata
cleanup, not a re-run.

## The one structural falsification

**The model cannot express the observed IGFBP-1-before-PRL onset order, and this
is a formal falsification rather than a gap.**

`network.bnd` gives `S_IGFBP1` and `S_PRL` the *identical* rule
(`logic = S_DECIDUALIZED`), the same initial state, and — since **no `rate_up` or
`rate_down` is declared anywhere in the repository** — the same transition rate.
Exhaustive enumeration puts them in one seven-member alias class with
`S_DECIDUALIZED`, `S_SPP1`, `S_TAZ_ECM` and `OUT_STROMAL_DECIDUALIZED`. Their
onset distributions are therefore identical by construction.

The observation is strictly ordered: at day 0 basal IGFBP-1 is detected in 4/5
columns at 37.9–551.3 pg/mL while basal PRL is 0/6; at day 3 IGFBP-1 is 5/5 with
4/5 above 1000 pg/mL while PRL is 1/6 with a maximum of 113.6. A 2× difference in
detection limits cannot manufacture a >25× day-0 gap.

Simulation confirms it: at the converged horizon both are exactly 1.0. At the
declared horizon they differ by 0.0033 with `S_PRL` **higher** in 15/15 seeds —
a seed-independent pipeline asymmetry running in the *wrong* direction.

`OM-016` records this as a standing structural requirement on candidate models.
The current model fails it.

## Why no literature-informed variant was built

The user's third comparison arm was considered and **deliberately not built.**
The obvious candidate — restoring the `S_FOXO1` node dropped after v0.1.0 to
differentiate the two markers — fails on three grounds, one fatal:

1. **It would produce the wrong order or nothing.** In the committed v0.1.0,
   `S_FOXO1` is read by nothing, so restoring it faithfully is a no-op.
   `models/specs/edges.tsv` carries `S_FOXO1 → S_PRL` *and* `S_FOXO1 → S_IGFBP1`
   symmetrically, so it gates both and leaves them synchronous. The source
   specification makes IGFBP-1 carry one *extra* conjunct
   (`S_DECIDUALIZED and S_FOXO1 and S_CEBPB`), which in a rate-free asynchronous
   model makes IGFBP-1 **later**, not earlier. Getting IGFBP-1 first requires an
   asymmetric wiring no record supports — an invented topology asymmetry, which
   is worse than an invented rate because it looks like curated biology.
2. **The evidence trail is a leakage loop.** Every `S_FOXO1` edge cites
   `SOFIA-STR-001`, which is the same in-house ELISA from which `OM-016` is
   derived. Choosing topology from an observation and then reporting that the
   model reproduces it is forbidden without an explicit leakage-control design.
   No reference in the 70-entry bibliography gives an IGFBP-1-versus-PRL time
   course.
3. **It would be invisible at the decided horizon.** `S_FOXO1 = S_PGR and S_PKA`
   is logically equivalent to `S_DECIDUALIZED` by absorption, so at the fixed
   point the variant is bit-identical to the current model. The onset difference
   exists only in the transient, and no transient readout policy exists.

**Arms 1 and 2 are also the same executable state.** The corrected metadata
changed the *observed* side only; no `.bnd` or `.cfg` byte differs. What changed
is the comparison, not the prediction. Manufacturing a difference would have
been dishonest.

## Somkuti 1997 and Jin 2025

Independently re-derived: **2 bibliography registrations, 20 verified expression
claims, 9 candidate relations, 0 observation mappings, 0 executable promotions.**
The four tiers are kept strictly separate.

- **Somkuti: no ADOC result is in scope.** ADOC never measured ITGB3, αvβ3 or
  ITGB5; there is no integrin readout anywhere. It bears on a model *rule*, not
  on any observation, and it has no adhesion assay.
- **Jin: the mechanism is unreachable in the ADOC design.** ADOC's HT arm holds
  progestin *and* cAMP ON for the full 96 h — the saturated regime where
  `S_IGFBP1 = 1` and a 1.6–3× potentiation has nothing to potentiate. `IN_HCG` is
  false in all 20 protocols, and Jin's own staging puts the route at LH+2, days
  before the day-6 window.
- **What Jin does diagnose, and it is worth keeping:** `S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2`
  has no epithelial input that survives absorption, so the model has **no working
  epithelium→stroma channel at all**. Jin is the corpus's only candidate for a new
  one — and still not promotable, on one named blocking experiment: EREG and
  HB-EGF on stromal cells without db-cAMP and without MPA.

Neither paper improves reproduction of any single ADOC result.

## Circularity, and the one held-out comparison

Two of the eight engaged results are **circular by construction**: R15 (`E_PAEP`,
OM-001) and R12 (`S_IGFBP1`, OM-002). These are precisely the model's only two
measured nodes, and their mapping rows were built by *demoting* the OM-003…OM-017
alternatives against the same cells. OM-001 is the sole `active_constraint` — the
feasibility gate on the retained ensemble — so agreeing with it is agreement with
the filter.

`SOFIA-ADH-003` / **R43 (mifepristone, 1/8) is the only held-out
*magnitude*** comparison, and the hold-out is enforced in code, not merely
declared: `src/dt_adoc/calibration/objectives.py` sums the calibration likelihood
over `roles=("calibration",)` only. Its verdict is **held-out direction agreement
with held-out magnitude disagreement** — the direction is strongly right
(0.820 → 0.000) and the magnitude is wrong by ~2500×.

Two corrections to earlier revisions of this paragraph, both recorded rather than
silently edited (2026-09-11):

- The magnitude was described as **structurally unreachable**, on the grounds
  that mifepristone clamps PGR so no parameter setting yields `p > 0`. That is
  wrong. The exhaustive enumeration constrains the Boolean *target function* at
  its fixed point, not the simulated observable: the same arm averages
  `0.000020` at the declared horizon, non-zero in three of its five seeds. The
  accurate statement is that the support is `{0}` **at the asymptotic Boolean
  fixed point**, which is what the enumeration does establish. The converged
  horizon is a separate and weaker matter: those runs record `0.0` in 5/5 seeds,
  which `concordance_analysis.md` records as an observation about those runs and
  explicitly not a demonstration that the finite-horizon support *is* `{0}`.
  Either way the failure belongs to the complete-antagonism encoding rather than
  to the Boolean model class.
- The **direction** is not independent either. Both `IN_MIFEPRISTONE ⊣ E_PGR`
  (LE002) and `IN_MIFEPRISTONE ⊣ S_PGR` (LE038) cite `SOFIA-HT-002`, the same
  study's methods, so a reduction was guaranteed by construction. Only the
  magnitude was held out. `SOFIA-HT-002` has no entry in
  `config/evidence_roles.yaml` at all, and the evidence register's own
  instruction to "pre-register whether this row defines a perturbation or remains
  held out" was never closed.

See [`concordance_analysis.md`](concordance_analysis.md) for the regenerated
values, the repaired regimen lineage and the horizon instability that is R43a's
remaining limitation, and the per-row mechanism.

**No row in this matrix constitutes validation.**

## What would change the picture

In rough order of value:

1. **A day-3 protocol stage** (`OM-011`). One third of the assayed time course is
   currently unreachable. It needs no rule change, but it is not free: splitting
   the HT phase shifts the day-6 endpoint by 0.007–0.010, because the
   continuation memory policy carries only 35 of 45 tracked nodes and each new
   boundary adds a reset. Necessary, not sufficient.
2. **Implementing the endpoint-readout policy** in `config/protocols.yaml`, which
   requires recalibration.
3. **Differentiating `S_IGFBP1` from `S_PRL` on external evidence** — the one
   change that would let the model be tested against `OM-016` rather than
   failing it by construction.
4. **A PhysiBoSS2 or continuous/spatial layer** for the 36 geometry-bound
   results. This is a change of model class, not an extension.
5. **Resolving PAEP's outlet.** The published Methods say "epithelial channel";
   the repository still records it as unverified.
