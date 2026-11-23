# PROFILE Local Reimplementation

## Scope

DT_ADOC reimplements reusable PROFILE and PROFILE_v2 ideas locally in Python
with ADOC-specific provenance, claim boundaries, and tests. The upstream
repositories are methodological references, not runtime dependencies.

## Pinned Upstream Revisions

- PROFILE:
  `https://github.com/sysbio-curie/PROFILE` at
  `87db279aa064efd5c923560f0aefac653a79a9e6`
- PROFILE_v2:
  `https://github.com/ArnauMontagud/PROFILE_v2` at
  `c3e8c39dacb0cad1ff21a79aa871667356b6bf42`

See [`context/upstream/upstream_versions.yaml`](../context/upstream/upstream_versions.yaml)
and [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Execution Paths Inspected

### PROFILE

- `README.md`
- `example1_Linux.sh`
- `example2_Linux.sh`
- `Scripts/Simulations/MaBoSS_specific.py`

Observed workflow:

1. Build patient-profile tables in RMarkdown.
2. Feed mutation/CNA tables into strict node variants.
3. Feed normalized RNA tables into initial-condition or rate-modifier logic.
4. Rewrite MaBoSS `.bnd` and `.cfg` artifacts per profile.
5. Execute MaBoSS via shell and Perl helpers.
6. Postprocess outputs in R.

### PROFILE_v2

- `README.md`
- `Gradient inhibition of nodes/PROFILE_DrugSim.py`
- `Gradient inhibition of nodes/drugs_loop_single.sh`
- `Gradient inhibition of nodes/drugs_loop_double.sh`

Observed workflow:

1. Start from an already-personalized MaBoSS model.
2. Inject anti-node controls into the BND file.
3. Write one CFG per target-engagement combination.
4. Generate shell scripts for all single or double screens.
5. Run MaBoSS many times.
6. Aggregate and plot results in R.

## Reusable Ideas Retained

- Keep baseline topology separate from individualized context.
- Represent strong discrete evidence separately from softer continuous context.
- Encode partial perturbation as target-engagement fractions rather than as a
  binary ON/OFF perturbation.
- Compare matched unperturbed and perturbed models under the same baseline.
- Keep deterministic provenance for every generated model artifact.

## Upstream Behavior Summary

| Topic | PROFILE | PROFILE_v2 | DT_ADOC local decision |
|---|---|---|---|
| Missing genes / NA values | CSV inputs tolerate `NA`; missing values are often skipped rather than forced into a state | Engagement script checks whether target nodes exist in BND | Keep missingness explicit and never turn missing/dropout into OFF or clamp evidence |
| Duplicate identifiers | Not robustly resolved in simulation wrapper; assumes pre-cleaned input tables | Not a primary concern in screen script | Validate duplicates in preprocessing contracts before model mapping |
| Zero values | Continuous inputs assumed numeric and already normalized | Engagement levels are explicit fractions | Preserve numeric zero separately from blank or below-detection source states |
| Scaling / clipping | Soft-rate mode uses a multiplicative factor and log-scale transform around 0.5 | Engagement grid uses explicit values such as `0, 0.2, ..., 1` | Reimplement with explicit, configurable clipping and provenance, not hard-coded cancer settings |
| Initial probabilities | Unregulated inputs default to `0.5` ON probability | CFG rewriting creates per-node inhibition states | Use explicit defaults only when documented as model assumptions |
| Rate modifiers | PROFILE scales rates with a user-provided amplification factor | PROFILE_v2 modifies effective node activity through anti-node mixtures | Keep rate modifiers optional, configurable, and sensitivity-tested |
| Strict variants | Mutation/CNA tables clamp node activity | Not the core focus | Strict variants in DT_ADOC require strong constitutive evidence only |
| Partial inhibition | Not the main mechanism | Implemented by anti-nodes and per-level CFG files | Reimplement as target engagement with deterministic schemas and tests |
| Combinations | PROFILE examples are mainly single-profile simulation cases | PROFILE_v2 generates all single and double combinations through shell scripts | Implement directly in Python, without shell generation |
| Output scoring | Postprocessed in R from output-node probabilities | Postprocessed in R with efficacy/synergy plots | Keep scoring in Python with explicit effect direction and safety separation |

## Assumptions DT_ADOC Must Not Copy

- Cancer-specific models, cohorts, phenotype names, and drug target lists
- RMarkdown profile-building pipelines as ADOC preprocessing defaults
- Shell-script generation as the orchestration layer
- Perl-based postprocessing as a required runtime dependency
- Bundled MaBoSS executables checked into the repository
- Implicit acceptance of `0.5` default states without ADOC provenance notes
- Aggressive rate scaling factors chosen for cancer models
- R plotting limits or figure-specific manuscript aesthetics

## DT_ADOC Deviations

- ADOC preserves donor/sample/condition/compartment lineage explicitly.
- ADOC keeps construction, calibration, and validation evidence roles distinct.
- ADOC treats blanks, below-detection values, and zeros as different states.
- ADOC uses target-engagement language, not dose or occupancy language.
- ADOC cannot infer topology from expression alone.
- ADOC will not estimate PROFILE reference distributions from only three donors.
- ADOC must record blocked gates when source annotations or validation evidence
  are unavailable.
