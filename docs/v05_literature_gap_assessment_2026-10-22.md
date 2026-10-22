# Literature gap assessment — 2026-10-22

**Status:** read-only scientific assessment, submitted for owner approval.
**Scope:** Phase B of the 2026-10-22 continuation request. This is **not** a
re-run of the 147-paper screen or of the 31-candidate reconciliation.
**Authoring:** AI-assisted session.

> **Nothing here changes U1's registration scope.** Two papers read below are new
> to the corpus and are registered nowhere. Adding them is an owner decision, not
> a consequence of having read them (§5).

---

## 1. Corpus state at the time of this assessment

**Re-checked 2026-10-22 evening; the folder changed again and the changes are
recorded here.** 183 PDF files hold **165 distinct digests**, against 168
reconciliation rows after this refresh. Four kinds of change:

| change | count | handling |
|---|---|---|
| files renamed to carry a year | 4 | `relative_path` updated; same digests, same articles |
| copies duplicated from `prl_igfbp1_foxo1/` to the top level | 19 digests | recorded in `duplicate_group`; no new evidence |
| articles absent from the reconciliation | 3 | rows added with digest, path and DOI |
| **a recorded file replaced on disk** | **1** | **see below** |

**The replaced file is a canonical-provenance break and the second of its kind.**
`PDF-034`, Lin 2026 on the glandular secretome, content-addresses digest
`72e79cdf2616…` at 24 pages. **That file is gone**, replaced by a 25-page
rendering `06f2ee99a2e8…`. The canonical row now addresses a file nobody holds,
exactly as `PDF-048` does. The replacement is stamped *"This is the Pre-Published
Version."*, so `publication_status = accepted_unedited` stays correct and the row
**must not** be flipped to `version_of_record`: doing so would break three
canonical tests at once. The row is left untouched and the break is recorded.

**The replacement was read in full, and it changes no conclusion.** CST3 appears
**zero times** in Lin 2026, so §3's statement that Lin never measures CST3 is now
verified against the complete text rather than inferred. WNT7A and CSF1 appear as
recorded.

| file | SHA-256 | DOI | read |
|---|---|---|---|
| Fitzgerald 2023, basolateral secretions | `dc932744d4a2a9ff587f9a9fc8268721c190427175d57829073b5626c4abd260` | `10.1093/molehr/gaad007` | §3 |
| Zhou 2026, dynamin-2 | `da39f3706cc3e705894fedcf745f32019cbcd32f9bfc64732b291af2ddce6308` | `10.1093/reprod/xaag120` | §4 |
| Lin 2026, replacement rendering | `06f2ee99a2e8d9ce…` | `10.1093/jmcb/mjag023` | §1, CST3 check |

**The second closes the one outstanding full-text request** recorded in
`docs/v05_external_review_delta_2026-10-22.md` §2.1 item 2. That request is now
discharged, and the answer is negative (§4).

---

## 2. B1 — HBP1, SOX4 and the three PGR layers

Both papers were read at figure level from the local PDFs.

### 2.1 What the experiments genuinely support

**They do separate PGR protein abundance from PGR transcriptional activity, and
the separation is measured rather than inferred.** This is the strongest result
in the Phase B set.

| layer | what regulates it | evidence | verdict |
|---|---|---|---|
| PGR **transcript** | neither factor | HBP1 knockdown leaves `PGR` mRNA unchanged (Guo Fig 4B); SOX4 knockout gives no "overt transcription reduction" (Huang Fig 5A) | **not** a regulated layer in either paper |
| PGR **protein abundance** | SOX4, post-transcriptionally | SOX4 knockout drops PRA and PRB protein on days 0, 2, 3, 6; MG-132 rescues, 3-MA does not; cycloheximide chase shows a shortened half-life; PGR ubiquitination rises (Huang Figs 5A–5F) | **supported**, with a proteasomal mechanism and three converging assays |
| PGR **transcriptional activity** | HBP1 | HBP1 knockdown leaves PGR mRNA and protein unchanged across D2–D6 while `FOSL2`, `FKBP4`, `FKBP5` and `SRC1` fall at mRNA (Guo Fig 4F) and FOSL2/FKBP4/FKBP5 at protein (Fig 4G); HBP1 overexpression raises H3K4me3 at PGR-target promoters (Fig 5D) and PGR occupancy at the `FOXO1` and `HOXA10` promoters (Figs 4H, 4I) | **supported** — same cells, same perturbation, receptor level flat and receptor output down |

**FOXO1 is supported as a regulated output of both, with different mechanisms.**
Huang establishes direct transcriptional control, with SOX4 binding the `FOXO1`
locus by ChIP-qPCR and `FOXO1` knockdown abolishing the effect of SOX4
overexpression — a real epistasis test (Huang Fig 4G–4J, Fig 4—suppl 1). Guo
reports a post-translational route instead: HBP1 knockdown raises phospho-AKT
with total AKT unchanged, the PI3K inhibitor LY294002 restores IGFBP1, and HBP1
overexpression raises **nuclear** FOXO1 (Guo Figs 3B–3D).

**IGFBP1 transcription is supported as a direct HBP1 target**: ChIP-Seq
co-occupancy of HBP1 and H3K4me3 at the `IGFBP1` promoter, with overexpression
raising peak intensity, and RNA-Seq confirming the drop on knockdown (Guo Fig 5D).

### 2.2 What they do not support

**Neither paper separates PRL from IGFBP1.** Both markers fall together on HBP1
knockdown (Guo Figs 2A, 2B) and on SOX4 knockout, and both rise on SOX4
overexpression (Huang Figs 3A–3F). **Both are therefore unifying for TI-04**, like
Tamura 2014 and Tamura 2024, and neither helps that deferral.

**Both factors are themselves progesterone-driven, and this is the decisive
structural fact.** HBP1 mRNA rises under MPA and the rise is attenuated by PGR
knockdown (Guo Fig 4A). SOX4 is induced by MPA, abolished by RU486, carries a PGR
ChIP-qPCR peak at its own promoter, and responds to PGR overexpression in a
reporter assay (Huang Figs 2A–2G). So each sits **downstream of the same
`IN_PROGESTIN` input the model already encodes**.

**Guo's independence claim is computational and internally awkward.** Its
evidence that "HBP1 operates independently" is an absence of DEG overlap between
siHBP1, siPGR and siFOXO1 in a public dataset (Suppl Fig 1). That is not a
perturbation test, and it sits oddly beside the paper's own finding that HBP1
knockdown lowers PGR target genes — which predicts overlap with siPGR. Recorded
as a tension, not used.

### 2.3 Could this break the seven-member hormone class?

The class is `{E_IHH, E_PGR, IN_PROGESTIN, S_BMP2, S_HAND2, S_NR2F2, S_PGR}`,
re-derived this session from the repository's own loader.

**The biology licenses three distinguishable layers. Whether the Boolean model
can hold them apart is a different question, and this assessment does not claim
it is answered.** The reason is concrete. Both candidate regulators are PGR-driven,
so a faithful encoding creates a feedback loop: progestin drives PGR, PGR drives
SOX4 and HBP1, and those feed back onto PGR protein and PGR activity. A loop whose
only exogenous driver is one input tends to collapse back onto that input in
Boolean form, which is exactly how the current seven-member class arose.

**So the honest status is: a candidate node family worth building and enumerating,
with a real risk that it reproduces the alias rather than breaking it.** Settling
it requires composing the candidate network and enumerating it, which is topology
work inside the 2026-09-30 pause. **No AND/OR relationship is proposed here**, and
none should be drawn from the transcriptional associations above — the task's own
constraint, and it binds.

One further caution for any future unit. Both factors also couple to the cell
cycle: HBP1 overexpression reduces proliferation and Ki67 while knockdown raises
it (Guo Figs 2G–2I), and SOX4 knockout derepresses 438 cell-cycle genes (Huang
Fig 4—suppl 2). That is the **R6 seam**, not the PGR seam, and conflating the two
would misattribute the evidence.

---

## 3. B2 — CST3 as a candidate mediator of the glandular brake

**The paper is present locally** (§1) and was read at figure level.

**What it shows.** Human endometrial epithelial organoids from **three donors**
on Transwells; the basolateral secretome by mass spectrometry; P4 and PGE2 raise
basolateral CST3, SERPINA3 and STC1. Recombinant protein was then applied to
stromal cells at 10, 100 and 1000 ng/ml. **CST3 at 1000 ng/ml only** reduced
`PRL` and `IGFBP1` mRNA against E2 + MPA (P < 0.05). SERPINA3 and STC1 did not.
None of the three induced decidualization alone.

**Sufficiency versus necessity, which the request rightly separates.** This is
**recombinant sufficiency at a single dose**, and nothing more. There is no
CST3 immunodepletion from conditioned medium, no neutralising antibody, and no
CST3 knockdown in the organoid. **So the necessity of CST3 for the effect of whole
conditioned medium is untested.**

**Does it explain Lin 2026?** Not on this evidence, and the request's caution is
the correct one. The two studies agree in **direction** — a gland-derived brake on
stromal PRL and IGFBP1 — which is more than the deferred placeholder had before.
But Lin never measures CST3, Fitzgerald never tests Lin's conditioned medium, the
hormonal contexts differ (E2 + MPA ± PGE2 here against progesterone and cAMP
there), and Lin's own proteomic candidates were WNT7A and CSF1, not CST3.

**Four limits to carry into any register row.** Only the top dose worked, which
leaves a threshold and a supraphysiological artifact equally open and makes the
dose-response uninformative; no uterine-fluid concentration is established
anywhere here, so physiological relevance is unanchored; the endpoints are
marker **mRNA** only; and n = 3 donors.

**Disposition: CST3 upgrades `X_GLAND_SECRETOME_DECID_BRAKE` from an unidentified
placeholder to a placeholder with one named candidate ligand.** It does not make
the edge molecule-specific, and it licenses no rule.

---

## 4. B3 — DNM2 does not supply an independent adhesion mechanism

The outstanding request is discharged, and the answer is negative.

**The two halves of the paper are in different systems and are never joined.**
The secretion work is in **fertile-donor organoids** with Dyngo-4a at 10 µM, and
yields 21 apical proteins down and 25 up (Fig 3). The adhesion work is **DNM2
siRNA in Ishikawa**, greater than 50 % knockdown, scored against HTR8/SVneo
spheroids (Fig 4C). **The organoids have donors and no adhesion endpoint; the
adhesion assay has an endpoint and no donors.** No experiment links altered
apical secretion to altered adhesion.

**The STAT3 and SPP1 result is weaker than the abstract implies.** It is qPCR
after the adhesion assay at **N = 6 technical replicates per group** by the
paper's own legend, not biological replicates. **There is no mediation test** — no
STAT3 or SPP1 rescue, no epistasis — so `DNM2 → STAT3/SPP1 → adhesion` remains
exactly what the external review warned it was: an association. Dyngo-4a is
additionally a **pan-dynamin** inhibitor, so DNM1 and DNM3 are not excluded.

**The decisive point for the model is upstream.** Figure 2 is titled for
**progestin-dependent induction** of DNM2. DNM2 is therefore driven by the same
stimulus the model already encodes as `E_SECRETORY_STATE`, and both of its named
downstream genes already exist in the network as `E_GP130_STAT3` and
`E_SPP1_EXPR`, each already inside an alias class.

**Disposition: an independent adhesion route is UNPROVEN here, which is not the
same as a demonstrated Boolean alias, and the two must not be conflated.** What
the paper fails to establish is independence: secretion and adhesion are measured
in different systems, the mediator chain is untested, and the inhibitor is
pan-dynamin. What it does establish is that DNM2 is progestin-induced, which
makes a `DNM2` node *expected* to land inside the nine-member epithelial
secretory class.

**That expectation has not been computed.** No candidate network containing DNM2
was composed or enumerated, so this assessment claims only that the evidence does
not license an independent route, and **not** that DNM2 is provably an alias of
`E_SECRETORY_STATE`. Proving the alias would need the same enumeration the N8
seam needs, and it is topology work inside the pause. No node, no edge, no rate.

---

## 5. B4 — the four standing contradictions, and what would settle each

For each: the competing claims, the context that differs, the discriminating
measurement, and whether any paper or dataset already holds it. **None is
resolved by majority, citation count or Boolean convenience.**

### 5.1 SETD7

**Claims.** Gain-of-function makes SETD7 deleterious for PRL and IGFBP1 (Yu);
two independent loss-of-function studies make it required (Chen, Konyushatova).
Separately, the two loss-of-function papers disagree with **each other** on
compartment and substrate: nuclear and HOXA10 against cytoplasmic and ER-α.

**Contexts that differ.** Direction of perturbation; achieved dose relative to
endogenous, which no paper measures; and subcellular fractionation, performed
only by Konyushatova.

**Discriminating measurement.** A **dose-controlled titration spanning endogenous
level** in one system, with decidual markers and an independent arrest readout,
plus matched fractionation. That tests the only reconciliation not excluded, a
non-monotonic requirement.

**Already available?** **No.** Yu only adds, the others only remove, and none
reports achieved dose against endogenous.

**Disposition: contradiction retained; the missing measurement is recorded.**

### 5.2 Human IHH

**Claims.** The committed rule `E_IHH = E_PGR` makes IHH progestin-driven. Hewitt
2022 shows robust **estrogen** induction across all three donors, and the two
atlases place IHH in the proliferative-phase basal glands.

**Context that differs.** The committed rule reads an input the human data do not
support; the progestin-attenuation term rests on **one annotated donor** in a
system whose authors call it progesterone-incompetent.

**Discriminating measurement.** A **progestin-alone arm with a protein-level IHH
readout in human epithelium**, across more donors. This is already plan §10.3
item 4, and it is load-bearing for a second reason: any corrected IHH sign turns
`S_BMP2` off in all 16,384 progestin-alone states, silently enacting the
withdrawn R4-a edit.

**Already available?** **No.** No source in this corpus applies progestin without
estrogen, Hewitt included.

**Disposition: contradiction retained. This is the single measurement that
unblocks the most, and it is already requested.**

### 5.3 MUC1

**Claims.** The committed `E_MUC1_BARRIER = ¬E_SECRETORY_STATE` says the barrier
falls as the epithelium becomes secretory. Four independent human datasets put
MUC1 **up** in the secretory state, and the one functional panel in the corpus
assigns the barrier role to **MUC16** instead.

**Context that differs.** Molecular layer. The barrier question is about
**surface glycoform and local clearance**, while the contrary data are abundance
and promoter activity. DeLoia shows the secretory-phase change is a glycoform
change on a core protein of unchanged abundance.

**Discriminating measurement.** A **glycoform-selective perturbation** with a
surface readout and an adhesion endpoint, and separately an embryo-local
clearance determinant tested by perturbation rather than imaged.

**Already available?** **No.** No paper in either cluster performs a
glycoform-selective perturbation, and the only paper holding MUC1-removal tools
has no adhesion endpoint.

**Disposition: contradiction retained; TI-06 stands, and §3.2's structural block
on the barrier arm is independent of it.**

### 5.4 WNT and DKK1

**Claims.** Four experiments give no common sign. Loss- and gain-of-function in
the same compartment with the same markers **both reduce** the endpoint.

**Context that differs.** Compartment, species, and which side the ligand was
applied to; one key experiment manipulates the embryonic surrogate rather than
the maternal monolayer.

**Discriminating measurement.** A **graded** stromal perturbation of canonical
WNT activity, in one human system, with a monotonicity test across the range.
Boolean form cannot carry the result either way, so this is a question about
level, not sign.

**Already available?** **No**, and the authors of the relevant paper concede the
significance of decidual DKK1 "remains unclear".

**Disposition: contradiction retained, and it is explicitly not
Booleanisable — the same class as PANX1.**

---

## 6. Prioritised gap table

| # | gap | status | decision it could change | priority |
|---|---|---|---|---|
| 1 | human progestin-alone arm with protein-level IHH | **requires new measurement** | unblocks R4-b without silently enacting R4-a; the highest-leverage single measurement | **high** |
| 2 | PGR protein versus activity, as an executable split | **resolvable from local papers, but the structural question needs enumeration** | N8; the only candidate attacking the seven-member class | **high** |
| 3 | SETD7 dose-controlled titration | **requires new measurement** | would assign or refuse a SETD7 sign | medium |
| 4 | CST3 necessity in whole conditioned medium | **requires new measurement**, by immunodepletion or organoid knockdown | would make the glandular brake molecule-specific | medium |
| 5 | MUC1 glycoform-selective perturbation | **requires new measurement** | TI-06 and R3-b | medium |
| 6 | graded WNT monotonicity test | **requires new measurement** | whether a WNT node is admissible at all | low |
| 7 | DNM2 as an independent adhesion route | **closed by the local full text — independence unproven**, which is weaker than a demonstrated alias and is stated as such | none now; an alias claim would need enumeration | **not decision-relevant** |
| 8 | Sofia 163-PDF archive manifest | **resolvable from an identified external artifact** | makes the 147/163 overlap computable | low |

**Nothing in rows 1 to 6 is resolvable by further reading.** Every one needs an
experiment. That is the main finding of Phase B: the literature is no longer the
binding constraint on the open questions, and additional screening would not
change a decision.

---

## 7. Effect on U1 to U3

**No change to U1's authorised scope, and none is proposed here.** Fitzgerald
2023 and Zhou 2026 are unregistered, and registering them is a separate owner
decision — reading a paper is not a reason to widen a canonical registration
unit. If authorised, each would add one `pdf_manifest.tsv` row on the same terms
as the contract's seven, and neither would enter
`active_evidence_manifest.tsv` or `context/evidence-register.tsv`, for the
reasons in plan §6/U1.

**No change to U2**, except that the N8 row's unblock condition is now partly
met: Guo and Huang **have** been read at figure level, so the condition narrows
from "read the papers" to "compose the candidate network and enumerate whether
the class actually breaks". That is a strictly harder condition and it stays
inside the pause.

**No change to U3's priority order.** The identifiability question for N8 is now
better posed, because the seam is evidenced at three molecular layers rather than
asserted.

**No change to the pause.** All three resume triggers remain false.

---

## 8. Provenance

**Files added by this assessment:** this document only.

**Not touched:** `network.bnd`, any condition config, protocol, calibration,
transition rate, intervention library, observation mapping, frozen experimental
artifact, or any canonical evidence ledger. Nothing under `data/`. No simulation
run and no seeds spent. The `dropout_e2` pause is not lifted.

**Reproducing the corpus claim in §1:**

```sh
find context/literature/pdfs -name '*.pdf' | wc -l
sha256sum "context/literature/pdfs/Fitzgerald et al. - 2023 - Basolateral secretions of human endometrial epithelial organoids impact stromal cell decidualization.pdf"
```

The corpus is gitignored, so these reproduce only in a working tree holding it.

**Claim boundaries.** Every relationship discussed is a candidate. No perturbation
discussed is causal biological evidence for a patient. No transition rate, no
physical time and no calibration is proposed.
