# These data do not establish a measured prior for `E_KLF12_HIGH`

Status: state-estimation result, 2026-09-14. Pre-registered in
[`klf12_prior_preregistration.md`](klf12_prior_preregistration.md) before any
KLF12 value was read; that document is a separate, earlier commit and its digest
is pinned in the artifact below. No Boolean rule was changed, no baseline was
rewritten, and no external asset was promoted.

**Decision: `CONDITIONAL_GO`** — with the qualification §1 develops, that the
pre-registration does **not** uniquely determine a branch. Two of its criteria
admit more than one defensible reading, and crossing them reaches `GO`,
`CONDITIONAL_GO` and `NO_GO` alike; the whole grid is committed as
`decision_under_each_reading_pair`. `CONDITIONAL_GO` is the cell that actually
governed what was done, and under it conditioning may be run *only* as a
labelled arbitrary-threshold sensitivity analysis. It was, and this document
reports both halves: why no defensible prior could be measured, and what putting
a number in anyway does to the model. **Nothing was activated under any cell of
the grid**, which is what makes the ambiguity disclosable rather than
disqualifying.

## Summary

| Question | Answer |
|---|---|
| Can `E_KLF12_HIGH` be given a **measured** prior from these data? | **No.** Not "no high state exists" — no *biologically interpretable* high/low boundary comes out of a one-molecule measurement. |
| Is that a limitation of the assay or of the model? | Not the model's: §1 is the assay, §2 is the absence of a reference population. |
| Was the pre-registered M1(a) criterion the one applied? | **No.** The applied rule is a post-hoc conservative reading; two readings closer to the frozen wording would have *passed* M1(a). All three are reported. |
| Does the conclusion depend on which reading is taken? | **No**, and that is what settles it: all three M1(a) readings — and M1(b) — certify a population simulated with no latent state, 25 of 25. (The calibration covers M1(a) and M1(b); not M1(c) or the falsifiers.) |
| Does the pre-registration determine a single decision branch? | **No.** M1(a) and F3 each admit two or more readings, and the six combinations reach `GO`, `CONDITIONAL_GO` and `NO_GO`. The grid is committed; nothing was activated under any cell. |
| Did the raw-UMI sensitivity change the answer? | **No** (§1a). On integer counts **65.5% of detected cells carry exactly one UMI** and the median detected value is one molecule in every unit. No latent-state model is fitted there, deliberately — see §1a. |
| Is the donor x condition estimate at least *identified*? | **No** — its sign depends on which nuisance variable is adjusted for. |
| Does conditioning change the model? | Yes, and exactly linearly. The conditioned node itself moves in **all six** arms; downstream movement reaches **two** — `hormone_treated` (9 nodes) and `hormone_treated_maternal` (8) — and no endpoint moves in the other four. |
| Is anything now validated, conditioned or activated? | **No.** |

## What was used

| | |
|---|---|
| Source | `E-MTAB-15842`, `seurat_object.rds`, sha256 `504a674d…89a1a`, re-verified in full by `pixi run verify-scrna-object` |
| Primary layer | `counts` — decontX-corrected and **not** raw UMIs |
| Sensitivity layer (§1a) | the same accession's per-sample `filtered_feature_bc_matrix` raw integer UMIs, joined by barcode, with their own digests |
| Population | union of the four epithelial `celltype_v2` labels: 20,441 of 28,212 cells |
| Unit | donor x condition; 3 donors (`SZ09`, `SZ10`, `SZ25`) x (`CNT`, `HT`) |
| Artifacts | [`klf12_state_evidence.tsv`](klf12_state_evidence.tsv), [`klf12_state_findings.json`](klf12_state_findings.json), [`klf12_raw_umi_evidence.tsv`](klf12_raw_umi_evidence.tsv), [`klf12_raw_umi_findings.json`](klf12_raw_umi_findings.json) |

**The per-cell table was re-derived from the object rather than trusted.** The
committed provenance chain checks two digests — that the extraction's recorded
`rds_sha256` is the one `config/external_data_manifest.tsv` declares for
`EXT-SCRNA-001`, and that the per-cell table still hashes to what its sidecar
records. That is an integrity chain: it proves the table has not changed since
extraction and that *an* extraction named the right object. It does not by
itself prove the table came out of those bytes. So the extraction was re-run
from the hashed RDS with R 4.5.3 and SeuratObject 5.4.0, and the result is
**byte-identical** to the committed table, sha256
`9a566014d5f645e21ca6ca68c7a1f41cd8c103799197979fbe2a62b1ee6471d3`. The binding
is reproducible, not merely consistent.

The population definition is the pre-registration's and was fixed before any
KLF12 value was read. It behaves: `EPCAM` is detected in 98.6% of the cells it
selects against 54.6% outside, `PTPRC` in 0.26% against 3.3%, `VIM` in 48.2%
against 97.4%. It is also close to condition-balanced in *share* — 73.2% of CNT
cells and 70.9% of HT cells — which is the property that made the union usable
where no single label is. Its *composition* is another matter, and §3 is about
that.

The unit is the donor, as `config/preprocessing_contract.yaml` already declared.
The 20,441 cells are not 20,441 observations, no interval over cells is reported
anywhere here, and with three donors no across-donor inferential statistic is
computed at all.

## 1. KLF12 is a one-molecule measurement, and no interpretable high/low boundary comes out of it

83.2% of epithelial cells carry no KLF12. Of the 3,429 that do, **84.2% carry
under two transcript-equivalents**, and the median detected value is 0.95.

| detected KLF12 | value |
|---|---|
| minimum | 4.5e-15 |
| 25th percentile | 0.88 |
| median | **0.95** |
| 75th percentile | 1.85 |
| 95th percentile | 3.90 |
| maximum | 24.49 |

**M1 was fitted, not assumed to fail.** A two-component Gaussian mixture on the
3,429 detected values (log scale, zeros excluded — including them would hand one
component to the dropout spike and return the detection limit as a "boundary",
which is exactly what M1(a) forbids) converges to components at 0.91 and 1.69
transcript-equivalents, and its density *is* formally bimodal. It still fails
M1(a), for a reason the fit itself makes visible:

> **it proposes no ordered boundary at all.** The two components have very
> different widths (log-sd 0.06 against 1.09), so the narrow one sits *inside*
> the broad one. The posterior crosses 0.5 at **two** points — 0.78 and 1.06
> transcript-equivalents — and the broad "high" component owns **both** tails:
> a cell is assigned high *below* 0.78 as well as *above* 1.06.

**That verdict depends on a rule that was NOT pre-registered, and the dependence
is the finding.** The frozen sentence is short enough to quote whole:

> **(a)** the implied boundary falls in a genuine density valley, not inside
> the zero spike

It names no posterior crossing, no count of crossings and no ordering
requirement. Everything the paragraph above does beyond it — counting crossings,
demanding exactly one, demanding it lie between the component means, demanding
it lie inside the fitted data's support — was chosen *after* these values were
read. It is a defensible and deliberately conservative operationalisation. It is
**not** a pre-registered criterion, it is labelled
`m1_a_rule_provenance: post_hoc_operationalisation` in the artifact, and it is
not the only reading a careful reader could take. Three survive:

| reading of frozen M1(a) | boundary it proposes | M1(a) |
|---|---:|---|
| `implemented` — exactly one crossing inside the fitted support, between the means | none exists | **fails** |
| `interior_only` — the crossing between the means, ignoring those outside | 1.058 | **passes** |
| `density_valley` — the literal sentence: the boundary *is* the density minimum | 1.168 | **passes** |

All three are in `m1_a_under_each_reading`. Two of the three pass, and the
closest of them to the frozen wording — the boundary *is* the valley — is the
most permissive. Reporting only the implemented rule's verdict, as an earlier
revision of this document did, would have presented a post-hoc conservative
choice as though the pre-registration had compelled it.

**What settles it is not the wording but the estimator.** The question "which
reading is right" has no good answer, and it does not need one, because all
three readings fail the same prior test: *does this criterion distinguish a
population that has a KLF12-high state from one that does not?*

`m1_a_specificity_calibration` answers that directly. It builds a population
with **no latent state at all** — one homogeneous Poisson rate per unit of
sequencing depth, calibrated to reproduce this object's detection fraction at
this object's per-cell depths, pushed through the same integer lattice and the
same decontX-like shrinkage (mean 0.905, sd 0.109, both measured here) — and
runs the identical fit and the identical three readings over it. In **25 of 25**
replicates:

> every one of the three readings certifies the stateless null, and proposes a
> boundary above one transcript-equivalent while doing so (median 1.26 for the
> implemented and interior-only readings, 1.32 for the valley reading).

Including the conservative implemented rule. M1(b) passes on the null too, in
every replicate. **A criterion that fires on data built with no state in it is
not measuring a state**, so no reading of M1(a) can support a measured prior
here, and the fact that the implemented one happens to vote "fail" on the real
data is not evidence either — it votes "pass" on the null. The negative
conclusion therefore does not rest on the choice of rule, which is the only
reason it is safe to report at all.

**What this calibration does *not* establish, stated because the distinction is
easy to slide past.** It covers M1(a) under all three readings and M1(b). It
does **not** cover M1(c) — which needs per-cell depths tied to the simulated
assignment — nor F1, F2 or F3, which need per-unit donor, condition and subtype
structure this null does not model. So the supported claim is "the M1(a)
criterion has no specificity at this lattice resolution", **not** "the whole
pre-registered battery would pass on stateless data". The artifact says so in
`covers` and `does_not_cover` rather than leaving the scope to be inferred.
Likewise, the conclusion is that these data do not yield a biologically
interpretable KLF12-high boundary — not the broader claim that no latent-state
model of any kind is identifiable in principle.

The failure is scoped, not universal: widen the shrinkage noise by half again
and the false passes stop (`false_pass_under_widened_shrinkage_noise`, 0 of 12
at x1.5 and x2). The rule is fooled by a lattice it can *see*. These data sit
squarely in the regime where it can.

**Why the fit does this is visible in one number.** The "low" component has a
log-sd of **0.06** — a spread of ±6%. It is not a low state; it is a spike on a
single lattice point: `log_sd_low` is 0.0618, so its ±3-sd band spans
[0.755, 1.093] — a factor of 1.45 end to end, around one molecule. The two posterior crossings, 0.777 and 1.058, are almost exactly
that spike's ±2.5-sd shoulders. What the mixture has separated is *cells at one
molecule* from *cells not at one molecule* — and the "high" component it builds
out of the remainder contains **351 cells below the lower crossing** alongside
1,177 above the upper one (`high_component_below_lower_crossing`,
`high_component_above_upper_crossing`). "High" here is not "more KLF12".

**The support definition does not decide this, and was checked rather than
assumed.** "Inside the fitted data's support" is computed over the observed
minimum of the detected values, and that minimum is 4.5e-15. That number is not
an abundance. The raw layer identifies that cell and commits it as
`cross_layer_corrected_vs_raw.minimum_corrected_cell`: it captured **one** KLF12
UMI at a raw depth of 9,095, essentially all of which decontX attributed to
ambient contamination. So the floor of the support is set by how hard the correction
pushed on one cell — a property of the correction, not a measurement of how much
KLF12 that cell had, and not something a biological conclusion may rest on.
Recomputing the same test over the central 98% of the detected values leaves
both crossings inside (`support_definition_changes_m1_a: false`); the lower
crossing at 0.777 has 351 detected cells below it, a tenth of the detected
population, so it is interior to the data on any reasonable definition. The
numeric floor is allowed to stand only because it changes nothing.

**F2 does not fire, and it is now evaluated on what was written.** F2 was
pre-registered as a statement about the *shape* of the distribution — "a zero
spike plus a monotone decreasing tail with no valley". An earlier revision
computed `F2 = not M1(a)`, which is a different claim; a later one decided it
from the *fitted* two-component density, which is also a different claim — a
fitted Gaussian pair cannot see the zero spike the sentence names, never tests
monotonicity, and can be unimodal over a histogram that plainly is not. F2 is
now read off the empirical histogram the report itself publishes: the tail is
**not** monotone decreasing (it rises to the one-molecule mode) and carries
eight interior modes, so F2 is silent — `F2_basis:
empirical_histogram_of_detected_values`, with the fitted-density test retained
beside it as `F2_fitted_density_proxy`, labelled as the proxy it was. Both agree
here. Nothing downstream turns on it in any case: the pre-registered decision
rule routes **CONDITIONAL-GO** through "M1 fails and F1 and F3 do not fire", and
F2 appears in neither the CONDITIONAL-GO nor the NO-GO condition.

**What the multimodality actually is.** The committed histogram of the detected
values (`detected_log_histogram`, 40 bins over the central 99% of the range)
has eight modes, and they sit at

| mode | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| transcript-equivalents | 0.57 | **0.97** | **1.91** | **2.79** | **3.77** | **4.72** | **5.92** | **6.88** |

— one, two, three, four, five, six and seven molecules, plus one mode below a
molecule. **The structure in this distribution is the integer UMI lattice
showing through the correction, not two biological states.** That is why a
two-component fit reports "bimodal", and why bimodality alone was never a
sufficient criterion.

**The sub-one mode is not what an earlier revision said it was**, and §1a
settles it against the raw counts rather than by argument. That revision called
those values "the correction's residue of cells that carried no molecule". They
are nothing of the kind: every one of the 2,251 epithelial cells with a
corrected value strictly between 0 and 1 carried at least one raw KLF12 UMI, and
2,247 of them carried exactly one. None carried zero. decontX subtracts an
ambient fraction from a real capture; it never zeroes a detected gene and never
creates one, which is why both layers report the identical zero fraction to
twelve places. The `ONE_TRANSCRIPT` constant survives that correction — one
molecule is still the smallest difference the assay can report — but the reason
given for it did not, and it is now stated from the raw layer instead.

What this distribution does support is a statement about the *measurement*: what
differs between these cells is how many KLF12 molecules were captured, and for
84.2% of the cells where anything was captured at all that number is one or two.
Whether the underlying transcription differs is a question this assay does not
reach; capture is not abundance, and the sentence is deliberately about the
former.

This is not a subtlety of the mixture fit. At this sequencing depth the
measurement in front of us is *"was a molecule of KLF12 seen in this cell"*. A
gene observed at nought, one or two molecules cannot distinguish a high state
from a low one *in these data*; it can only distinguish expressing from
not-expressing, and the pre-registration declared in advance that those are not
the same thing. That is a limit of this measurement, not a demonstration that no
KLF12-high state exists in this tissue — a claim the assay is not powered to
make in either direction. For contrast, in the same cells `LIF` — the gene
`E_KLF12_HIGH` exists in the model to repress — is detected in 79.4% of
epithelial cells. The regulator is the half
of this edge the assay cannot carry.

**M1(b) and M1(c) both pass, and M1 fails only under the implemented reading of
(a).** That is worth stating
plainly rather than burying: the high component excludes 55.4% of the cells M0
would call high (clearing a **post-hoc** 50% bar the pre-registration did not
set), and the two components' median sequencing depths differ by a factor of
only 1.20 (clearing a **post-hoc** 1.5 bar). Both bars were chosen after the
data existed and are labelled as such in the code. M1(c) is computed over the
fit's **own posterior assignment**, not over a cut on expression — with the
broad component owning both tails no threshold reproduces that assignment, and
an earlier revision of this repair used the 1.17 valley as a cut and so measured
a different partition than the one M1(c) names.

**M1(c)'s pooled ratio is the wrong stratum, and the post-hoc bar is not what
carries it.** Median depth differs 5x *between* units here — `SZ25TE_HT` at
~62,000 against ~12,000 elsewhere — so a pooled high-versus-low depth ratio is
partly a comparison of samples. The claim M1(c) makes is a within-unit one, so
it is now computed within each unit too (`m1_c_depth_ratio_per_unit`):

| unit | SZ09TE_CNT | SZ09TE_HT | SZ10TE_CNT | SZ10TE_HT | SZ25TE_CNT | SZ25TE_HT |
|---|---:|---:|---:|---:|---:|---:|
| high/low median depth | 0.68 | 0.82 | 0.98 | 0.77 | **1.38** | 0.89 |

All six sit inside the 1.5 bar, but that is not the evidence. The evidence is
that they do not agree in *direction* — five below one, one above
(`m1_c_ratio_direction_is_consistent: false`) — so there is no monotone depth
signal for the assignment to be reading. That conclusion would survive any bar,
which is the only reason a post-hoc bar is tolerable here. What it certifies is
narrow, though: the partition M1(c) vindicates is "at one molecule" against
"not at one molecule", so passing (c) says that lattice position is not
depth-driven, not that a biological state was found. So (b) and (c) are
satisfied and **M1(a) alone decides the branch** — and, as above, M1(a) decides
it only under the implemented post-hoc reading. Under either reading closer to
the frozen wording, (a), (b) and (c) would all pass and the pre-registered rule
would route to **GO**, with `EXT-SCRNA-001` eligible for promotion.

That is worth stating as baldly as possible, because it is the reason this
document was revised: **a defensible reading of the frozen criterion would have
awarded a measured prior to a fit whose "low" component is a single lattice
point.** What stops that is not the wording but the calibration — the reading
that would have awarded it also awards it to data with no state in it. Nothing
was promoted, and nothing should have been under any reading.

**And M1(a) is not the only loose sentence.** F3 admits two readings too (§4),
and they pull the other way: under the strict reading F3 fires and the branch is
**NO_GO** whatever M1(a) says. Crossing the two ambiguities gives the grid the
artifact now commits as `decision_under_each_reading_pair`:

| | F3 permissive (shipped) | F3 strict |
|---|---|---|
| M1(a) `implemented` | **CONDITIONAL_GO** | NO_GO |
| M1(a) `interior_only` | GO | NO_GO |
| M1(a) `density_valley` | GO | NO_GO |

All three branches are reachable, so
`decision_is_uniquely_determined_by_the_preregistration` is **false**. The
shipped `decision` is the top-left cell — the combination that actually governed
what was done — and it is reported as one cell of that grid rather than as the
branch the pre-registration determines, because the pre-registration does not
determine one. **Nothing was activated under any cell**, which is the only
reason the ambiguity is disclosable rather than disqualifying.

**Two of the five sensitivity thresholds are not thresholds** — a **post-hoc**
finding, not a pre-registered one: the pre-registration declared M2 over
q in {0.75 … 0.95} and named no degeneracy criterion. Because 83.2% of
cells are zero, the pooled 75th and 80th percentiles of KLF12 are *exactly zero*:
at q75 and q80, M2 silently becomes M0, the bare detection rule the
pre-registration declared inadmissible on its own. They are recorded in the
artifact as `degenerate_thresholds` rather than dropped, because the degeneracy
is the finding. Only q85, q90 and q95 (0.78, 0.92, 1.71) are thresholds at all,
and each sits inside the one-or-two-molecule mode.

## 1a. The raw-UMI sensitivity, run because the primary analysis was not decisive

The pre-registration allows exactly one fallback layer, and only on a condition
that §1 meets:

> Sensitivity, **only if the primary analysis is not already decisive**: the raw
> per-sample `filtered_feature_bc_matrix` UMIs from the same accession, joined
> by barcode.

§1 is not decisive in the relevant sense. Its M1(a) verdict flips with the
reading of one frozen sentence, and the criterion that produces it certifies a
stateless null. That is exactly the case the fallback exists for, so it was run.
Artifacts: [`klf12_raw_umi_findings.json`](klf12_raw_umi_findings.json) and
[`klf12_raw_umi_evidence.tsv`](klf12_raw_umi_evidence.tsv), with **their own**
provenance — six per-sample matrices with their own digests. The deposited RDS
digest binds §1 and is deliberately not reused here.

**What was preserved.** The pre-declared epithelial population (imported from
the primary module, not restated), donor × condition as the unit, no
re-clustering, no condition-dependent population definition, no interval over
cells, and the same leakage boundary. The 3.0 GB of matrices (2,996,292,088
bytes, each digested over the stream that reduced it) were read and discarded,
keeping one gene row plus per-barcode totals; nothing else was retained.

**The join is complete**, which is what makes the comparison legitimate: all
28,212 object cells are present in their sample's filtered matrix, 20,441 of
them epithelial, and the two layers report the **identical** zero fraction —
0.8322489115013942 — to twelve places. decontX rescales a capture; it does not
create or destroy one.

**On integer counts the measurement is a single molecule.**

| raw KLF12 UMIs | 0 | 1 | 2 | 3 | 4 | 5–9 | ≥10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| epithelial cells | 17,012 | **2,247** | 628 | 285 | 104 | 141 | 24 |

65.5% of detected cells carry exactly one UMI and 83.8% carry two or fewer; the
median detected value is 1, the 95th percentile is 4. This is the §1 finding
without the correction in the way, and it does not depend on any mixture.

**It holds in every donor and every arm**, which is the robustness check the
pre-registration's unit definition requires — reported per unit, never pooled
into an interval over cells:

| unit | median raw depth | detection | median detected UMI | share at exactly 1 UMI |
|---|---:|---:|---:|---:|
| SZ09TE_CNT | 17,079 | 0.101 | 1 | 0.678 |
| SZ09TE_HT | 16,572 | 0.036 | 1 | 0.859 |
| SZ10TE_CNT | 15,214 | 0.155 | 1 | 0.740 |
| SZ10TE_HT | 15,455 | 0.104 | 1 | 0.774 |
| SZ25TE_CNT | 14,503 | 0.264 | 1 | 0.620 |
| SZ25TE_HT | **68,954** | 0.366 | 1 | 0.533 |

The depths here are **raw** library sizes and are deliberately not the same
quantity as §3's `median_depth_counts`, which are decontX-corrected column sums
(`SZ25TE_HT`: 68,954 raw against 61,403 corrected). Both are reported under
their own names rather than one standing in for the other.

The median detected value is one molecule in all six. `SZ25TE_HT` — sequenced
**4.04x** deeper than the next-deepest unit, and 4.04x to 4.75x deeper than the
other five — has both the highest detection and the
*lowest* share at a single molecule, which is what §3's depth argument predicts
and is the clearest statement of the problem: the thing that most moves this
measurement across units is how deeply the unit was sequenced.

**No latent-state model is fitted here, and that is a decision with a reason.**
An earlier revision of this section fitted a two-component gamma-Poisson
mixture against a single-rate model and compared them by BIC, to ask whether
the raw counts carry structure beyond one homogeneous rate. **That analysis has
been removed.** A two-component negative-binomial likelihood is multimodal;
three successive fitters — plain EM, EM with coordinate ascent, EM with a
diagonal pattern search — were each shown by explicit counterexample to return
a non-maximum, and the reported gain moved **+17.0 → +10.24 → +21.52** as the
search was hardened, with no sign of having converged. A model-selection
statistic whose value tracks how hard one looked is not evidence.

It was also never load-bearing. Everything this section concludes rests on
counts and order statistics, which need no optimiser and can be checked by
inspection. The removal is recorded in the artifact itself
(`latent_state_model: "NONE FITTED…"`) rather than left as a silent absence.

**What the counts show instead.** Thinning every cell binomially to the lowest
unit median (14,503 UMIs) and simply *recounting* the detection fraction is the
model-free form of the depth question.

**It has to be done on the cells that were actually matched, and an earlier
revision of this section got that wrong.** Thinning cannot raise a cell already
below the target, so a scheme that keeps every cell leaves an unthinned
remainder — and that remainder is wildly uneven between units, because the
target *is* `SZ25TE_CNT`'s median depth. Comparing units that way thins the deep
unit almost completely and barely touches the shallow one, which is the
opposite of holding depth constant. The per-unit table below therefore uses
`matched_cells_only`: every cell in it was above the target and was genuinely
thinned to it. What each unit gave up to get there is reported beside it.

| unit | crude detection | depth-matched | cells matched | unmatched |
|---|---:|---:|---:|---:|
| SZ09TE_CNT | 0.101 | 0.085 | 2,431 | 37.8% |
| SZ09TE_HT | 0.036 | 0.028 | 1,616 | 36.3% |
| SZ10TE_CNT | 0.155 | 0.142 | 2,232 | 46.1% |
| SZ10TE_HT | 0.104 | 0.086 | 1,574 | 43.1% |
| SZ25TE_CNT | 0.264 | 0.257 | 2,841 | **50.0%** |
| **SZ25TE_HT** | **0.366** | **0.139** | 1,346 | **4.1%** |
| **spread** | **0.330** | **0.229** | | |

`SZ25TE_HT` — sequenced **4.04×** deeper than the next-deepest unit, and
4.04–4.75× deeper across the other five — has the **highest**
crude KLF12 detection and falls to **third** once every cell it contributes is
put at the common depth, behind both `SZ25TE_CNT` (0.257) and `SZ10TE_CNT`
(0.142). Between-unit spread falls from 0.330 to 0.229.

**The part that matters is within donor `SZ25`, and it reproduces §3 on integer
counts.** Crude, that donor reads HT 0.366 against CNT 0.264 — the **+0.102**
positive contrast that §3 singles out as the one donor pointing the other way.
Depth-matched, it reads HT 0.139 against CNT 0.257, a contrast of **−0.118**.
The sign reverses. §3 reached the same reversal by direct standardisation on the
corrected layer (**−0.061**) and warned that the adjustment was extrapolating
into strata the unit barely occupies; here it falls out of counting raw
molecules after thinning, with no standardisation and no model. That two routes
with nothing in common agree on that sign is the strongest form the depth
argument takes in this document.

**Read the asymmetry in the last column before leaning on it.** `SZ25TE_CNT`
contributes only half its cells to the matched comparison and `SZ25TE_HT`
contributes almost all of its. That is unavoidable — a common depth can only be
reached from above — but it means the matched contrast is computed on a
deep-biased half of the CNT arm and on essentially all of the HT arm. It is a
better comparison than the crude one and than the mixed scheme it replaces; it
is not a randomised one.

**Conclusion of the sensitivity.** The raw layer does not rescue a measured
prior and does not contradict §1. It removes decontX as an explanation: the
median detected value is one molecule in every unit and two thirds of all
detections are a single molecule, and those are properties of the counts
themselves rather than of the correction. There is no range above the detection
event for a high/low boundary to sit in. **The current data do not justify
mapping KLF12 expression onto a measured `E_KLF12_HIGH` Boolean prior, and no
prior is activated.**

It also **corrects** §1 on one point of fact, which is recorded in §1 rather
than buried here: the sub-one corrected values are cells that captured exactly
one molecule, not cells that captured none.

That correction is a claim about **both** layers at once, so it is computed
from both rather than asserted: `cross_layer_corrected_vs_raw` tabulates the
corrected value against the raw UMI for the same 20,441 cells, under the same
two-parent binding as everything else here. It records 17,012 cells zero in
both layers and 3,429 positive in both, with **no cell positive in one and zero
in the other** — which is why the two layers report the identical detection
fraction — and of the 2,251 cells whose corrected value lies strictly between 0
and 1, 2,247 carried one raw UMI, 2 carried two, 1 carried three, 1 carried
four, and **none carried zero**.

## 2. "High" has no reference, and this repository already said so

REF-037 (Huang 2018) does not define an absolute KLF12 level. It reports KLF12
**increased in recurrent-implantation-failure endometrium relative to fertile
controls**, and that comparison is the whole content of "high". This repository
holds no RIF or fertile label for `SZ09`, `SZ10` or `SZ25`, and
`config/personalization.yaml` already declares
`reference_strategy.mode: external_reference_required` with
`reference_path: null` and the instruction *"Do not estimate PROFILE-style
reference distributions from the three currently available donors."*

So the comparative route was closed before the analysis began — **F4 was true at
writing time**, stated as such in the pre-registration, not discovered
afterwards. The within-data route (M1) was the only one left open, and §1 and
§1a between them establish that it yields no biologically interpretable
boundary on this measurement — in the corrected layer or the raw one.

## 3. The per-unit estimate is not identified either

This is the finding the pre-registration named as a risk but did not enumerate
as a falsifier, and it is stated here as **post-hoc**.

Take the estimate at face value — the fraction of epithelial cells with any
KLF12 — and the six units read 0.036 to 0.366, a ten-fold range. Two things
confound it, both adjustable, and the two adjustments disagree about the sign of
the HT-versus-CNT difference:

| donor | crude HT − CNT | depth-standardised | subtype-standardised |
|---|---:|---:|---:|
| SZ09 | −0.065 | −0.065 | −0.057 |
| SZ10 | −0.051 | −0.048 | −0.001 |
| SZ25 | **+0.102** | −0.061 | **+0.161** |
| sign set | {−, +} | {−} | {−, +} |

Sign sets are the artifact's `condition_contrast_sign_sets`. `SZ10`'s
subtype-standardised value is −0.0008: negative by arithmetic, and better read
as no difference at all. The table carries the magnitude so the reader is not
left with the sign alone.

**Depth.** `SZ25TE_HT` was sequenced to a median depth of 61,403 against
11,692–13,511 for every other unit — 4.5x to 5.3x — with a median 8,455 genes
detected against 4,378–4,807. It is also the unit with the highest crude KLF12
detection. In all six units the top depth quartile detects KLF12 more often than
the bottom, though the intermediate quartiles are not monotone in `SZ09TE_HT` or
`SZ25TE_HT`. So the crude comparison is partly a library-size comparison. Adjusting for depth is what makes
the three donors agree — and it makes them agree by overturning `SZ25`, the one
donor whose crude contrast pointed the other way.

**Subtype composition.** The four epithelial labels are near-disjoint between
arms: CNT units are 53–74% `Luminal-like epithelium`, HT units 0.7–1.4%. And
KLF12 detection differs sharply between labels (`Cycling` 0.24 in CNT,
`HT epithelium II` 0.04). So most of the crude contrast is a relabelling. But
adjusting for subtype partly removes the condition itself, because three of the
four labels are ~80% one arm — the circularity the observability map warned
about. That adjustment leaves the donors disagreeing, `SZ25` strongly positive.

**Neither adjustment is trustworthy, and a cell count alone understates how
badly.** What matters is not only how few cells the thinnest stratum holds but
how much of the answer it decides — direct standardisation weights every unit by
the *pooled* mix, so a stratum can be both tiny and load-bearing. Both numbers
are columns in `klf12_state_evidence.tsv`:

| unit | thinnest depth stratum | its weight | thinnest subtype stratum | its weight |
|---|---:|---:|---:|---:|
| SZ09TE_CNT | 641 | 0.200 | **3** | **0.205** |
| SZ09TE_HT | 268 | 0.200 | **19** | **0.433** |
| SZ10TE_CNT | 494 | 0.200 | 42 | 0.170 |
| SZ10TE_HT | 215 | 0.200 | **38** | **0.433** |
| SZ25TE_CNT | 754 | 0.200 | 473 | 0.205 |
| SZ25TE_HT | **14** | **0.200** | **14** | **0.433** |

Every HT unit's subtype-standardised rate is thus 43% a rate measured on 14–38
cells, and the `+0.161` that makes `SZ25`'s sign flip is carried by 14 Luminal
cells. `SZ25TE_HT`'s depth-standardised rate puts a fifth of its weight on 14
cells, because its depth distribution (median 61,403) barely overlaps the pooled
quintiles it is standardised to.

That is worse than imprecision. Both adjustments violate positivity: the
epithelial labels are near-disjoint across arms, and `SZ25TE_HT`'s depths are
nearly disjoint from every other unit's, so a directly standardised contrast here
extrapolates into strata a unit barely occupies. `_standardise` returns nothing
where a unit misses a stratum outright, but its effective threshold is one cell,
which is not a safeguard. **"Sign undetermined" is the conservative reading;
"neither adjusted contrast estimates a well-defined quantity" is the accurate
one.**

The honest statement is therefore stronger than "no threshold exists": **with
these data the direction of the HT-versus-CNT difference in epithelial KLF12 is
not determined**,
and a conditioning scheme that encoded one would be encoding an analyst's choice
of nuisance adjustment.

## 4. F1 and F3 did not fire, and are reported as they were written

Discipline matters more here than a tidier story, so both are reported by the
letter of the pre-registration rather than reinterpreted to agree with §3.

- **F1 (depth confounding)** was operationalised as a within-unit top-versus-bottom
  depth-quartile detection ratio above 2 in a *majority* of units. It reaches
  that in **3 of 6** — not a majority — so **F1 does not fire**. The ratio is
  above 1 in all six and reaches 6.5 in `SZ25TE_CNT`, and the *between*-unit depth
  problem in §3 is a different quantity that F1 was not written to catch.
- **F3 (threshold dominance)** compares each unit's across-q width with the
  largest across-unit spread at a fixed q. The widths are 0.032–0.220 against a
  spread of 0.330, so **F3 does not fire**.

  **The pre-registered sentence admits two readings and this matters, so both
  are in the artifact.** "The largest across-unit difference at any fixed q"
  parses most naturally as the *maximum* over q — 0.330 — and that is the
  reading the decision follows. Read instead as "exceeds, at any fixed q, the
  across-unit difference", the bar is the *minimum* over q, 0.141, which both
  `SZ25TE_CNT` (0.166) and `SZ25TE_HT` (0.220) clear: **F3 would fire and the
  decision would be NO_GO.** `F3_threshold_dominance_strict_reading` records
  this. The permissive reading is the one that licenses running the sweep, so
  it is disclosed rather than left to the parse; nothing was activated under
  either, and §5's conclusion is negative under both.

That combination — M1 failed, F1 and F3 silent — is exactly the
`CONDITIONAL_GO` branch, and it is the branch that was taken.

## 5. What conditioning actually does

Run as declared: an arbitrary-threshold sensitivity sweep, converged horizon,
20,000 trajectories, five seeds, the same six arms the concordance build
simulates. Artifacts:
[`klf12_conditioning_response.tsv`](klf12_conditioning_response.tsv) and
[`klf12_conditioning_settings.json`](klf12_conditioning_settings.json).

**How the prior enters.** One `.istate` line, on a free variable, **substituted
for** `baseline.cfg`'s plain `E_KLF12_HIGH.istate = FALSE;` in the configuration
the runner already assembles — not appended, for the reason the next paragraph
gives. No rule is edited and
`baseline.cfg` is untouched. Two mechanical points are worth recording because
both were live failure modes:

- MaBoSS takes a probabilistic initial state only in the bracketed form
  `[E_KLF12_HIGH].istate = …`, which does *not* share a merge key with
  `baseline.cfg`'s plain `E_KLF12_HIGH.istate = FALSE;`. Adding it leaves both
  lines, and the engine **refuses** with `duplicate node istate declaration`
  rather than silently picking one. The implementation therefore replaces the
  line and asserts it replaced exactly one.
- The prior is re-applied at *every* phase of every protocol in the chain.
  `E_KLF12_HIGH` is not in `minimal_stable_joint`, the superset's default memory
  policy, so a phase that did not carry it would fall back to `FALSE` and the
  chain would report an unconditioned model under a conditioned label. Note the
  related asymmetry: `E_LIF`, `E_GP130_STAT3` and `E_RECEPTIVE_SURFACE` *are*
  memory nodes, so at each phase boundary the prior's consequences arrive from
  memory while the prior itself is re-drawn independently, briefly breaking the
  correlation between them. At the converged horizon read here that is
  immaterial — `E_KLF12_HIGH` has logic `E_KLF12_HIGH` and never moves — but at a
  declared horizon it would not be.

**The result is exactly linear, and that is the whole of it** — but the reason
is narrower than it first looks, and an earlier draft of this section got it
wrong. `E_KLF12_HIGH` never changes *within* a phase, so within one phase the
ensemble does split into two sub-ensembles that never mix. Across a chain it
does not: the prior is re-drawn at each of the four or five phases, so a priori
the endpoint is a polynomial in the prior, not a line. What makes it a line is
the **converged horizon** — each phase reaches its fixed point, so the endpoint
depends on the final phase's draw alone and every earlier draw is erased. The
linearity below is therefore an observed property of the converged readings, not
a theorem about the chain, and it would not be expected to hold at a declared
horizon. With that qualification, every reported occupancy is the weighted
average of the two extremes:

> value(p) = (1 − p) · value(0) + p · value(1)

Every one of the 286 rows of the response table is checked against that law,
with no node exempted. Two qualifications keep the check honest. 156 of those
rows sit at p = 0 or p = 1, where the deviation is zero *by construction* —
those are the two anchors the prediction is built from — and of the 130 rows at
interior priors, 67 have the two anchors equal, where the law is satisfied
trivially. **63 rows carry evidential content**, and over the whole table the
largest deviation is 6.0e-4.

That residual is **not** across-seed noise, and a reader checking it against the
artifact's `node_sd_across_seeds` column (maximum 1.0e-4) would rightly object.
The explanation is visible in the table: `E_KLF12_HIGH` reads back 0.100050 at a
requested 0.1 and 0.366150 at a requested 0.366097, with an across-seed
deviation of exactly zero at every prior. The engine assigns a **deterministic**
number of trajectories to each initial state — 2001 and 7323 of 20,000 — rather
than sampling it, which is why the seeds agree exactly and why the realised
prior is not the requested one. Three such deterministic splits (this node and
two interface relays) are specified independently and cannot factorise exactly
over a finite ensemble, and 6.0e-4 x 20,000 is **twelve trajectories**. The
residual is that discretisation. `node_sd_across_seeds` measures something else
entirely and bounds neither it nor the initial-state assignment. The interesting consequence is negative: **conditioning
`E_KLF12_HIGH` adds no shape.** It interpolates between two runs that were
already available. A sweep that produced a curve would have said something about
the model; a straight line says the node is a multiplicative gate.

**The executable route, traced rather than narrated.** `E_KLF12_HIGH` gates
exactly one rule — `E_LIF = E_SECRETORY_STATE and not E_KLF12_HIGH` — and
everything downstream follows from that one edge:

```
E_KLF12_HIGH ─┤ E_LIF → E_GP130_STAT3 → E_RECEPTIVE_SURFACE ─┬→ OUT_EPITHELIAL_RECEPTIVE
                                        │                    ├→ X_ADHESION_ROUTE_SPP1
                                        └→ E_CD98_CD9        └→ X_ADHESION_ROUTE_REDUNDANT
                                                                      ↓
                                              OUT_MATERNAL_ADHESION_COMPETENCE → OUT_STABLE_ADHESION
```

Ten tracked quantities move in the hormone-treated arm — the conditioned node
and nine downstream of it — and three do not. The instructive non-mover is
`E_ITGAVB3_5`, whose rule is `E_LIF or E_HBEGF or E_SECRETORY_STATE`: shutting
the LIF gate leaves the `E_SECRETORY_STATE` disjunct standing, so integrin
occupancy is flat at 1.000 at every prior including p = 1. `X_ANTIADHESIVE_ROUTE`
is flat at 0.000 because its own inputs are off in this arm, and
`OUT_STROMAL_DECIDUALIZED` because no path reaches it at all. In the four arms
whose endpoints are already zero — `untreated`, `mifepristone`,
`basal_maternal`, `e2_primed_maternal` — the *only* thing that moves is
`E_KLF12_HIGH` itself.

Which quantities move, at the largest data-derived candidate p = 0.366:

| arm | quantity | p = 0 | p = 0.366 | p = 1 |
|---|---|---:|---:|---:|
| `hormone_treated` | `E_LIF`, `E_GP130_STAT3`, `E_RECEPTIVE_SURFACE`, `E_CD98_CD9` | 1.000 | 0.634 | 0.000 |
| `hormone_treated` | `X_ADHESION_ROUTE_SPP1` | 0.700 | 0.443 | 0.000 |
| `hormone_treated` | `X_ADHESION_ROUTE_REDUNDANT` | 0.400 | 0.253 | 0.000 |
| `hormone_treated` | `OUT_EPITHELIAL_RECEPTIVE` | 1.000 | 0.634 | 0.000 |
| `hormone_treated` | `OUT_MATERNAL_ADHESION_COMPETENCE` | 0.820 | 0.520 | 0.000 |
| `hormone_treated` | `OUT_STABLE_ADHESION` | 0.820 | 0.520 | 0.000 |
| `hormone_treated` | `E_ITGAVB3_5` | 1.000 | 1.000 | 1.000 |
| `hormone_treated` | `OUT_STROMAL_DECIDUALIZED` | 1.000 | 1.000 | 1.000 |
| `hormone_treated` | `X_ANTIADHESIVE_ROUTE` | 0.000 | 0.000 | 0.000 |
| `hormone_treated_maternal` | `OUT_EPITHELIAL_RECEPTIVE` | 1.000 | 0.634 | 0.000 |
| `hormone_treated_maternal` | `OUT_MATERNAL_ADHESION_COMPETENCE` | 0.820 | 0.520 | 0.000 |
| `hormone_treated_maternal` | `OUT_STABLE_ADHESION` | 0.000 | 0.000 | 0.000 |
| `untreated`, `mifepristone`, `basal_maternal`, `e2_primed_maternal` | every output | 0.000 | 0.000 | 0.000 |

`hormone_treated_maternal`'s `OUT_STABLE_ADHESION` is **recorded as zero**, not
absent: that arm carries no embryo, so the endpoint is structurally off, and the
row says so rather than leaving a gap. Its maternal competence does move, which
is the second arm the conditioning reaches.

The p = 0 rows reproduce the tracked concordance values — `OUT_STABLE_ADHESION`
0.8203 here against 0.8201 in `docs/concordance/run_settings.json` — which is how
the sweep is tied to the existing record rather than being a second, differently
configured simulation of the same model.

**Sensitivity to the state model.** The 30 candidate priors — six units x five
quantiles — span 0.0047 to 0.3661, a 77-fold range. Note where each end comes
from. The maximum is `SZ25TE_HT` at q75 or q80, and those are the two
*degenerate* thresholds, so the top of the range is the bare detection fraction:
M0, which §1 showed is the same measurement as "any KLF12 at all", and which the
pre-registration declared the upper bound on any threshold-based estimate rather
than an estimate in its own right. The minimum is `SZ09TE_HT` at q95. Over the
three non-degenerate quantiles alone the range is 0.0047 to 0.3376, which is
barely narrower.

Through the linear law, that is `OUT_STABLE_ADHESION` anywhere from 0.816 to
0.520 in the hormone-treated arm. The spread is not measurement error around a
value; it is the range of an undetermined parameter, and no part of it is
preferred by the evidence.

## 6. What this is not

- **Not validation.** These are the study's own cells; the row stays
  `same_dataset_internal`.
- **Not a conditioned digital twin.** No defensible measured prior could be
  established, so nothing was conditioned on a measurement.
- **Not a demonstration that KLF12-high does not occur.** The negative result is
  about what this assay can identify, not about the tissue. A one-molecule
  measurement cannot exclude a high state any more than it can establish one,
  and §1a shows that is a property of the counts and not of decontX.
- **Not calibrated adhesion probability.** `OUT_STABLE_ADHESION` is a simulated
  trajectory frequency under stated rules and hand-set rates. Its unconditioned
  value of 0.820 is, as `docs/identifiability_analysis.md` shows, arithmetic on
  two typed-in relay probabilities.
- **Not evidence about KLF12.** A moved occupancy is the model's rules restating
  themselves, not causal support for KLF12 in implantation.
- **Not an activation.** `EXT-SCRNA-001` stays
  `structurally_verified_not_integrated` and `SC-011` stays `provisional`. The
  object being on a local disk licenses nothing, and `active_diagnostic` in this
  repository means a directional constraint evaluated every run, which this is
  not.
- **Not a fix for the horizon problem.** Every reading here is converged; the
  declared-horizon and continuation-semantics questions are untouched.

## 7. What would lift this

In order of how much it would buy:

1. **A reference population for "high".** Endometrial epithelium from donors
   with a known implantation phenotype, processed comparably. This is what
   REF-037's definition requires and what `config/personalization.yaml` is
   already waiting for. Without it, "high KLF12" has no referent in this
   repository whatever the sequencing depth.
2. **A KLF12 measurement with dynamic range.** Targeted RNA quantification,
   protein, or single-cell data deep enough that KLF12 is not a one-molecule
   event — deep enough, specifically, that the integer lattice in §1 stops being
   the dominant structure in the distribution. Deeper sequencing alone would
   sharpen §1 but not §2.
3. ~~**A depth-matched or raw-UMI re-derivation.**~~ **Done — see §1a**, and it
   did not lift this. The raw matrices were joined by barcode and the cells
   thinned to a common depth; the result is counts and order statistics, with
   **no latent-state model fitted** (`latent_state_model: "NONE FITTED…"`). The
   answer is unchanged and the reason is now attributable to the counts rather
   than to the correction. This line is kept struck through rather than deleted
   so the record shows a proposed remedy that was carried out and failed, not a
   remedy still outstanding.

Explicitly *not* on this list: more analysis of these 28,212 cells. The
ambiguity in §1 and §3 is a property of the measurement, not of the method
applied to it.

## 8. What this means for the other 26 observable states

`E_KLF12_HIGH` was the easy case — the sole free variable, no rule change
needed, a directly measured transcript. It still did not yield a defensible
measured prior, and the way it failed is more instructive than the failure:
under one defensible reading of its own pre-registered criterion it would have
*succeeded*, on a fit that was separating molecule counts. The other 26
observable states all carry `conditioning_compatibility = rule_override_required`,
so each needs a **rule edit** before any measurement can reach it, and a rule
edit is a model change with its own evidence burden.

Five things this increment establishes that apply to all of them:

- The condition-coded `celltype_v2` labels are not an admissible stratifier for
  any HT-versus-CNT contrast. Any future conditioning needs a
  condition-independent population definition, and the union used here is a
  template.
- Depth is confounded with sample in this object, `SZ25TE_HT` acutely. Any
  per-unit summary needs a depth argument before it is believed.
- Detection is not state. Establishing that a gene *is* expressed is not
  establishing that a Boolean node is ON, and for a low-abundance regulator the
  two can be the same measurement wearing different names. The raw layer makes
  this concrete: on raw KLF12 UMIs the median detected value is **one molecule**
  in every one of the six units, so "expressed" and "high" are the same
  measurement here whatever is fitted on top of it.
- **A pre-registered criterion still has to be operationalised, and the
  operationalisation is not pre-registered.** The frozen M1(a) is one sentence;
  the rule that decided it here is four conditions, all chosen afterwards, and
  the decision branch turns on them. Any future criterion should be written with
  its operationalisation, or its readings enumerated and reported the way
  `m1_a_under_each_reading` and `decision_under_each_m1_a_reading` now are.
- **A mixture fit will find "two states" in a count lattice.** The 3,429
  detected KLF12 values are formally bimodal and the modes are the integers.
  The test this analysis applied is a **conjunction** — *exactly one posterior
  crossing inside the fitted data's support, **and** that crossing lying
  between the component means* — and it is worth stating exactly, because it
  was chosen after the data existed and an earlier revision of this document
  presented it as though the pre-registration had compelled it. It did not:
  the frozen M1(a) names no crossing at all.

  **Two readings closer to the frozen wording reverse it, and both are
  committed.** Requiring only the crossing between the means, this fit proposes
  a boundary at 1.06 transcript-equivalents and M1(a) passes; taking the
  literal sentence, where the boundary *is* the density valley, it passes at
  1.17. Both sit in `m1_a_under_each_reading` beside the implemented verdict.

  **So the reusable lesson is not the conjunction — it is the calibration.**
  All three readings certify a population simulated with no latent state, 25
  times out of 25, and propose a boundary above one molecule while doing it.
  Any future binarisation of a low-abundance gene here should therefore be run
  against such a null before its verdict is believed:
  `klf12_state.calibrate_m1a_specificity` is the reusable part, and
  `fit_two_component_mixture` with the `ONE_TRANSCRIPT` check is what it
  calibrates. A criterion not yet shown to fail on stateless data is not yet
  evidence of a state.

The observability map's central finding stands and is unaffected: 27 states have
some observability but v0.4 compresses them into 9 native signatures, and that
remains a representational deficit in the rules rather than a ceiling on the
assay.
