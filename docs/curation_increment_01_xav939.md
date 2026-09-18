# Curation increment 1 — IN_XAV939

Date: 2026-07-28. Claim level: `bibliographically supported, not executable`.
Scope: the disconnected input `IN_XAV939` only. No executable model file was
modified in this increment; the GIF is unchanged.

## Repository discrepancies found

1. Seed-file path: initially found at `context/literature/adhesion_routes_seed.tsv`;
   the user relocated it to `context/literature/searches/adhesion_routes_seed.tsv`
   during this increment. Resolved — docs now reference the `searches/` path.
2. The brief's migration counts were restated from the live tables rather than
   carried over. They match: 93 edges, 294 assertions, 277 bibliographic, 17
   in-house, 294 not-yet-curated, 127 transfer-flagged, 0 reviewed transfers,
   0 manually verified edge-level supports.

## Literature search log

| # | database | query | date | filters | hits | kept |
|---|---|---|---|---|---|---|
| 1 | Europe PMC | `TITLE:"Tankyrase inhibition stabilizes axin and antagonizes Wnt signalling"` | 2026-07-28 | none | 1 | 1 |
| 2 | Europe PMC | `"XAV939" AND ("decidual*" OR "endometri*")` | 2026-07-28 | none | 281 | 0 |
| 3 | Europe PMC | `ABSTRACT:"XAV939" AND ABSTRACT:"endometrial"` | 2026-07-28 | abstract-scoped | 10 | 0 |
| 4 | Europe PMC | `"tankyrase inhibitor" AND ("endometrial epithelial" OR "endometrial organoid")` | 2026-07-28 | none | 5 | 0 |
| 5 | Europe PMC | `("WNT inhibition" OR "Wnt inhibitor") AND "endometrial organoid" AND differentiation` | 2026-07-28 | none | 11 | 1 |
| 6 | Europe PMC | `"beta-catenin" AND "decidualization" AND "human endometrial stromal"` | 2026-07-28 | none | 36 | 0 |
| 7 | Crossref | DOI identity verification for both retained papers | 2026-07-28 | — | 2 | 2 |

**Negative result, recorded deliberately.** Queries 2, 3, 4 and 6 returned no
study testing XAV939, tankyrase inhibition or canonical-WNT manipulation in
*human endometrial stromal decidualization*. The 10 abstract-scoped
XAV939+endometrial hits are endometriosis, endometrial cancer, telocyte and
fibrosis studies, none of which tests the relation the model would encode.

## References promoted to the canonical bibliography

Both were already present as discovery seeds (`ADH-SEED-001`, `ADH-SEED-002`)
and are now canonical with Crossref-verified identity (40/40 references resolve).

- **REF-039** — Huang SM et al. 2009. *Tankyrase inhibition stabilizes axin and
  antagonizes Wnt signalling.* Nature 461(7264):614-20.
  doi:10.1038/nature08356, PMID 19759537.
- **REF-040** — Garcia-Alonso L et al. 2021. *Mapping the temporal and spatial
  dynamics of the human endometrium in vivo and in vitro.* Nature Genetics.
  doi:10.1038/s41588-021-00972-2, PMID 34857954, PMC8648563.

## Claim-level evidence assertions

### A1 — XAV939 reduces canonical WNT activity

| field | value |
|---|---|
| relation | `IN_XAV939 ⊣ E_WNT_CANONICAL_ACTIVITY` |
| evidence origin | bibliographic |
| identifier | REF-039 · doi:10.1038/nature08356 · PMID 19759537 |
| full-text inspection | abstract and reported mechanism inspected; full text not retrieved (paywalled) |
| species evidence | human cell lines / in vitro biochemistry |
| target species | human |
| species transfer required | no (human cell lines) |
| compartment | **not endometrial** |
| experimental system | chemical-genetic screen, quantitative chemical proteomics, cell lines |
| perturbation | XAV939 small-molecule treatment |
| measured readout | β-catenin-mediated transcription; AXIN protein stability |
| direction | inhibition of canonical WNT activity |
| directness | indirect — the drug acts on TNKS1/2; the node abstracts pathway activity |
| support type | pharmacological |
| evidence grade | **B** (human functional, non-endometrial) |
| support rationale | XAV939 inhibits tankyrase 1/2, stabilising AXIN, the concentration-limiting destruction-complex component, thereby stimulating β-catenin degradation and selectively inhibiting β-catenin-mediated transcription. |
| limitations | **No endometrial or reproductive tissue was tested.** Licenses the drug→pathway mechanism only. |
| curation status | curated |
| implementation class | **catalog_only** (variants A/B recorded as `uncertain_rule_variant`) |

### A2 — Reduced canonical WNT promotes epithelial secretory differentiation

| field | value |
|---|---|
| relation | `E_WNT_CANONICAL_ACTIVITY ⊣ E_SECRETORY_STATE` |
| evidence origin | bibliographic |
| identifier | REF-040 · doi:10.1038/s41588-021-00972-2 · PMID 34857954 |
| full-text inspection | open access (PMC8648563); abstract and stated in-vitro result inspected |
| species evidence | human |
| target species | human |
| species transfer required | no |
| compartment | **epithelium** (endometrial organoid) |
| experimental system | human endometrial organoids, single-cell and spatial reference maps |
| perturbation | in vitro downregulation of WNT (and NOTCH) pathways |
| measured readout | differentiation efficiency along secretory and ciliated lineages |
| direction | WNT downregulation **increases** secretory differentiation, i.e. WNT activity inhibits the secretory state |
| directness | direct at pathway-to-lineage level |
| support type | functional |
| evidence grade | **B** (human functional, correct compartment) |
| support rationale | "In vitro downregulation of WNT or NOTCH pathways increases the differentiation efficiency along the secretory and ciliated lineages" in human endometrial organoids. |
| limitations | Perturbs the **pathway**, not XAV939 specifically. Confounded with NOTCH in the same stated result. |
| curation status | curated |
| implementation class | **catalog_only** (variants A/B recorded as `uncertain_rule_variant`) |

### A3 — Composite conclusion

`IN_XAV939 → E_SECRETORY_STATE` is **`composite_or_inferred`**. No single
endometrial experiment tests the complete chain: REF-039 supplies the mechanism
without the tissue, REF-040 supplies the tissue without the compound. The chain
must be represented as two links, never as one direct edge.

## Accepted / rejected ledger

| candidate | decision | class | reason |
|---|---|---|---|
| `E_WNT_CANONICAL_ACTIVITY` node | **accept, catalog_only** | catalog | Required to express A1 and A2 without collapsing them into one unsupported edge. No equivalent node exists — the superset has no AXIN, β-catenin or TCF/LEF node. |
| `IN_XAV939 ⊣ E_WNT_CANONICAL_ACTIVITY` | accept, catalog_only | catalog | Grade B, A1. |
| `E_WNT_CANONICAL_ACTIVITY ⊣ E_SECRETORY_STATE` | accept, catalog_only | catalog | Grade B, A2, correct compartment. |
| `IN_XAV939 → E_SECRETORY_STATE` direct edge | **reject** | — | Composite of two studies; no experiment tests the chain. Would misrepresent inferred pathway completion as direct evidence. |
| **stromal XAV939 relation** | **reject** | — | Queries 2, 3, 4, 6 found no study testing XAV939 or canonical-WNT manipulation in human endometrial stromal decidualization. Negative result recorded. |
| global WNT-inhibition edge across both compartments | **reject** | — | Not defensible in stroma; would assert an effect the search failed to support. |
| `E_TNKS1_2_ACTIVITY` | **catalog_only** | catalog | Real drug target (REF-039), but inserting it adds an intermediate no endometrial experiment resolves. Belongs in the drug-discovery layer. |
| `E_AXIN1_2_STABILIZED` | **catalog_only** | catalog | Same: mechanistically real, not separately observable in ADOC. |
| `E_CTNNB1_TCF_ACTIVITY` | **catalog_only** | catalog | Overlaps `E_WNT_CANONICAL_ACTIVITY`; keeping both in the executable layer would be an alias. Retained in the catalog as the molecular readout. |

## Drug-target annotation (catalog layer)

| target | HGNC | class | perturbation semantics | compounds | model readout | grade | executable? |
|---|---|---|---|---|---|---|---|
| TNKS1/2 | TNKS, TNKS2 | poly-ADP-ribosyltransferase | small-molecule inhibition → AXIN stabilisation → WNT off | XAV939 (REF-039); tankyrase-inhibitor class | none directly; acts via `E_WNT_CANONICAL_ACTIVITY` | B | no — catalog_only |
| AXIN1/2 | AXIN1, AXIN2 | scaffold, destruction complex | stabilisation → β-catenin degradation | indirect via TNKS inhibitors | none directly | B | no — catalog_only |
| CTNNB1/TCF | CTNNB1 | transcriptional co-activator | inhibition → reduced WNT target transcription | — | overlaps `E_WNT_CANONICAL_ACTIVITY` | B | no — catalog_only |

Druggability is not contraceptive suitability. Local delivery, reversibility,
selectivity and safety are unassessed. XAV939 is a research tool compound.

## Dynamic validation of the rule variants

Three architectures were simulated at the converged horizon (`max_time` 30,
4000 trajectories, seeds 1-3) against the unchanged v0.3.0 baseline. Upstream
lineage state was transferred from the unmodified model in every case.

- **baseline** — v0.3.0 unchanged.
- **A, hard permissive gate** — `E_SECRETORY_STATE = IN_E2 and E_PGR and not E_WNT_CANONICAL_ACTIVITY`.
- **B, separate differentiation branch** — hormone control of `E_SECRETORY_STATE`
  retained; new `E_WNT_SENSITIVE_DIFFERENTIATION = E_SECRETORY_STATE and not
  E_WNT_CANONICAL_ACTIVITY` gates `E_PAEP`.

`E_WNT_CANONICAL_ACTIVITY = not IN_XAV939` in both.

A discriminating protocol had to be added: **HT_minus_XAV939** (full hormone
cocktail with XAV939 withheld). It does not exist in `config/protocols.yaml`
because the ADOC protocol always includes XAV939.

| variant | protocol | E_SECRETORY_STATE | E_PAEP | OUT_EPITHELIAL_RECEPTIVE | OUT_MATERNAL_ADHESION_COMPETENCE | S_DECIDUALIZED |
|---|---|---|---|---|---|---|
| baseline | HT | 1.000 | 1.000 | 1.000 | 0.820 | 1.000 |
| baseline | HT−XAV939 | 1.000 | 1.000 | 1.000 | 0.820 | 1.000 |
| **A** | HT | 1.000 | 1.000 | 1.000 | 0.820 | 1.000 |
| **A** | HT−XAV939 | **0.000** | **0.000** | **0.000** | **0.000** | 1.000 |
| **B** | HT | 1.000 | 1.000 | 1.000 | 0.822 | 1.000 |
| **B** | HT−XAV939 | 1.000 | **0.000** | **0.000** | **0.000** | 1.000 |

Seed SD was ≤0.001 everywhere, so every difference above is far outside Monte
Carlo noise. `basal`, `e2_primed` and `XAV939_alone` were 0.000 across all
variants, i.e. no unexpected movement in protocols without the hormone cocktail.
`S_DECIDUALIZED` stayed 1.000 in every variant, confirming no stromal effect was
introduced.

A harness defect was found and fixed mid-run: the joint continuation re-pins
protocol inputs through `forced_nodes`, so the first pass silently restored
`IN_XAV939=True` and made HT−XAV939 identical to HT in every variant. The
corrected harness overrides the continuation's forced nodes for the perturbed
input. The first-pass table was discarded.

### Decision: reject both executable variants, retain catalog-only

Both A and B are structurally valid, non-constitutive within the existing
protocol suite, and produce no regression in `basal`, `e2_primed` or `HT`. They
are nonetheless rejected for the executable network on four grounds:

1. **The evidence is graded; the variants are absolute.** REF-040 reports that
   WNT downregulation *increases differentiation efficiency* along the secretory
   lineage. Both variants encode WNT activity as *abolishing* differentiation.
   A Boolean `and not` converts an efficiency modulation into a hard
   requirement, which overstates what the paper licenses.
2. **They are unfalsifiable under the current protocols.** XAV939 is ON in every
   protocol in which the secretory state fires, so A and B are behaviourally
   identical to baseline across `basal`, `e2_primed` and `HT`. The addition
   changes nothing that any existing protocol can observe.
3. **The only discriminating condition is not an ADOC experiment.** HT−XAV939
   had to be invented for this test. Its prediction cannot be checked against
   any available measurement, so wiring it would add an untestable dependency.
4. **Both make XAV939 necessary for the entire epithelial adhesion arm.** That is
   a strong claim to derive from a composite of two studies, neither of which
   tested the chain: competence falls 0.820 → 0.000 on withdrawal of one
   cocktail component.

`E_WNT_CANONICAL_ACTIVITY`, the two relations and the three molecular targets are
therefore retained as **`catalog_only`** with `uncertain_rule_variant` status
recorded for architectures A and B, so the analysis is preserved and can be
promoted if a XAV939-withdrawal experiment or a graded (rate-based) treatment
becomes available.

The executable model, `edge_evidence.tsv`, the node dictionary and the animation
are unchanged. OM-001, OM-002 and the adhesion suite are unaffected because no
topology changed.

## Why nothing was wired into the executable model

Direct human functional evidence makes a relation an executable **candidate**,
not an automatic executable relation. Wiring `E_WNT_CANONICAL_ACTIVITY` changes
`E_SECRETORY_STATE`, currently `IN_E2 and E_PGR`, adding an inhibitory input
upstream of the whole epithelial receptivity arm and therefore of the adhesion
endpoint. The brief requires, before such a change lands: topology and rule
validation, protocol comparison across basal / E2-primed / hormone-treated /
mifepristone / anti-SPP1, single and combination route perturbations, a check
that adhesion is not constitutively ON or OFF, and convergence plus Monte Carlo
uncertainty quantification.

That validation was not run in this increment, so the relations remain candidates
and the executable model, `edge_evidence.tsv`, the node dictionary and the GIF
are all untouched.

## Unresolved evidence gaps

1. No study tests XAV939 in human endometrial **stroma**. Until one exists, the
   ADOC protocol's XAV939 component has no defensible stromal representation.
2. REF-040's stated result confounds WNT with NOTCH downregulation. Separating
   them needs the figure-level data or a WNT-only perturbation.
3. REF-039 full text was not retrieved (paywalled); the mechanism is taken from
   the abstract's explicit statements, and that limitation is recorded per
   assertion rather than glossed.
4. No ADOC in-house measurement isolates the XAV939 contribution — it is applied
   only as part of the four-component cocktail, so the model cannot currently be
   calibrated against a XAV939-specific readout.
