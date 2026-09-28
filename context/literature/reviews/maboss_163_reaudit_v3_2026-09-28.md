# ADOC MaBoSS literature re-audit v2

**Date:** 2026-09-28  
**Corpus:** 163 PDFs in the Sofia bibliography archive  
**Model reconciled against:** `models/superset/adoc-literature-superset-v0.5.1/`  
**Purpose:** final literature-to-model reconciliation after the paper-by-paper 163-PDF pass, the independent multi-reader review (`A_stromal`, `B_relays_inputs`, `C_epithelial`, `D_kinetics_readouts`, `E_crosscutting`), current repository state, and targeted primary-source verification.

## 1. Claim boundary and evidence policy

This audit separates four things that must not be conflated:

1. **Primary evidence**: human perturbation with an adhesion/attachment or decidualization endpoint is strongest; human descriptive evidence supports timing/state but not an executable edge; non-human causal evidence is species-transfer only; reviews point to primaries and consensus but do not by themselves license edges.
2. **Structural truth about the current Boolean network**: algebraic absorption/aliasing is a property of the model and can be established independently of biology.
3. **A useful candidate rule**: a rule can be biologically plausible yet unidentifiable in the current ADOC design.
4. **A canonical executable rule**: this requires evidence, structural usefulness, and an identifiable/adopted representation.

The independent review used essentially the same hierarchy. Its strongest methodological contribution is that figure-level verification must be treated as a gate when a claim depends on a panel: multiple prose/legend summaries were inconsistent with the figures.

## 2. What changed relative to the first 163-PDF audit

The second review did not overturn the main diagnosis, but it changes several dispositions.

### 2.1 XAV939: canonical wiring is now **deferred**, not required

Earlier I leaned toward connecting `IN_XAV939` to an explicit WNT state. After reconciling Garcia-Alonso 2021, Shibata 2024, Gnecco 2023, Xu 2026, Aikawa 2017 and the review synthesis, that is too strong.

- Human WNT inhibition can increase secretory-lineage differentiation efficiency, but it is **not necessary** for the secretory state.
- Secretory/decidual phenotypes occur on platforms without XAV939 and even under active RSPO1/WNT-supporting culture.
- Other systems give opposite or context-dependent signs.
- The direct ADOC protocol already contains XAV939 and still decidualizes, excluding a canonical stromal WNT veto.

**Final disposition:** keep `IN_XAV939` as a zero-degree canonical input for now. Maintain a **WNT/lineage rate-modifier rule family** as an uncertainty variant. The discriminating experiment is a hormone-treated ADOC arm **minus XAV939**.

**Confidence:** 9.5/10.

### 2.2 PRL versus IGFBP1: the ordering is strong, but the numerical rate is not calibrated

The independent review strengthens the biological case that `S_PRL` and `S_IGFBP1` should not be synchronous. Gnecco 2019 and Molè/CREST provide human in-vitro time-course support for IGFBP1 preceding PRL, while Wang 2020 and Riesewijk 2003 independently show non-equivalent state occupancy/expression in vivo.

However, current repository `TI-04` correctly warns that ADOC detection limits, absolute abundance differences and lost chip pairing prevent the ADOC outlet data from calibrating a physical rate ratio.

**Final disposition:** use the ordering

```text
u_up(S_IGFBP1) > u_up(S_PRL)
```

as a **literature-informed relative-rate prior / sensitivity axis**, not as a calibrated `2x` fact. Independent Boolean rules remain deferred under `TI-04` until the measurement/design blocker is satisfied.

**Confidence:** 9/10 for ordering; 4/10 for any particular numerical ratio.

### 2.3 PAEP: observation-model problem confirmed; stromal secretion claim softened

PAEP/glycodelin is a strong secretory differentiation marker, particularly of glandular epithelium. The review correctly identifies that it should not define luminal epithelial receptivity. A decidual stromal subpopulation has been reported to express `PAEP`, so an outlet measurement is not safely interpreted as luminal-epithelium-specific.

But the available material establishes **stromal expression**, not comparably strong direct proof that decidual stroma is a quantitatively important source of secreted PAEP in the ADOC outlet.

**Final disposition:** treat PAEP as a **glandular/global secretory readout with uncertain compartment purity**, not a luminal attachment gate. Do not describe stromal PAEP secretion as established unless a direct secretion experiment is added.

**Confidence:** 9.5/10 for demoting PAEP as a receptivity gate; 6/10 for meaningful stromal contribution to secreted PAEP.

### 2.4 CD98: important determinant, but **not** a universal conjunct on all redundant adhesion

The independent review proposed making CD98 a hard conjunct of `X_ADHESION_ROUTE_REDUNDANT`. Dominguez 2010 gives strong evidence that CD98 and CD9 independently affect blastocyst adhesion in a human endometrial cell model, and that CD98 is induced by hCG, E2, LIF and EGF.

That evidence does **not** establish that CD98 is required for every other redundant route (CDH1, ANXA2, HB-EGF, DAG1, MUC1 glycoform). Making it a universal conjunct would turn a strong determinant into a universal veto and would re-open a deliberate redundancy design choice without direct evidence.

**Final disposition:** reject the universal CD98 conjunct as canonical. Instead:

- split `E_CD98_CD9` into distinguishable CD98 and CD9 states;
- give CD98 a non-LIF-only upstream rule family (`hCG`, E2, LIF/STAT3, EGF where representable);
- represent CD98/CD9 as their own adhesion-support route or rate contribution rather than as a mandatory gate on all redundant routes.

**Confidence:** 9/10.

### 2.5 MUC1: the diagnosis is now primary-verified; the patch remains deferred

Meseguer et al. 2001 has now been directly verified and is registered in the current repository as `REF-085`. It shows progesterone-associated up-regulation of human endometrial MUC1 and strictly local removal at the attached embryo. Thus the current rule

```text
E_MUC1_BARRIER = not E_SECRETORY_STATE
```

has the wrong interpretation if read as human MUC1 abundance.

The primary still does **not** identify the determinant of local clearance. Therefore `TI-06` remains correctly deferred.

**Final disposition:** abundance, permissive glycoform and local clearance must remain separate concepts. Do not use a bare sign flip. The barrier should ultimately act at the interface/anti-adhesive layer, after a human perturbational determinant of local clearance is identified and the exact split is adopted.

**Confidence:** 10/10 diagnosis; 6/10 exact future Boolean implementation.

### 2.6 Mifepristone: hard PGR veto is a challenge abstraction, not a quantitative law

Lalitkumar et al. 2007 has now been independently verified: at `10^-5 M` mifepristone, **0/15** human embryos attached to a 3D human endometrial construct, versus **10/17** controls and **6/14** levonorgestrel. This validates a strong anti-attachment effect at the same nominal 10 uM scale used by ADOC.

But Shibata 2024 reports a much smaller, non-significant steroid-blockade effect, whereas ADOC reports 1/8 residual stable adhesions. These systems differ in embryo model, endpoint and flush/stability criterion.

**Final disposition:** retain the current hard `not IN_MIFEPRISTONE` formulation as a **defined ADOC challenge abstraction / stress-test variant**, but do not interpret it as a quantitatively universal human rule. A bounded antagonism or stochastic-residual variant is appropriate for quantitative probability fitting.

**Confidence:** 9/10.

### 2.7 The WOI clock: do not explain ADOC failures by a 1:1 cycle-day mapping

Review articles consistently place the natural human implantation window roughly in the mid-luteal period, but they do not justify mapping one in-vitro ADOC day to one in-vivo cycle day. The review synthesis itself warns that in-vivo timing can license ordering, not calibrated intervals.

**Final disposition:** use in-vivo timing only as a **partial ordering prior**. Do not currently attribute a portion of the 10/19 non-adhesions to the chip being at the “leading edge” of the WOI.

**Confidence:** 9/10.

---

## 3. Current v0.5.1 structural state

The current executable core still contains several biologically distinct variables that are exact or near-exact logical aliases:

```text
E_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE
E_IHH = E_PGR
S_PGR = IN_PROGESTIN and not IN_MIFEPRISTONE
S_NR2F2 = E_IHH and S_PGR
S_BMP2 = (S_PGR and S_PKA) or S_NR2F2

E_PAEP = E_SECRETORY_STATE
E_PC6 = E_SECRETORY_STATE
E_HBEGF = E_SECRETORY_STATE
E_SPP1_EXPR = E_SECRETORY_STATE
E_ANXA2_ACTIN = E_SECRETORY_STATE
E_MUC1_SLEX = E_SECRETORY_STATE

S_PRL = S_DECIDUALIZED
S_IGFBP1 = S_DECIDUALIZED
S_SPP1 = S_DECIDUALIZED
S_TAZ_ECM = S_DECIDUALIZED
```

`OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED` is already repaired in v0.5.1 (`TI-01` discharged), which should be preserved.

The major remaining issue is therefore not simply missing molecules. It is **loss of perturbational distinctions through artificial identity classes**.

---

## 4. Final model-action matrix

### 4.1 Recommended canonical cleanup now

#### C1. Remove PAEP from the epithelial phenotype definition

Current:

```text
OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE and E_PAEP
```

Recommended:

```text
OUT_EPITHELIAL_RECEPTIVE = E_RECEPTIVE_SURFACE
```

Rationale: PAEP is a marker/output of secretory differentiation, not demonstrated as a causal requirement for attachment. The current conjunct is algebraically absorbed today, so this is a low-blast-radius repair that prevents a future PAEP de-aliasing from accidentally becoming a receptivity veto.

**Confidence:** 9.5/10.

#### C2. Correct the observation model before adding more biology

Recommended measurement semantics:

```text
PRL outlet        -> S_PRL                         [stromal; best compartment purity]
IGFBP1 outlet     -> OUT_IGFBP1_SECRETED          [epithelial + stromal ambiguity]
PAEP staining/ELISA -> glandular/global secretory readout; not luminal-specific
SPP1 outlet       -> mixed epithelial/stromal ligand pool; not source-resolved
```

If no new `OUT_IGFBP1_SECRETED` node is added immediately, at minimum the existing mapping must be flagged as **compartment-ambiguous** rather than `S_IGFBP1`-specific.

**Confidence:** 9.5/10.

#### C3. Introduce explicit relative-rate semantics as a model layer

The corpus repeatedly distinguishes **delay** from **block**. This is most obvious for SPP1/alphaVbeta3, CD44 and epithelial HA, where perturbations change early attachment kinetics but arms later converge.

Minimum model-policy change:

- perturbation scoring must include **time-to-`OUT_STABLE_ADHESION`** or occupancy over a finite assay window;
- do not rely exclusively on fixed-point truth values;
- allow named relative-rate priors even when absolute MaBoSS time remains uncalibrated.

**Confidence:** 10/10 for the need; 7/10 for any individual rate value.

#### C4. Re-express the anti-SPP1 perturbation as a kinetic penalty

Current biology is more consistent with:

```text
anti-SPP1 -> lower probability / slower rate of the SPP1-mediated stable-attachment transition
```

than with a universal statement that final adhesion is impossible whenever SPP1 is neutralized.

For stress testing, the hard clamp can remain as an extreme variant, but the default quantitative perturbation should be rate-based.

**Confidence:** 9/10.

#### C5. Remove the redundant direct HAND2 conjunct from epithelial proliferation

Current:

```text
S_FGF_MITOGENIC = not S_HAND2
E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC and not S_HAND2
```

Under the current upstream rule this simplifies to:

```text
E_ESTROGENIC_PROLIFERATION = IN_E2 and S_FGF_MITOGENIC
```

Removing the second `not S_HAND2` is bit-identical today but prevents a future independent WNT/FGF or other stromal relay from being incorrectly suppressed merely because HAND2 is present. It also matches the repository note that the HAND2 effect is a **net effect through the stromal relay**, not a demonstrated direct epithelial edge.

**Confidence:** 9/10 as a safe refactor; 7/10 as biological semantics because the exact human relay identity remains unsettled.

---

### 4.2 Strong corrections that remain deferred

#### D1. MUC1 abundance / glycoform / local-clearance split (`TI-06`)

**Evidence status:** contradiction is settled; executable determinant is not.

Required conceptual separation:

```text
E_MUC1_ABUNDANCE
E_MUC1_PERMISSIVE_GLYCOFORM
X_MUC1_LOCAL_CLEARANCE
X_MUC1_BARRIER_AT_INTERFACE
```

Do not use a bare sign flip. Do not make maternal receptivity itself embryo-contact-dependent merely to rescue the MUC1 sign.

**Confidence:** 10/10 that a split is required; 6/10 exact topology.

#### D2. Split CD98 and CD9; then repair CD98 upstream wiring

Current:

```text
E_CD98_CD9 = E_GP130_STAT3
```

This incorrectly makes CD98/CD9 identical to the LIF-STAT3 state. Dominguez 2010 independently manipulates CD98 and CD9 and shows both influence adhesion; CD98 is induced by hCG, E2, LIF and EGF.

Preferred future family:

```text
E_CD98 != E_CD9
E_CD98 <- E_GP130_STAT3 OR IN_HCG OR IN_E2 [plus EGF route if represented]
X_CD98_CD9_MICRODOMAIN <- E_CD98 AND E_CD9   [candidate functional complex]
```

Do **not** make CD98 a universal hard conjunct of every redundant adhesion mechanism.

**Confidence:** 9.5/10 split; 8/10 hCG as an upstream CD98 input; 6/10 exact microdomain Boolean AND.

#### D3. De-alias LIF, IL11 and epithelial GP130/STAT3

Current:

```text
E_GP130_STAT3 = E_LIF
```

Human epithelial experiments show LIF and IL11 can converge on STAT3 while producing ligand-specific downstream behavior. Therefore ligand and pathway state should not remain identical.

Candidate family:

```text
E_GP130_STAT3 = E_LIF OR E_IL11
```

with ligand-specific effectors or rates rather than assuming all consequences are shared.

**Confidence:** 9/10 that the identity is incomplete; 7/10 for the simple OR as the final rule.

#### D4. Split alphaVbeta3 and alphaVbeta5 (`TI-03`)

Accumulated evidence assigns different biology:

```text
SPP1 -> alphaVbeta3 -> early attachment/stabilization
PC6-related processing -> alphaVbeta5 / other surface-integrin branch
```

The merged `E_ITGAVB3_5` node masks this distinction. The split remains deferred until every current reader of the merged node is adjudicated and a non-absorbed upstream determinant exists.

**Confidence:** 9/10 diagnosis.

#### D5. Reopen `E_IHH = E_PGR`

Primary human organoids show strong E2-associated IHH induction without progestin in at least two donors, while mouse causal work identifies SOX17/GATA2/PGR enhancer competence. Human in-vivo studies and SPRM work also support progesterone dependence, so the literature does **not** license a simple replacement.

Maintain a rule family rather than a canonical flip:

```text
v0: E_IHH = E_PGR
v1: E_IHH = IN_E2 OR E_PGR
v2: E_IHH = E_PGR AND E_SOX17_COMPETENT
```

Test variants against human ADOC epithelial readouts before adoption.

**Confidence:** 9/10 that the identity is too strong; 6/10 for any one replacement.

#### D6. Separate mechanical permissiveness from decidualization

Rawlings 2021 shows that a highly differentiated decidual state can become mechanically non-permissive when the dynamic senescent/remodelling subpopulation is eliminated. The current model effectively collapses:

```text
X_MECHANICAL_PERMISSIVE_ECM ~ S_DECIDUALIZED
```

because `S_TAZ_ECM = S_DECIDUALIZED` and the remaining mechanics are weakly active in the recorded design.

Future structure should permit:

```text
S_DECIDUALIZED = 1
X_MECHANICAL_PERMISSIVE_ECM = 0
```

with a balanced-remodelling/senescence or independent matrix-dynamics state.

Also separate **beneficial shear/prostanoid signaling** from **harmful stiffness/ER-stress mechanics**; they are not one sign of one variable.

**Confidence:** 9.5/10.

#### D7. Generalize the stromal-to-epithelial proliferation relay

The existence of a stromal influence on epithelial E2-driven proliferation has human support, but the current name `S_FGF_MITOGENIC` is too specific.

- Mouse HAND2 work supports a family of FGFs.
- Human Murata work isolates FGF9 as the progesterone-regulated member among those tested.
- Nallasamy shows an independent MSX/WNT/beta-catenin route to stromal FGF10/18/21 in mouse while HAND2 remains present.
- Human conditioned-medium experiments show stromal paracrine effects but do not establish FGF identity and can even be anti-proliferative depending on context.

Preferred abstraction:

```text
S_TO_E_PROLIFERATION_RELAY
```

with FGF as one candidate mechanism, rather than assuming all human stromal paracrine control is FGF.

**Confidence:** 9/10 for abstraction change; 6/10 exact upstream logic.

#### D8. Independent PRL and IGFBP1 Boolean rules remain deferred (`TI-04`)

Biological non-equivalence is now strong. The remaining blocker is **identifiability**, not whether the two analytes differ.

Until the observation/design conditions are met, use relative-rate sensitivity rather than inventing a new Boolean regulator.

**Confidence:** 9.5/10.

---

## 5. Inputs and relays: final dispositions

### 5.1 `IN_XAV939`: keep canonical zero-degree; variant-only rate effect

Do not add a hard WNT-off requirement to `E_SECRETORY_STATE` or `S_DECIDUALIZED`. Human organoid data support WNT inhibition as a lineage-differentiation modifier, but control cultures already generate secretory states, and signs are context dependent.

**Experiment that resolves it:** ADOC full hormone cocktail minus XAV939.

### 5.2 `IN_HCG`: do not wire to a generic maternal state yet

There are many candidate hCG targets with different systems and endpoints. The strongest current direct route into the existing model is:

```text
IN_HCG -> E_CD98
```

from primary human endometrial epithelial data, but this should be implemented only after splitting CD98 from CD9. Do not equate CGA-FSHR with canonical hCG-LHCGR biology.

### 5.3 `IN_EMBRYO_CONDITIONED_SIGNAL`: keep unwired canonically

Maternal responses to embryo-conditioned cues are biologically plausible and supported by several candidate studies, but no current corpus result provides a clean, general pre-contact maternal rule that can safely replace the input with a named pathway. Maintain it as a boundary uncertainty input until a primary perturbation/rescue result is adjudicated.

### 5.4 The `X_*_RELAY` variables should not be forcibly collapsed to single molecules

The corpus did not identify a unique receptor/mechanism for any relay. CD44, HB-EGF/EGFR-family engagement, HA, PIEZO1 and others are useful mechanistic candidates and measurement handles, but most single-molecule assignments would only rename the free variable or overstate a redundant interface.

Recommended policy:

- keep the stochastic relays as abstractions for now;
- attach mechanistic provenance and candidate measurement handles;
- only replace a relay when the replacement changes truth-table content **and** has direct evidence for the modeled endpoint.

**Confidence:** 9/10.

---

## 6. Rate/stage layer: now a first-class model requirement

The corpus repeatedly shows that the same Boolean endpoint can be reached with very different kinetics. The model should therefore distinguish:

```text
block versus delay
fast versus slow induction
transient versus sustained signaling
early differentiation versus late maintenance
```

### 6.1 High-confidence relative-rate constraints

Use as ordering/sensitivity priors, not calibrated hours:

```text
S_IGFBP1 rises before S_PRL under several human in-vitro schedules
cAMP accelerates stromal decidual outputs relative to progestin alone
E_IHH can precede late epithelial PAEP maturation in organoids
anti-SPP1 / alphaVbeta3 perturbation mainly delays stable attachment in the hybrid assay
CD44 blockade delays initial attachment
apical HA removal accelerates the weak-to-stable transition
```

### 6.2 Stage-dependent sign mechanisms

Keep as staged variants rather than universal Boolean edges:

- **TGFbeta:** early differentiation support versus later suppression of PRL/IGFBP1 in already-decidualized stroma.
- **LEFTY:** decidual feedback/resolution brake, not a simple `NOT S_DECIDUALIZED` requirement.
- **WNT:** lineage/state dependent; not a universal positive or negative receptivity switch.
- **senescence:** balanced/dynamic component can be beneficial; persistent/excessive senescence is not equivalent to the required remodelling state.

### 6.3 No window-closing mechanism remains a structural gap

The current network largely latches hormone-induced competence under sustained inputs. Natural receptivity is transient. This should be recorded as a formal structural limitation rather than patched with an arbitrary timer.

**Confidence:** 9/10.

---

## 7. Observation-model audit

### 7.1 High-priority corrections

| Readout | Current interpretation | Reconciled interpretation |
|---|---|---|
| PRL outlet | stromal decidualization | strongest compartment-pure stromal readout in corpus |
| IGFBP1 outlet | `S_IGFBP1` | compartment-ambiguous secreted IGFBP1; epithelial expression is documented |
| PAEP | epithelial receptivity | glandular/global secretory differentiation; not luminal attachment competence |
| SPP1 outlet | free SPP1 / stromal or epithelial | mixed-source pool unless compartment resolved; antibody acts on free ligand, not source expression |
| LIF | epithelial pathway | useful epithelial readout, but ligand != pathway activation and IL11 convergence matters |

### 7.2 Recommended additional measurable proxies

Prioritize analytes that break model classes rather than adding more aliases:

- CD98 and CD9 separately at the luminal epithelial surface.
- alphaVbeta3 and alphaVbeta5 separately.
- HABP/hyaluronan at the apical surface plus outlet HA.
- LIF and IL11 separately, plus pSTAT3 as the shared-pathway state.
- CXCL8 early stress pulse versus later PRL/IGFBP1/CXCL14 for temporal staging.
- matrix/remodelling measures that can separate decidual differentiation from mechanical permissiveness.

---

## 8. Candidate mechanisms to retain, but not canonicalize

These are useful catalog/rule-variant mechanisms, not current default rules:

- `S_LEFTY_BRAKE` - human perturbational brake evidence, but stage/maintenance semantics required.
- epithelial `TGFbeta1 -> stromal SMAD2/3` - strong early decidualization candidate, but conflicts with later TGFbeta suppression and cAMP can bypass epithelial dependence.
- `E_SOX17_COMPETENT -> E_IHH` - strong mouse causal enhancer biology, human transfer uncertain.
- `E_HA_APICAL` anti-adhesive/kinetic brake - behavior-changing candidate; hormone-conditioned persistence on ADOC remains unknown.
- `E_CD44` initial attachment support - useful kinetic modifier and reagent target; not a full replacement for the SPP1 relay.
- endothelial prostanoid -> stromal cAMP - strong physiological route, but ADOC lacks an endothelial compartment and exogenous cAMP masks it.
- maternal EV/miRNA -> embryo state - transfer is established; specific human causal cargo rules are not.
- VEGFA-VEGFR1 and CGA-FSHR - post-attachment/outgrowth interface candidates, not stable-adhesion gates.
- ATX/LPC/LPA3 - useful interface extension, mostly mouse and not maternal-core canonical.
- CRH - literature-search candidate only.

---

## 9. Mechanisms explicitly **not** to encode from this corpus

1. `E_MUC1_BARRIER = E_SECRETORY_STATE` as a bare sign flip.
2. `S_PGR = ... AND IN_E2` as a universal requirement.
3. epithelial/stromal PGR down-regulation as immediate Boolean self-inhibition; this creates unsupported oscillatory logic.
4. a hard epithelial conjunct on `S_DECIDUALIZED`; human stroma can decidualize without epithelium under direct hormonal/cAMP stimulation.
5. `IN_XAV939` as a hard requirement for secretory differentiation or decidualization.
6. CD98 as a universal hard conjunct on every redundant adhesion route.
7. PAEP as a causal requirement for receptivity/adhesion.
8. LEFTY as a simple constitutive inhibitor incompatible with decidualization.
9. any single named molecule as the definitive replacement for an `X_*_RELAY` without endpoint evidence.
10. CGA-FSHR interpreted as `IN_HCG -> FSHR`.
11. individual EV miRNAs as executable embryo-competence edges without depletion/add-back or functional human endpoints.
12. direct cycle-day-to-MaBoSS-time conversion.

---

## 10. Experiment priorities after full reconciliation

### Priority 1 - minus XAV939

**Arm:** full hormone cocktail minus XAV939.  
**Why:** resolves the largest declared but unwired input, tests whether WNT inhibition is necessary, beneficial, neutral or adverse in the actual ADOC geometry.

### Priority 2 - minus cAMP

**Arm:** E2 + progestin + XAV939, no cAMP.  
**Why:** reveals endogenous routes into stromal cyclic-nucleotide signaling and separates cAMP as a fast accelerator from a hard biological requirement. It also unmasks hCG/prostanoid/embryo-mediated routes that are otherwise epistatically hidden by 250 uM cAMP.

### Priority 3 - determine local MUC1 clearance mechanism

Cross embryo-conditioned signal versus physical contact and, ideally, a sheddase/protease intervention.  
**Why:** this is the remaining evidence condition for `TI-06`.

### Priority 4 - CD98 versus CD9 independent perturbation in hormone-conditioned human ADOC

**Why:** directly resolves the merged `E_CD98_CD9` node and tests whether one or both are limiting in the actual platform.

### Priority 5 - alphaVbeta3 versus alphaVbeta5 selective perturbation

**Why:** resolves `TI-03` and tests the SPP1/alphaVbeta3 versus PC6/alphaVbeta5 allocation.

### Priority 6 - time-resolved anti-SPP1 endpoint

Score weak attachment, stable attachment after flush and convergence over time rather than one late binary value.  
**Why:** distinguishes kinetic delay from true loss of competence.

### Priority 7 - LIF/IL11/STAT3 decoupling

If the goal is to break the epithelial LIF/STAT3 alias, pathway inhibition is more informative than simply measuring another marker. A design that compares ligand-specific blockade with shared STAT3 inhibition would distinguish `E_LIF` from `E_GP130_STAT3` and test IL11 compensation.

---

## 11. Repository actions

### 11.1 Already resolved in current repo

- `OUT_STROMAL_DECIDUALIZED = S_DECIDUALIZED` is already landed in v0.5.1 (`TI-01` discharged).
- Meseguer 2001 is now registered as `REF-085`; the prior “obtain Meseguer 2001” action is obsolete.
- MUC1 rule-family evaluation is discharged as `TI-02`; canonical implementation remains `TI-06` deferred.

### 11.2 Registration work still needed

At the time of this reconciliation, the current `references.tsv` still does not contain several repeatedly used corpus primaries, including:

- Fitzgerald 2019 - human endometrial epithelial organoids.
- Gnecco 2019 - endothelial prostanoid / stromal decidualization chip.
- Wang 2020 - single-cell atlas of the human endometrium.
- Berneau 2019 - CD44 / hyaluronan attachment kinetics.
- Tang 2010 - LEFTY decidual brake.
- Kim 2005/2006 TGFbeta epithelial-stromal coculture paper (distinct from the registered FOXO1 Kim paper).
- Kang 2014 - SPP1 / alphaVbeta3 attachment kinetics.
- Li 2026 - human endometrioid implantation model.
- Song 2025/2026 - post-implantation embryo-endometrium coculture.
- Xu 2026 - adenomyosis assembloid WNT/BMP intervention.
- Lalitkumar 2007 - mifepristone versus levonorgestrel human attachment model.

Registration should be DOI/title based, not author+year only, because the corpus contains author-year collisions and mislabeled filenames.

### 11.3 Figure-verification gate

For every evidence row whose direction, magnitude or significance depends on a figure:

1. render the relevant page;
2. inspect panel labels and significance marks;
3. record figure-level values separately from prose/abstract summaries;
4. refuse promotion when figure and prose disagree until resolved.

---

## 12. Final ranked diagnosis of the current model

### Tier A - highest-confidence structural/biological problems

1. **PAEP is a readout, not part of the definition of epithelial receptivity.**
2. **MUC1 abundance is encoded with the wrong human interpretation; abundance and local barrier clearance must be split.**
3. **LIF, GP130/STAT3 and CD98/CD9 are artificially coupled.**
4. **alphaVbeta3 and alphaVbeta5 are improperly merged.**
5. **S_PRL and S_IGFBP1 are biologically non-equivalent; current synchronous rules are an abstraction limit.**
6. **mechanical permissiveness is not identical to decidualization.**
7. **fixed-point-only perturbation scoring misses real delay phenotypes.**
8. **the observation model over-assigns IGFBP1 and PAEP to specific compartments/states.**

### Tier B - strong but representation-dependent problems

9. `E_IHH = E_PGR` is too strong and needs an uncertainty family.
10. `S_FGF_MITOGENIC = not S_HAND2` is too specific/incomplete for the human stromal-to-epithelial relay.
11. cAMP should be understood as a powerful kinetics modifier and experimental shortcut, not solely a biological gate.
12. the network lacks a credible window-closing mechanism.
13. the mifepristone challenge is too binary for quantitative probability fitting.

### Tier C - real biology, not yet canonical-model obligations

14. LEFTY/TGFbeta stage-dependent control.
15. SOX17/GATA2 enhancer competence.
16. HA/CD44 attachment kinetics.
17. maternal EV communication.
18. endothelial prostanoid input.
19. post-attachment VEGFA/VEGFR1 and CGA/FSHR axes.
20. embryo-conditioned negative cues / PVRL1-like routes pending primary adjudication.

---

## 13. Bottom line

After the full 163-PDF pass and independent review reconciliation, the main conclusion is unchanged but is now sharper:

> **The next useful MaBoSS version should primarily de-alias states and add time/rate semantics, not add a large number of new molecules.**

The most defensible immediate changes are the PAEP phenotype cleanup, observation-model correction, and explicit kinetic scoring. The strongest biologically required but still deferred repairs are MUC1 splitting, CD98/CD9 separation, LIF/IL11/STAT3 de-aliasing, beta3/beta5 separation, mechanical-permissiveness separation, and PRL/IGFBP1 de-synchronization.

`IN_XAV939`, generic hCG routing, embryo-conditioned signaling and the four hand-set relays should **not** be forcibly resolved merely because they are currently free/unwired; the evidence does not yet select a unique canonical mechanism.

The two highest-information missing ADOC conditions are **minus XAV939** and **minus cAMP**.

---

## 14. Primary sources directly re-checked during final reconciliation

- Meseguer M et al. 2001. *Human endometrial mucin MUC1 is up-regulated by progesterone and down-regulated in vitro by the human blastocyst.* Biology of Reproduction 64:590-601. DOI: `10.1095/biolreprod64.2.590`.
- Lalitkumar PG et al. 2007. *Mifepristone, but not levonorgestrel, inhibits human blastocyst attachment to an in vitro endometrial three-dimensional cell culture model.* Human Reproduction 22:3031-3037. DOI: `10.1093/humrep/dem297`.
- Dominguez F et al. 2010. *Human Endometrial CD98 Is Essential for Blastocyst Adhesion.* PLoS ONE 5:e13380. DOI: `10.1371/journal.pone.0013380`.
- Garcia-Alonso L et al. 2021. *Mapping the temporal and spatial dynamics of the human endometrium in vivo and in vitro.* Nature Genetics 53:1698-1711. DOI: `10.1038/s41588-021-00972-2`.
- Wang W et al. 2020. *Single-cell transcriptomic atlas of the human endometrium during the menstrual cycle.* Nature Medicine 26:1644-1653. DOI: `10.1038/s41591-020-1040-z`.
- Gnecco JS et al. 2019. *Hemodynamic forces enhance decidualization via endothelial-derived prostaglandin E2 and prostacyclin in a microfluidic model of the human endometrium.* Human Reproduction 34:702-714. DOI: `10.1093/humrep/dez003`.
- Berneau SC et al. 2019. *Investigating the role of CD44 and hyaluronate in embryo-epithelial interaction using an in vitro model.* Molecular Human Reproduction 25:265-273. DOI: `10.1093/molehr/gaz011`.

## Overall confidence

**9.5/10** for the final prioritization and “do not encode” boundaries.  
**8/10** for the exact shape of the next canonical Boolean topology, because several of the most important problems are now known to be stage-, rate- or compartment-dependent rather than uniquely Boolean.

---

## 15. Recommended active evidence set from the 163-PDF corpus

This section makes explicit the subset of the 163-paper corpus that is actually worth retaining as **active model-support evidence**. It is not the same thing as Section 14, which lists only the small number of primaries re-checked directly during the final reconciliation. The active set below contains **36 unique papers** (not 35; the earlier conversational count was an arithmetic error): 20 core evidence papers, 10 uncertainty/variant papers, 1 boundary-definition paper, and 5 synthesis reviews. Duplicate PDFs are listed once.

### 15.1 Core model-support papers (20)

| corpus # | paper / PDF | primary model role |
|---:|---|---|
| 10 | Blauer et al. 2005, *A novel organotypic culture...* | Human stromal context constrains E2-driven epithelial proliferation; supports a stromal-to-epithelial relay but not a uniquely FGF-defined one. |
| 21 | Cullinan et al. 1996, LIF/LIFR/gp130 in human endometrium | Human compartment/timing constraint for LIF-family signaling and gp130/LIFR interpretation. |
| 28 | Dominguez et al. 2010, *Human Endometrial CD98 Is Essential for Blastocyst Adhesion* | Direct CD98 and CD9 gain/loss adhesion evidence; CD98 induction by hCG/E2/LIF/EGF; supports CD98/CD9 de-aliasing. |
| 30 / 116 | Fitzgerald et al. 2019, *Self-renewing endometrial epithelial organoids of the human uterus* | Human epithelial hormone/cAMP perturbation; challenges `E_IHH = E_PGR`; supports epithelial cAMP potentiation and PAEP as readout. Keep one PDF. |
| 32 / 33 | Garcia-Alonso et al. 2021 | Human WNT-inhibition / NOTCH-separation experiment; supports XAV939 as differentiation/rate modifier rather than a necessary gate. Keep one PDF. |
| 38 | Gnecco et al. 2017 | Human stromal/endothelial chip; shows hormone-driven decidualization without epithelium and provides timing constraints. |
| 39 | Gnecco et al. 2019 | Strong human kinetic evidence for IGFBP1-before-PRL; endothelial COX2 -> PGE2/PGI2 -> stromal cAMP/decidualization route. |
| 40 | Gnecco et al. 2023 | Human epithelial-stromal co-culture in synthetic ECM; constrains stiffness, IL1B, WNT-context and cross-compartment interpretation. |
| 56 | Kang et al. 2014 | SPP1/alphaVbeta3 perturbation; attachment is delayed rather than permanently blocked, supporting rate semantics. |
| 69 | Li et al. 2026, *A 3D in vitro model for studying human implantation and implantation failure* | Human implantation model validating hormone+cAMP effects and separating attachment from later outgrowth; interface candidates VEGFA/VEGFR1 and CGA/FSHR. |
| 86 | Mole et al. 2025/2026, *Modeling human embryo implantation in vitro* | High-fidelity human implantation model; stromal/epithelial coupling and important counter-evidence against XAV939 necessity. |
| 91 | Nallasamy et al. 2012 | Causal mouse MSX/WNT/beta-catenin -> stromal FGF -> epithelial proliferation route; demonstrates `S_FGF_MITOGENIC = not S_HAND2` is incomplete. |
| 107 | Rawlings et al. 2021 | Human assembloid perturbation demonstrating decidualization can coexist with mechanically non-permissive/static matrix; key to de-aliasing mechanical permissiveness. |
| 121 / 159 | Shibata et al. 2024 | Human embryo-endometrial interface model; key counterexample to hard hormone/XAV/epithelial gates. Keep one PDF. |
| 125 | Stavreus-Evers et al. 2006 | Human glycodelin/PAEP timing and localization; supports PAEP as receptive-phase secretory marker, not adhesion gate. |
| 128 | Turco et al. 2017 | Human gland organoids; hormone/cAMP/PAEP/SPP1/LIF responses and PRL/hCG/hPL effects; important observation-model context. |
| 138 | Wang et al. 2020, single-cell atlas | Human in-vivo evidence that PRL and IGFBP1 are non-equivalent; epithelial and stromal transitions have different timing/state occupancy. |
| 145 | Berneau et al. 2019 | CD44/HA perturbation; direct evidence that key interface mechanisms alter attachment kinetics rather than final reachability. |
| 155 | Riesewijk et al. 2003 | Human paired-cycle transcriptomics; strong temporal evidence for PAEP and IGFBP1 and useful readout ordering. |
| 157 | Schutte et al. 2015 | Human stromal<->epithelial conditioned-medium evidence; supports paracrine architecture while cautioning against a uniquely FGF-defined relay. |

### 15.2 Uncertainty / rule-variant papers (10)

These should support explicit alternative rules, stage/rate hypotheses or evidence-gap entries rather than canonical edges by themselves.

| corpus # | paper / PDF | model role |
|---:|---|---|
| 4 | Aikawa et al. 2017 | ATX/LPA/LPA3 embryo-maternal signaling candidate and important XAV939 sign conflict. |
| 23 | Daikoku et al. 2011 | Mouse MSX/WNT5A/polarity mechanism; species-transfer uncertainty module. |
| 60 | Kim et al. 2006, progesterone-dependent epithelial TGF-beta1 release | Human epithelial->stromal TGF-beta/SMAD decidual route; must remain stage-dependent because later TGF-beta can suppress decidual markers. |
| 76 / 77 | Mareckova et al. 2024 | Human endometrial atlas supporting TGF-beta/LEFTY timing, WNT restraint and compartment/state architecture. Keep one version. |
| 90 | Munoz-Blat et al. 2025 | Human multi-omics evidence for mosaic decidualization resistance; constrains tissue-level interpretation of `S_DECIDUALIZED`. |
| 115 | Segura-Benitez et al. 2023 | Direct human endometrial EV uptake by human blastocysts; supports maternal->embryo communication as a real external/interface layer. |
| 132 | Vilella et al. 2015 | Maternal miR-30d transfer to embryo; functional leg is species-limited, so catalog/interface variant only. |
| 136 | Wang et al. 2018, SOX17 | Causal SOX17/GATA2/PGR enhancer control of IHH in mouse; strong reason to treat `E_IHH = E_PGR` as an uncertainty family. |
| 156 | Xu et al. 2026 | Human WNT/BMP intervention in adenomyosis assembloids; supports context-dependent XAV/WNT effects rather than a universal gate. |
| 160 | Tang et al. 2010 | LEFTY as a decidual brake; suitable for stage/rate variant, not a simple Boolean veto. |

### 15.3 Boundary-definition paper (1)

| corpus # | paper / PDF | model role |
|---:|---|---|
| 25 | Deglincerti et al. 2016 | Human embryo self-organization/attachment without maternal tissue; supports keeping embryo competence external and defining the modeled endpoint as maternal stable-adhesion permissiveness rather than intrinsic embryo adhesiveness. |

### 15.4 Reviews worth keeping as synthesis references (5)

These reviews are useful for terminology, temporal ordering, species differences and locating primaries. They should not by themselves license executable edges.

| corpus # | review | role |
|---:|---|---|
| 89 | Muter et al. 2023, *Human embryo implantation* | Modern integrative overview linking maternal and embryo sides. |
| 65 | Lessey & Young 2019, *What exactly is endometrial receptivity?* | WOI and receptivity semantics; useful for phenotype interpretation. |
| 151 / 152 | Gellersen & Brosens 2014, *Cyclic decidualization of the human endometrium...* | Best synthesis for decidual timing, cAMP, PRL/IGFBP1, stress and FOXO1-related biology. Keep one copy. |
| 161 / 162 | Whitby et al. 2020, systematic review of epithelial polarity | Polarity/barrier synthesis and species/context cautions. Keep one copy. |
| 6 | Aplin & Ruane 2017 | Compact implantation-interface framework and useful synthesis of redundancy at the adhesion interface. |

### 15.5 Why the other ~127 PDFs are not in the active evidence pack

They remain useful background literature, but most are one or more of the following: general embryology or reproductive-physiology reviews; platform/methods papers; post-implantation or embryo-side biology outside the maternal MaBoSS scope; descriptive studies without a discriminating rule consequence; duplicated/mislabeled PDFs; or papers whose useful claim is better supported by a primary source already listed above.

This active-set appendix is deliberately narrower than `references.tsv`: the repository may retain more references for provenance, candidate nodes and historical rationale, while the set above is the compact PDF/reference package needed to understand and defend the current model plus its live uncertainty families.

### 15.6 Important non-corpus primaries that must remain in the complete model-support pack

The 36-paper subset above is only the selected evidence from the 163-PDF archive. It does **not** replace core primary papers already held separately, especially Marwood 2009 (IL11/LIF/STAT3), Heng 2011/2015 (PC6/DAG1), Meseguer 2001 and DeLoia 1998 (MUC1), Murata 2019 (HAND2/FGF9), Kusama 2013 (PKA/EPAC), Tamura 2014, Huang 2022, Yap 2011, and the current ADOC calibration paper itself.
