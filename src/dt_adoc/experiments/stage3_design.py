"""Stage 3: which single prospective experiment most reduces maternal ambiguity.

`variant_discrimination.py` asks, per candidate rule pair, *which observation*
would separate it. This module asks the inverse and operationally prior
question: **given one prospective experiment, which mechanism forks does it
separate, and on a readout that exists?**

The inversion matters because the two questions have different answers. A pair
can be separable in principle by several arms while every one of those arms is
unaffordable, and an arm can be cheap and separate nothing. Ranking candidate
*experiments* requires holding the experiment fixed and sweeping the mechanisms,
which is what `evaluate()` does.

Four distinctions are carried through the computation rather than argued in
prose, because each one has already been collapsed at least once in this
repository:

1. **Mechanism fork vs rule variant.** A fork is a question -- "is concurrent E2
   required for the epithelial secretory program?" -- with two or more classes
   that answer it differently. Some classes come from the curated Gate-3
   candidate table; some are introduced here to represent a reading the
   experiment must be able to *exclude* even though nobody proposes adopting it.
   Those two roles are recorded separately (:data:`ADOPTABLE` vs
   :data:`CONFOUNDER_ONLY`) so that a confounder class can never be read as a
   proposed model repair.
2. **Intervention vs hypothesis.** A clamp that represents a drug is applied to
   *every* class of a fork; a clamp that represents a rule change belongs to one
   class. Mixing them produces an experiment that appears to separate a fork it
   only assumed.
3. **Protocol status vs assay status.** An arm the protocol already passes
   through can still require a readout the platform has never produced. Both are
   declared per experiment, with provenance, and neither is inferred from the
   other.
4. **Readout tier.** Reused verbatim from `variant_discrimination` and derived
   from `config/observation_model_map.tsv`: a separation at a node nothing can
   assay is a difference between two model states, not an experiment.

Nothing here simulates and nothing here edits a committed file. Every prediction
is the exact marginal of the committed network -- or of the network with one
class's rule substitution applied in memory -- over the latent free variables,
conditioned on the experiment's controlled inputs. Controlled inputs are never
marginalised: averaging over "IL-11 supplied" and "IL-11 absent" yields a number
no experiment can produce.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from dt_adoc.experiments.variant_discrimination import (
    _ACTIVE_STATUSES,
    INPUT_DEFAULTS,
    MAPPED_COMPOSITE,
    NO_ASSAY,
    USABLE_ASSAY,
    _is_maternal,
    _readout_tier,
)
from dt_adoc.reporting.identifiability import (
    _evaluate,
    _latent_seeds,
    _topological_order,
    load_identifiability,
    parse_bnd_rules,
    repo_root,
    resolve_model,
)
from dt_adoc.reporting.structure import load_structure

MODEL_VERSION = "adoc-literature-superset-v0.4.0"
OUT_MD = Path("docs/experiments/stage3_experiment_design.md")
OUT_TSV = Path("docs/experiments/stage3_experiment_design.tsv")
#: The tables `docs/stage3_experiment_selection.md` needs but must not restate.
#:
#: Five review rounds on this change found one class of defect and nothing else:
#: a statement about the work that the work itself contradicted -- usually a
#: hand-written sentence about a computed fact that the generated artifact
#: refuted, once a code comment narrower than the code beneath it. Not one
#: touched the computation. The cause is structural rather
#: than careless -- a decision document that retypes forty computed cells has
#: forty places to drift, and a cell carrying a prose caveat cannot even be
#: checked mechanically. So the tables are emitted here and cited there, and the
#: selection document keeps only what is genuinely its own: the reasoning, and
#: the curated judgements that no computation produces.
OUT_TABLES = Path("docs/experiments/stage3_decision_tables.md")

#: The arm `docs/stage3_experiment_selection.md` recommends. Named here so
#: table C is generated for it rather than transcribed from the prose that
#: recommends it.
RECOMMENDED = "dropout_e2"
#: The fork that arm decides.
RECOMMENDED_FORK = "SEC"

#: A class such that an outcome favouring it would license a rule change
#: DIRECTLY, without anything further being sourced first. NOT a claim that the
#: repository already supports it -- an earlier version of this line said
#: exactly that ("a class the repository could adopt as a rule if the experiment
#: supported it"), and it was wrong: `SEC-b` is ADOPTABLE with no prior support
#: at all. Prior support is the separate `MechanismClass.prior_support` field.
ADOPTABLE = "adoptable_alternative"
#: A class introduced only so the experiment can be required to exclude it. It
#: carries no proposal to change the model and must never be read as one: it is
#: the rival explanation of the same measurement. An outcome favouring it
#: licenses opening an evidence gap, never an edit.
CONFOUNDER_ONLY = "confounder_only"
#: The rule as committed in `network.bnd`.
COMMITTED = "committed"


@dataclass(frozen=True)
class MechanismClass:
    """One answer to a fork, as an in-memory edit of the committed network."""

    class_id: str
    label: str
    #: What an outcome favouring this class would LICENSE: :data:`ADOPTABLE`,
    #: :data:`CONFOUNDER_ONLY` or :data:`COMMITTED`. It is not a statement about
    #: how well supported the class already is -- that is `prior_support`.
    role: str
    provenance: str
    evidence: str
    #: What the repository already holds FOR this rule, as against the committed
    #: one. Declared separately from `role` because the two come apart, and
    #: `"none"` is an admissible and informative value.
    prior_support: str = "none"
    overrides: dict[str, str] = field(default_factory=dict)
    #: Free variables the class introduces that an experimenter controls.
    added_free: tuple[str, ...] = ()


@dataclass(frozen=True)
class Fork:
    """A maternal mechanism the current design cannot resolve."""

    fork_id: str
    axis: str
    question: str
    classes: tuple[MechanismClass, ...]
    #: The recorded evidence gap this fork corresponds to, where one exists.
    gap_id: str = ""
    note: str = ""


@dataclass(frozen=True)
class Experiment:
    """One prospective experiment, as a conditioning of the committed network."""

    experiment_id: str
    label: str
    #: A committed condition cfg, by the arm id `identifiability.py` records.
    background: str
    #: Controlled inputs the experiment moves relative to that background.
    input_overrides: dict[str, bool] = field(default_factory=dict)
    #: Derived nodes the INTERVENTION forces. Applied to every class of every
    #: fork, because a drug is not a hypothesis.
    clamps: dict[str, bool] = field(default_factory=dict)
    kind: str = "observation_only"
    #: Whether the ADOC protocol already passes through this state.
    protocol_status: str = "new_arm"
    #: Curated, not derived: whether the platform has ever produced the readout
    #: the separation needs. Stated per experiment with its reason.
    assay_note: str = ""
    #: Interventions applied at once. The project prefers 1.
    perturbations: int = 1
    feasibility: str = ""


# --------------------------------------------------------------------------
# Forks
# --------------------------------------------------------------------------
#
# Curated classes cite their row in
# `context/literature/reviews/gate3_candidate_variants_2026-09-16.tsv`. Classes
# introduced by this Stage-3 analysis say so in `provenance`.
#
# `role` records ONE thing and it is not prior evidentiary support: it records
# what an outcome favouring the class would LICENSE. ADOPTABLE means a rule
# change directly; CONFOUNDER_ONLY means opening an evidence gap and nothing
# else. That is the criterion the decision tree in
# `docs/stage3_experiment_selection.md` §5 already applies, and it is the one
# this module's purpose needs, because the hazard being guarded against is a
# reader mistaking a class carried for exclusion for a proposed repair.
#
# Two earlier statements of this bar were wrong, and the second was wrong in a
# way worth naming. Both said `role` turned on whether the repository already
# SUPPORTS the class -- first citing `references.tsv` only, then widened to admit
# an observation-layer row. Widening it left the criterion unchanged and still
# wrong: `SEC-b` has NO prior support of either kind, and is ADOPTABLE anyway,
# because the recommended arm would supply the support and §5 records the edit
# its outcome licenses. `SEC-d` has no prior support either and is
# CONFOUNDER_ONLY -- not because it is less supported, but because a favourable
# outcome would point at an E2 dependence of PGR, and §5 records that as "open a
# gap", never an edit.
#
# Prior support is a real and different fact, so it is now declared per class in
# `prior_support` and never inferred from `role`. An ADOPTABLE class may have
# none; what it may not have is an unstated one.

_CURATED = "gate3_candidate_variants_2026-09-16.tsv"
_HERE = "introduced by this Stage-3 analysis"

FORKS: tuple[Fork, ...] = (
    Fork(
        "SEC",
        "epithelial secretory input logic",
        "Is concurrent E2 required for the epithelial secretory program, or "
        "does E2 act only upstream of PGR?",
        (
            MechanismClass(
                "SEC-a",
                "E_SECRETORY_STATE = IN_E2 and E_PGR (v0.4 as committed)",
                COMMITTED,
                "network.bnd",
                "MOD-01 keeps the protocol agents as explicit inputs; no "
                "single-agent arm exists, so the conjunction is untested.",
                prior_support=(
                    "none for the conjunction itself. MOD-01 is a modelling "
                    "convention -- keep the agents separate -- not evidence "
                    "that both are required."
                ),
            ),
            MechanismClass(
                "SEC-b",
                "E_SECRETORY_STATE = E_PGR (E2 primes, progestin drives)",
                ADOPTABLE,
                _HERE,
                "The standard reading in which E2 acts by priming and the "
                "progestin drives the secretory program. It is ADOPTABLE "
                "because §5 of docs/stage3_experiment_selection.md records the "
                "rule change its outcome licenses, NOT because the repository "
                "supports it -- see prior_support, which is `none`.",
                prior_support=(
                    "none. Nothing recorded discriminates SEC-b from the "
                    "committed SEC-a: both predict E_PAEP OFF under E2-only, so "
                    "OM-001 cannot tell them apart, and the computed pair index "
                    "reaches `SEC-a vs SEC-b` only through the prospective "
                    "dropout_e2 arm. That is the reason to run it."
                ),
                overrides={"E_SECRETORY_STATE": "E_PGR"},
            ),
            MechanismClass(
                "SEC-c",
                "E_SECRETORY_STATE = IN_E2 or E_PGR (either agent sufficient)",
                ADOPTABLE,
                _HERE,
                "The same OM-001 observation read as an induction rather than "
                "as a sub-threshold baseline.",
                prior_support=(
                    "OM-001's E2-only PAEP of 10165-25470 pg/mL, against a "
                    "3 pg/mL sensitivity. SEC-c is the ONLY class in this fork "
                    "that predicts E_PAEP ON there, so it is also the only one "
                    "data already held can support -- subject to the "
                    "binarisation that same row calls implicit and unrecorded."
                ),
                overrides={"E_SECRETORY_STATE": "IN_E2 or E_PGR"},
            ),
            MechanismClass(
                "SEC-d",
                "E2 acts only by maintaining PGR, in BOTH compartments",
                CONFOUNDER_ONLY,
                _HERE,
                "An outcome favouring it -- PAEP and IGFBP-1 both OFF -- "
                "licenses OPENING AN EVIDENCE GAP and nothing else: the rule it "
                "points at is an E2 dependence of E_PGR and S_PGR, and no "
                "repository row asserts an E2 -> PGR edge "
                "(context/literature/candidate-edges.tsv has none), so the "
                "action is to seek that citation before encoding anything. "
                "Carried because it predicts the same epithelial readout as "
                "SEC-a and a DIFFERENT stromal one, so an experiment reading "
                "only the epithelial outlet could not exclude it.",
                prior_support=(
                    "none; context/literature/candidate-edges.tsv holds no "
                    "E2 -> PGR edge."
                ),
                overrides={
                    "E_PGR": "IN_E2 and IN_PROGESTIN and not IN_MIFEPRISTONE",
                    "S_PGR": "IN_E2 and IN_PROGESTIN and not IN_MIFEPRISTONE",
                    "E_SECRETORY_STATE": "E_PGR",
                },
            ),
            MechanismClass(
                "SEC-e",
                "E2 maintains PGR in the EPITHELIUM ONLY",
                CONFOUNDER_ONLY,
                _HERE,
                "No outcome of this design licenses anything about it, which "
                "is the point: it predicts EXACTLY what the committed SEC-a "
                "predicts on both usable assays, in every arm of the "
                "catalogue, so nothing here can favour one over the other. Its "
                "role is to BOUND the interpretation rather than to be chosen "
                "-- a reader of the decision tree would otherwise take a "
                "PAEP-OFF/IGFBP-1-ON result as establishing the SEC-a "
                "conjunction specifically. Carried so that the "
                "indistinguishability is computed and visible rather than "
                "argued.",
                prior_support=(
                    "none, and the same gap as SEC-d: no repository row asserts "
                    "an E2 -> PGR edge in either compartment."
                ),
                overrides={
                    "E_PGR": "IN_E2 and IN_PROGESTIN and not IN_MIFEPRISTONE",
                    "E_SECRETORY_STATE": "E_PGR",
                },
            ),
        ),
        note=(
            "The fork the observation layer can actually read: E_PAEP is the "
            "only active_constraint and S_IGFBP1 the only active_diagnostic, "
            "and they sit on opposite sides of it. What opens the fork is a "
            "fact about the committed rule rather than support for any "
            "alternative: OM-001 records PAEP at 10165-25470 pg/mL under "
            "E2-only, roughly 3400-8500x the 3 pg/mL sensitivity -- that row's "
            "own claim_ceiling says 'five orders of magnitude', which is its "
            "arithmetic and is not repeated here -- and calls it OFF by a "
            "threshold the same claim_ceiling admits is implicit and "
            "unrecorded. So the committed conjunction is not ESTABLISHED by "
            "the data meant to support it. That is absence of support for "
            "SEC-a; it is not support for SEC-b, and no class below claims it "
            "as such."
        ),
    ),
    Fork(
        "CAMP",
        "cAMP necessity for the stromal decidual program",
        "Is cAMP a necessary conjunct of S_DECIDUALIZED, or a potentiator the "
        "Boolean class cannot express?",
        (
            MechanismClass(
                "CAMP-a",
                "S_DECIDUALIZED = S_PGR and S_PKA and S_BMP2 (v0.4)",
                COMMITTED,
                "network.bnd",
                "REF-073 (Kusama 2013): the PKA-selective analogue drives the "
                "IGFBP-1 and PRL response.",
                prior_support="REF-073, for cAMP driving the response.",
            ),
            MechanismClass(
                "CAMP-b",
                "S_DECIDUALIZED = S_PGR and S_BMP2 (cAMP dispensable)",
                CONFOUNDER_ONLY,
                _HERE,
                "An outcome favouring it -- IGFBP-1 still secreted without "
                "cAMP -- would license OPENING A GAP, not a rule edit, and that "
                "is why the role is confounder-only. The reason is not weak "
                "support: it is that the outcome would be Kusama's graded "
                "potentiation, and a rate-free Boolean model cannot express "
                "potentiation at all, so the repair it points at belongs to a "
                "future rate layer rather than to `S_DECIDUALIZED`'s rule. The "
                "candidate table already rejected `EPAC` as a node on exactly "
                "that ground. Separately, and not the reason for the role: "
                "REF-073 shows EPAC alone INERT and EPAC/RAP1 knockdown "
                "ATTENUATING the PKA-driven response -- attenuation, not "
                "abolition, and only of the second arm.",
                prior_support=(
                    "none, and REF-073 points the other way: EPAC alone inert, "
                    "EPAC/RAP1 knockdown attenuating rather than abolishing."
                ),
                overrides={"S_DECIDUALIZED": "S_PGR and S_BMP2"},
            ),
        ),
        note=(
            "Kusama's graded potentiation is a model-CLASS limitation, not a "
            "topology fork; the candidate table already rejects EPAC as a node "
            "for that reason. An arm that returns 'reduced but present' "
            "rediscovers a limitation the repository has recorded."
        ),
    ),
    Fork(
        "HH",
        "Hedgehog reception necessity",
        "Is stromal BMP2 induction reachable without Hedgehog reception, as "
        "v0.4's disjunct asserts, or does it require it?",
        (
            MechanismClass(
                "HH-a",
                "S_BMP2 = (S_PGR and S_PKA) or S_NR2F2 (v0.4)",
                COMMITTED,
                "network.bnd",
                "The disjunct makes the relay structurally vacuous: "
                "E_PGR = E_IHH = S_PGR = S_NR2F2 = S_BMP2 is one Boolean "
                "function, as GAP-014's impact column already records.",
                prior_support=(
                    "none for the disjunct itself; GAP-014 records that it makes "
                    "the relay vacuous."
                ),
            ),
            MechanismClass(
                "HH-b",
                "S_BMP2 = S_NR2F2 (Hedgehog reception required)",
                ADOPTABLE,
                _HERE,
                "REF-026 (Kurihara 2007) is rescue-grade: epithelial Ihh acts "
                "on stromal COUP-TFII, COUP-TFII is REQUIRED for Bmp2 "
                "induction, and intrauterine BMP2 add-back rescues the "
                "decidual response. Entirely mouse in vivo. REF-075 (Wei 2010) "
                "gives human compartment-resolved expression and a progestin "
                "response of GLI1, i.e. the relay's UPSTREAM half only.",
                prior_support=(
                    "REF-026, mouse and rescue-grade. REF-075 supports the "
                    "human UPSTREAM half only, and GAP-014 records that NR2F2 "
                    "was not among its measured targets."
                ),
                overrides={"S_BMP2": "S_NR2F2"},
            ),
        ),
        gap_id="GAP-014",
        note=(
            "GAP-014 states the limit precisely: NR2F2/COUP-TFII was not among "
            "REF-075's measured targets, so even the correlative human link "
            "from Hedgehog output to NR2F2 is untested."
        ),
    ),
    Fork(
        "GP130",
        "gp130/STAT3 ligand identity",
        "Is E_GP130_STAT3 driven by LIF alone, as the committed three-way "
        "alias asserts, or by any gp130 ligand?",
        (
            MechanismClass(
                "GP130-a",
                "E_GP130_STAT3 = E_LIF (v0.4)",
                COMMITTED,
                "network.bnd",
                "E_LIF, E_GP130_STAT3 and E_CD98_CD9 are ONE Boolean function.",
                prior_support="none beyond the rule as committed.",
            ),
            MechanismClass(
                "GP130-b",
                "E_GP130_STAT3 = E_LIF or X_IL11",
                ADOPTABLE,
                _CURATED,
                "REF-072 (Marwood 2009): IL-11 and LIF both raise primary human "
                "EEC adhesion and integrin-alpha2, yet dissociate on phenotype. "
                "The variant breaks the ligand/pathway alias and does NOT "
                "represent that downstream divergence.",
                prior_support=(
                    "REF-072: IL-11 and LIF both act on primary human EEC, so "
                    "gp130 activity is not LIF alone."
                ),
                overrides={"E_GP130_STAT3": "E_LIF or X_IL11"},
                added_free=("X_IL11",),
            ),
        ),
        note=(
            "X_IL11 is supplied, never endogenous: the repository encodes no "
            "stromal IL-11 source, and REF-064 (Tanaka 2001) forbids one -- "
            "IL-11 has NO effect on unstimulated stroma and, in the "
            "co-stimulated arm, raises viability without raising prolactin."
        ),
    ),
    Fork(
        "CD98",
        "CD98/CD9 surface regulation",
        "Is surface CD98 availability a pure STAT3 readout, or is it induced "
        "by hCG and/or E2 independently?",
        (
            MechanismClass(
                "CD98-a",
                "E_CD98_CD9 = E_GP130_STAT3 (v0.4)",
                COMMITTED,
                "network.bnd",
                "",
                prior_support="none beyond the rule as committed.",
            ),
            MechanismClass(
                "CD98-b",
                "E_CD98_CD9 = E_GP130_STAT3 or IN_HCG",
                ADOPTABLE,
                _CURATED,
                "REF-008 (Dominguez 2010): human endometrial CD98 is essential "
                "for blastocyst adhesion and is induced by hCG, E2, LIF and EGF.",
                prior_support="REF-008 lists hCG among the inducers of human CD98.",
                overrides={"E_CD98_CD9": "E_GP130_STAT3 or IN_HCG"},
            ),
            MechanismClass(
                "CD98-c",
                "E_CD98_CD9 = E_GP130_STAT3 or IN_HCG or IN_E2",
                ADOPTABLE,
                _CURATED,
                "Same REF-008 induction list, read as including E2.",
                prior_support="REF-008 lists E2 among the same inducers.",
                overrides={"E_CD98_CD9": "E_GP130_STAT3 or IN_HCG or IN_E2"},
            ),
            MechanismClass(
                "CD98-x",
                "E_CD98_CD9 = 1 (constitutive; CD98 is not a switch)",
                CONFOUNDER_ONLY,
                _HERE,
                "An outcome favouring it -- CD98 detected wherever it is "
                "looked for -- licenses REOPENING whether E_CD98_CD9 is a "
                "switch at all, not adopting `E_CD98_CD9 = 1` as a rule: a "
                "constitutive node earns its place by what reads it, and that "
                "is a modelling question no single readout settles. SLC3A2/"
                "4F2hc is the heavy chain of the broadly expressed amino-acid "
                "transporter heterodimers, and REF-008 reports INDUCTION of an "
                "already-present protein rather than its appearance. Carried "
                "because it predicts the same 'CD98 detected' result as CD98-b "
                "and CD98-c in every arm, so a presence/absence surface readout "
                "cannot exclude it.",
                prior_support=(
                    "none as a rule. That SLC3A2 is a broadly expressed "
                    "transporter subunit is general biology, not a repository "
                    "row, which is exactly why this class is carried to be "
                    "excluded rather than proposed."
                ),
                overrides={"E_CD98_CD9": "IN_E2 or not IN_E2"},
            ),
        ),
        note=(
            "E_CD98_CD9's only consumers are E_RECEPTIVE_SURFACE and the "
            "redundant adhesion route, so the fork is maternal but terminal."
        ),
    ),
    Fork(
        "PC6",
        "PC6 enzyme versus DAG1 substrate state",
        "Is cleaved alpha-dystroglycan identical to PC6 activity, as v0.4 "
        "asserts, or does it also depend on substrate availability?",
        (
            MechanismClass(
                "PC6-a",
                "E_DAG1_CLEAVED = E_PC6; E_DAG1_FULL = not E_PC6 (v0.4)",
                COMMITTED,
                "network.bnd",
                "",
                prior_support=(
                    "none beyond the rule as committed, and REF-011 contradicts it."
                ),
            ),
            MechanismClass(
                "PC6-b",
                "E_DAG1_CLEAVED = E_PC6 and E_DAG1_CLEAVABLE",
                ADOPTABLE,
                _CURATED,
                "REF-011 (Heng 2015): full-length DAG1 is a barrier and PC6 "
                "cleavage creates the adhesion-permissive form; the paper ran "
                "both the knockdown and the cleavage-resistant substrate.",
                prior_support=(
                    "REF-011: full-length DAG1 is a barrier and PC6 cleavage "
                    "creates the permissive form; the paper ran both the "
                    "knockdown and the cleavage-resistant substrate."
                ),
                overrides={
                    "E_DAG1_CLEAVED": "E_PC6 and E_DAG1_CLEAVABLE",
                    "E_DAG1_FULL": "not E_DAG1_CLEAVED",
                },
                added_free=("E_DAG1_CLEAVABLE",),
            ),
        ),
        note=(
            "E_DAG1_CLEAVABLE has no physiological determinant: the "
            "cleavage-site mutant is a laboratory construct, not a state ADOC "
            "varies. The candidate table records this as ACKNOWLEDGED ABSENT."
        ),
    ),
)


# --------------------------------------------------------------------------
# Experiments
# --------------------------------------------------------------------------

#: `protocol_status` values. An existing recorded state costs no new arm; an
#: existing PHASE the protocol passes through still costs a run if nothing was
#: sampled there; a new arm is a new condition.
EXISTING_RECORDED = "existing_recorded_state"
EXISTING_PHASE_NEW_SAMPLING = "existing_phase_new_sampling"
NEW_ARM = "new_arm"

EXPERIMENTS: tuple[Experiment, ...] = (
    Experiment(
        "observe_e2_primed",
        "E2-only priming, day 2 (observation only)",
        "e2_primed_maternal",
        kind="observation_only",
        protocol_status=EXISTING_PHASE_NEW_SAMPLING,
        assay_note=(
            "PAEP at this phase is already recorded (OM-001). Any CELL-surface "
            "readout here is new: every ADOC measurement in "
            "input_tables/adoc_secreted_proteins.tsv is a secretome ELISA "
            "(PAEP, IGFBP-1, PRL) and no cell-associated protein has ever been "
            "measured on the platform."
        ),
        perturbations=0,
        feasibility="No intervention; cannot fail to engage a target.",
    ),
    Experiment(
        "observe_hormone_treated",
        "Full cocktail, day 6 (observation only)",
        "hormone_treated_maternal",
        kind="observation_only",
        protocol_status=EXISTING_RECORDED,
        assay_note="PAEP and IGFBP-1 recorded (OM-001, OM-002).",
        perturbations=0,
        feasibility="Already run.",
    ),
    Experiment(
        "dropout_e2",
        "Cocktail minus E2 (MPA + cAMP + XAV939, days 2-6)",
        "hormone_treated_maternal",
        {"IN_E2": False},
        kind="reagent_omission",
        protocol_status=NEW_ARM,
        assay_note=(
            "No new assay. PAEP top outlet and IGFBP-1/PRL bottom outlet are "
            "the platform's three existing ELISAs."
        ),
        feasibility=(
            "Omission of one cocktail component after the normal E2 priming "
            "phase; no drug, no construct, no target-engagement risk. The "
            "residual risk is cell loss over four E2-free days, and confluence "
            "imaging is required in BOTH the epithelial and the stromal "
            "channel. Epithelial loss reads as the committed SEC-a on PAEP; "
            "stromal loss is the half more easily forgotten and the one that "
            "costs more, because S_IGFBP1 from the bottom outlet is the only "
            "thing separating SEC-a from the confounder SEC-d, so it reads as "
            "the SEC-d signature. See section 4 of "
            "docs/stage3_experiment_selection.md."
        ),
    ),
    Experiment(
        "dropout_camp",
        "Cocktail minus cAMP (E2 + MPA + XAV939, days 2-6)",
        "hormone_treated_maternal",
        {"IN_cAMP": False},
        kind="reagent_omission",
        protocol_status=NEW_ARM,
        assay_note="No new assay.",
        feasibility="Reagent omission; cannot fail to engage.",
    ),
    Experiment(
        "dropout_xav939",
        "Cocktail minus XAV939 (E2 + MPA + cAMP, days 2-6)",
        "hormone_treated_maternal",
        {"IN_XAV939": False},
        kind="reagent_omission",
        protocol_status=NEW_ARM,
        assay_note="No new assay.",
        feasibility="Reagent omission; cannot fail to engage.",
    ),
    Experiment(
        "add_hcg_on_hormone_treated",
        "Full cocktail + hCG",
        "hormone_treated_maternal",
        {"IN_HCG": True},
        kind="reagent_addition",
        protocol_status=NEW_ARM,
        assay_note="Surface CD98/CD9 is a new assay class for this platform.",
        feasibility="Recombinant hCG addition.",
    ),
    Experiment(
        "add_hcg_on_e2",
        "E2-only priming + hCG",
        "e2_primed_maternal",
        {"IN_HCG": True},
        kind="reagent_addition",
        protocol_status=NEW_ARM,
        assay_note="Surface CD98/CD9 is a new assay class for this platform.",
        feasibility="Recombinant hCG addition during the priming phase.",
    ),
    Experiment(
        "add_il11",
        "Full cocktail + recombinant IL-11",
        "hormone_treated_maternal",
        {"X_IL11": True},
        kind="reagent_addition",
        protocol_status=NEW_ARM,
        assay_note="pSTAT3 is a new assay class for this platform.",
        feasibility="Recombinant ligand.",
    ),
    Experiment(
        "anti_lif",
        "Full cocktail + LIF/LIFR neutralisation",
        "hormone_treated_maternal",
        clamps={"E_LIF": False},
        kind="biologic",
        protocol_status=NEW_ARM,
        assay_note="pSTAT3 is a new assay class for this platform.",
        feasibility="Neutralising antibody; needs its own engagement control.",
    ),
    Experiment(
        "anti_lif_plus_il11",
        "Full cocktail + LIF neutralisation + recombinant IL-11",
        "hormone_treated_maternal",
        {"X_IL11": True},
        clamps={"E_LIF": False},
        kind="biologic+reagent_addition",
        protocol_status=NEW_ARM,
        assay_note="pSTAT3 is a new assay class for this platform.",
        perturbations=2,
        feasibility="Violates the one-perturbation preference.",
    ),
    Experiment(
        "smo_antagonist",
        "Full cocktail + SMO antagonist (Hedgehog reception blockade)",
        "hormone_treated_maternal",
        clamps={"S_NR2F2": False},
        kind="small_molecule",
        protocol_status=NEW_ARM,
        assay_note=(
            "IGFBP-1/PRL need no new assay. A GLI1/PTCH1 pathway-activity "
            "readout in the stromal channel is new and is REQUIRED, because "
            "the committed model predicts no change and a null is otherwise "
            "indistinguishable from failed target engagement."
        ),
        feasibility=(
            "Small molecule on both channels. GAP-014's proposed_resolution "
            "names this arm. The clamp is an INTERPRETATION of the intervention, "
            "not a model of it: the network has no reception node, so blockade "
            "is applied to S_NR2F2 directly. That is defensible only because "
            "S_NR2F2 is aliased to E_IHH, and it would stop being defensible the "
            "moment a reception node existed."
        ),
    ),
    Experiment(
        "bmpr_inhibitor",
        "Full cocktail + BMP type-I receptor inhibitor",
        "hormone_treated_maternal",
        clamps={"S_BMP2": False},
        kind="small_molecule",
        protocol_status=NEW_ARM,
        assay_note="IGFBP-1/PRL need no new assay.",
        feasibility=(
            "Clamps a node the committed rules already make necessary for "
            "S_DECIDUALIZED, so the committed prediction is a near-certain "
            "loss of both stromal analytes."
        ),
    ),
    Experiment(
        "pc6_knockdown",
        "Full cocktail + PC6/PCSK5 knockdown",
        "hormone_treated_maternal",
        clamps={"E_PC6": False},
        kind="construct",
        protocol_status=NEW_ARM,
        assay_note="alpha-DG-N shedding is a new assay class.",
        feasibility="siRNA/shRNA in the epithelial channel.",
    ),
    Experiment(
        "dag1_cleavage_resistant",
        "Full cocktail + cleavage-resistant alpha-dystroglycan construct",
        "hormone_treated_maternal",
        {"E_DAG1_CLEAVABLE": False},
        kind="construct",
        protocol_status=NEW_ARM,
        assay_note="alpha-DG-N shedding is a new assay class.",
        feasibility=(
            "Requires transfecting primary epithelium with a mutant substrate; "
            "the candidate table records the determinant as absent from ADOC."
        ),
    ),
    Experiment(
        "anti_spp1",
        "Full cocktail + anti-SPP1",
        "hormone_treated_maternal",
        {"IN_ANTI_SPP1": True},
        kind="biologic",
        protocol_status=NEW_ARM,
        assay_note=(
            "No maternal readout exists: identifiability.py reports "
            "IN_ANTI_SPP1 as set_alone_no_shared_readout."
        ),
        feasibility="Neutralising antibody.",
    ),
    Experiment(
        "hand2_loss",
        "Full cocktail + siHAND2",
        "hormone_treated_maternal",
        {"IN_HAND2_LOSS": True},
        kind="construct",
        protocol_status=NEW_ARM,
        assay_note="HAND2 and FGF readouts are a new assay class.",
        feasibility="siRNA in the stromal channel.",
    ),
)


def _class_rules(
    base_rules: dict[str, str], klass: MechanismClass
) -> tuple[dict[str, str], list[str]]:
    rules = dict(base_rules)
    rules.update(klass.overrides)
    for node in klass.added_free:
        rules.setdefault(node, node)
    order = _topological_order(rules, {n for n in rules if rules[n].strip() == n})
    return rules, order


def _marginals(
    rules: dict[str, str],
    order: list[str],
    latent: tuple[str, ...],
    inputs: dict[str, bool],
) -> dict[str, float]:
    seeds, states, mask = _latent_seeds(latent)
    column = _evaluate(rules, order, seeds, mask, inputs)
    return {node: (column[node] & mask).bit_count() / states for node in rules}


def _experiment_inputs(
    experiment: Experiment, arms: dict[str, dict[str, bool]], fork: Fork
) -> dict[str, bool]:
    """Controlled inputs for this experiment, including every added free node.

    A free variable a fork's class introduces is EXPERIMENTER-CONTROLLED, so it
    is conditioned on at its current-design default unless this experiment moves
    it. Leaving it latent would marginalise over "IL-11 supplied" and "IL-11
    absent" and report a number no experiment can produce.
    """
    inputs = dict(arms[experiment.background])
    for klass in fork.classes:
        for node in klass.added_free:
            inputs.setdefault(node, INPUT_DEFAULTS.get(node, False))
    inputs.update(experiment.input_overrides)
    inputs.update(experiment.clamps)
    return inputs


def evaluate(root: Path | None = None, model_version: str = MODEL_VERSION) -> dict:
    """Every (experiment, fork, class pair) separation, with its readout tier.

    `model_version` defaults to the frozen v0.4 model this module's committed
    artifacts were computed against. U8 passes the adopted v0.5 model instead;
    nothing else about the computation -- forks, experiments, readout tiers --
    is a parameter, so a rerank cannot change the scoring along with the model.
    """
    active = root or repo_root()
    facts = load_identifiability(model_version, active)
    base_rules = parse_bnd_rules(resolve_model(model_version, active).network_bnd)
    arms = {arm.arm_id: dict(arm.inputs) for arm in facts.arms}
    tiers = {
        node: value
        for node, value in _readout_tier(active).items()
        if _is_maternal(node)
    }
    maternal = sorted(n for n in base_rules if _is_maternal(n))
    analytes = _analytes(active)

    results = []
    for experiment in EXPERIMENTS:
        if experiment.background not in arms:
            raise KeyError(
                f"{experiment.experiment_id}: no arm {experiment.background}"
            )
        per_fork = []
        for fork in FORKS:
            inputs = _experiment_inputs(experiment, arms, fork)
            predictions = {}
            for klass in fork.classes:
                rules, order = _class_rules(base_rules, klass)
                predictions[klass.class_id] = _marginals(
                    rules, order, facts.latent, inputs
                )
            pairs = []
            classes = fork.classes
            for i, left in enumerate(classes):
                for right in classes[i + 1 :]:
                    hits = []
                    for node in maternal:
                        a = predictions[left.class_id].get(node)
                        b = predictions[right.class_id].get(node)
                        if a is None or b is None or abs(a - b) <= 1e-12:
                            continue
                        tier = tiers.get(node, (NO_ASSAY, ""))
                        hits.append(
                            {
                                "node": node,
                                "left": round(a, 4),
                                "right": round(b, 4),
                                "opposite": {a, b} == {0.0, 1.0},
                                "readout_tier": tier[0],
                                "readout_note": tier[1],
                                "analyte": analytes.get(node, ""),
                            }
                        )
                    pairs.append(
                        {
                            "left": left.class_id,
                            "right": right.class_id,
                            "roles": (left.role, right.role),
                            "hits": hits,
                            "usable": [
                                h for h in hits if h["readout_tier"] == USABLE_ASSAY
                            ],
                            "usable_opposite": [
                                h
                                for h in hits
                                if h["readout_tier"] == USABLE_ASSAY and h["opposite"]
                            ],
                        }
                    )
            per_fork.append(
                {
                    "fork": fork.fork_id,
                    "axis": fork.axis,
                    "pairs": pairs,
                    "predictions": {
                        cid: {
                            node: round(value[node], 4)
                            for node in sorted(tiers)
                            if node in value
                        }
                        for cid, value in predictions.items()
                    },
                }
            )

        committed = _committed_change(base_rules, facts, arms, experiment, maternal)
        results.append(
            {
                "experiment": experiment.experiment_id,
                "label": experiment.label,
                "background": experiment.background,
                "kind": experiment.kind,
                "protocol_status": experiment.protocol_status,
                "perturbations": experiment.perturbations,
                "assay_note": experiment.assay_note,
                "feasibility": experiment.feasibility,
                # An arm with no overrides and no clamps moves nothing, so its
                # empty downstream set is arithmetic and carries no information
                # about the model. Derived, never declared alongside
                # `perturbations`, so the two cannot drift apart.
                "applies_nothing": not (
                    experiment.input_overrides or experiment.clamps
                ),
                "forks": per_fork,
                "forks_separated_any": sorted(
                    f["fork"] for f in per_fork if any(p["hits"] for p in f["pairs"])
                ),
                "forks_separated_usable_assay": sorted(
                    f["fork"] for f in per_fork if any(p["usable"] for p in f["pairs"])
                ),
                # Reached at `mapped_composite` but not better. Reported
                # separately rather than folded into either neighbour: the map
                # itself says such a row cannot validate its node, so this is
                # neither a usable separation nor a non-existent one.
                "forks_separated_mapped_composite": sorted(
                    f["fork"]
                    for f in per_fork
                    if not any(p["usable"] for p in f["pairs"])
                    and any(
                        h["readout_tier"] == MAPPED_COMPOSITE
                        for p in f["pairs"]
                        for h in p["hits"]
                    )
                ),
                # Reached ONLY where nothing can be measured. A fork here is a
                # difference between two model states, not an experiment.
                "forks_separated_no_assay_only": sorted(
                    f["fork"]
                    for f in per_fork
                    if any(p["hits"] for p in f["pairs"])
                    and all(
                        h["readout_tier"] == NO_ASSAY
                        for p in f["pairs"]
                        for h in p["hits"]
                    )
                ),
                "forks_separated_usable_opposite": sorted(
                    f["fork"]
                    for f in per_fork
                    if any(p["usable_opposite"] for p in f["pairs"])
                ),
                "committed_model_changes": committed,
            }
        )
    return {
        "model_version": model_version,
        "results": results,
        "readout_tiers": tiers,
        "analytes": analytes,
        "latent": list(facts.latent),
        "maternal_nodes": maternal,
    }


def _committed_change(
    base_rules: dict[str, str],
    facts,
    arms: dict[str, dict[str, bool]],
    experiment: Experiment,
    maternal: list[str],
) -> list[str]:
    """Maternal nodes the COMMITTED model moves DOWNSTREAM of the intervention.

    The node an intervention clamps always "changes", and counting it would let
    every drug look as though the model predicted an effect. Only nodes the
    experiment does not set directly are counted, so an empty list means the
    committed model predicts the intervention propagates nowhere.

    An experiment whose committed prediction is "nothing propagates" is not
    thereby worthless -- a predicted null is falsifiable -- but a negative
    result is then indistinguishable from failed target engagement, and that is
    a design requirement rather than a footnote. This column is what makes that
    visible.
    """
    order = _topological_order(
        base_rules, {n for n in base_rules if base_rules[n].strip() == n}
    )
    background = dict(arms[experiment.background])
    treated = {**background, **experiment.input_overrides, **experiment.clamps}
    before = _marginals(base_rules, order, facts.latent, background)
    after = _marginals(base_rules, order, facts.latent, treated)
    set_directly = set(experiment.input_overrides) | set(experiment.clamps)
    return [
        n
        for n in maternal
        if n not in set_directly and abs(before[n] - after[n]) > 1e-12
    ]


def _analytes(root: Path) -> dict[str, str]:
    """Per model node: the physical analyte and outlet the map records for it.

    Derived, so the report can never name a measurement the observation layer
    does not actually hold.
    """
    found: dict[str, str] = {}
    with (root / "config/observation_model_map.tsv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("activation_status", "").strip() not in {
                "active_constraint",
                "active_diagnostic",
            }:
                continue
            label = row["protein"].strip()
            outlet = row.get("outlet", "").strip()
            if outlet:
                label = f"{label} ({outlet} outlet)"
            for node in row.get("model_nodes", "").split(";"):
                node = node.strip()
                if node:
                    found.setdefault(node, label)
    return found


#: Column order for the TSV. One row per (experiment, fork, class pair).
TSV_COLUMNS = (
    "experiment",
    "background",
    "kind",
    "protocol_status",
    "perturbations",
    "fork",
    "left_class",
    "right_class",
    "class_roles",
    "separating_nodes",
    "usable_assay_nodes",
    "usable_assay_opposite_nodes",
    "usable_assay_analytes",
    "committed_model_changes_anything",
)


def _rows(report: dict) -> list[list[str]]:
    rows: list[list[str]] = []
    for result in report["results"]:
        for fork in result["forks"]:
            for pair in fork["pairs"]:
                rows.append(
                    [
                        result["experiment"],
                        result["background"],
                        result["kind"],
                        result["protocol_status"],
                        str(result["perturbations"]),
                        fork["fork"],
                        pair["left"],
                        pair["right"],
                        "/".join(pair["roles"]),
                        ";".join(h["node"] for h in pair["hits"]),
                        ";".join(h["node"] for h in pair["usable"]),
                        ";".join(h["node"] for h in pair["usable_opposite"]),
                        ";".join(
                            sorted(
                                {h["analyte"] for h in pair["usable"] if h["analyte"]}
                            )
                        ),
                        str(bool(result["committed_model_changes"])),
                    ]
                )
    return rows


#: scRNA observability levels that could in principle carry evidence about a
#: fork. `proxy_abundance_not_activity` is excluded on purpose: transcript
#: abundance is not surface availability or pathway activity, which is the exact
#: distinction the CD98 and GP130 forks turn on.
SCRNA_OBSERVABLE = frozenset({"direct_transcript", "regulon_activity", "gene_program"})


#: The conditions the deposited scRNA object actually contains, derived from the
#: committed per-unit table the KLF12 workstream produced rather than asserted.
#: This is the fact that decides what that dataset can and cannot separate, and
#: it is independent of observability: a contrast that is not in the data cannot
#: be measured however well the genes are detected.
SCRNA_UNIT_TABLE = Path("docs/scrna/klf12_state_evidence.tsv")


def _scrna_conditions(root: Path) -> tuple[list[str], list[str]]:
    """``(conditions, donors)`` present in the deposited object."""
    path = root / SCRNA_UNIT_TABLE
    if not path.exists():
        return ([], [])
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    return (
        sorted({r["condition"].strip() for r in rows if r.get("condition")}),
        sorted({r["donor"].strip() for r in rows if r.get("donor")}),
    )


def _scrna_can_alter_a_readout_tier(root: Path) -> tuple[bool, list[str]]:
    """Could any scRNA finding move a node into the usable-assay tier?

    The ranking's deciding criterion is "separates a fork on a readout that
    EXISTS", and that tier comes from `config/observation_model_map.tsv` alone --
    `_readout_tier` reads nothing else. The scRNA layer has its own map and, if
    no row of it is activated, it contributes no usable assay to any node. That
    makes the tier assignment invariant under every possible scRNA result, which
    is the load-bearing step in the ranking-invariance argument: a finding can
    change how much we CARE about a fork without changing whether the fork can
    be READ.
    """
    with (root / "config/scrna_observation_map.tsv").open(encoding="utf-8") as fh:
        statuses = sorted(
            {
                (r.get("activation_status") or "").strip()
                for r in csv.DictReader(fh, delimiter="\t")
            }
        )
    return (bool(set(statuses) & _ACTIVE_STATUSES), statuses)


def _scrna_rows(root: Path) -> dict[str, dict[str, str]]:
    with (root / "config/scrna_observation_map.tsv").open(encoding="utf-8") as fh:
        return {r["model_node"].strip(): r for r in csv.DictReader(fh, delimiter="\t")}


def _scrna_verdict(nodes: list[dict[str, str]]) -> str:
    """Can the committed scRNA layer move this fork? Derived, never asserted.

    A pure function of the SEPARATING quantities -- the ones whose values differ
    between the fork's classes. Intervention observability is deliberately not an
    argument: being able to see the thing you perturb constrains nothing if you
    cannot see the consequence that tells the classes apart. An earlier version
    took interventions too, and it let `GP130`'s observable `E_LIF` divert a fork
    whose only separator is unobservable into `PROXY_LEVEL_ONLY` -- a verdict
    whose own definition was false of it, and which `PC6`, with the identical
    separator, did not get.

    The question is NOT whether a gene is in the dataset. It is whether the
    quantity that SEPARATES the fork's classes is observable at a defensible
    level, from evidence that did not build the model it would be testing. Three
    ways to fail, and they are different failures:

    * `NOT_OBSERVABLE` -- nothing that separates the classes has an RNA
      observable at all.
    * `PROXY_LEVEL_ONLY` -- the best separator is transcript abundance where the
      fork is about surface availability or pathway activity.
    * `CONSTRUCTION_ROLE_ONLY` -- observable at a defensible level, but every
      such separator has `evidence_role = construction`, i.e. it helped build
      v0.4. Using it to judge v0.4 is leakage, not evidence.
    """
    observable = [
        n for n in nodes if n.get("measurement_observability") in SCRNA_OBSERVABLE
    ]
    if observable:
        if all(n.get("evidence_role") == "construction" for n in observable):
            return "CONSTRUCTION_ROLE_ONLY"
        return "IN_PRINCIPLE_CONSTRAINABLE"
    if any(
        n.get("measurement_observability") == "proxy_abundance_not_activity"
        for n in nodes
    ):
        return "PROXY_LEVEL_ONLY"
    return "NOT_OBSERVABLE"


def _scrna_assessment(report: dict, root: Path) -> list[dict]:
    """Per fork: what the committed scRNA layer could and could not say.

    Scoped to the quantities the DECISION rests on, not to everything that
    co-moves. A fork is decided at the best readout tier any arm reaches for
    it, so that tier fixes both the separating nodes and the interventions
    considered: unioning across every arm makes a fork look observable because
    some unrelated arm happens to move a measurable node.
    """
    scrna = _scrna_rows(root)
    by_experiment = {e.experiment_id: e for e in EXPERIMENTS}
    order = (USABLE_ASSAY, MAPPED_COMPOSITE, NO_ASSAY)
    out = []
    for fork in FORKS:
        per_tier: dict[str, tuple[set[str], set[str]]] = {
            tier: (set(), set()) for tier in order
        }
        for result in report["results"]:
            entry = next(f for f in result["forks"] if f["fork"] == fork.fork_id)
            experiment = by_experiment[result["experiment"]]
            for pair in entry["pairs"]:
                for hit in pair["hits"]:
                    nodes, inputs = per_tier[hit["readout_tier"]]
                    nodes.add(hit["node"])
                    inputs.update(experiment.input_overrides)
                    inputs.update(experiment.clamps)
        best = next((t for t in order if per_tier[t][0]), NO_ASSAY)
        separating, interventions = per_tier[best]
        nodes = [scrna[n] for n in sorted(separating) if n in scrna]
        inputs = [scrna[n] for n in sorted(interventions) if n in scrna]
        out.append(
            {
                "fork": fork.fork_id,
                "axis": fork.axis,
                "decided_at": best,
                "verdict": _scrna_verdict(nodes),
                "separating": [
                    (
                        n["model_node"],
                        n.get("measurement_observability", ""),
                        n.get("evidence_role", ""),
                    )
                    for n in nodes
                ],
                "interventions": [
                    (i["model_node"], i.get("measurement_observability", ""))
                    for i in inputs
                ],
            }
        )
    return out


def _propagation_cell(result: dict) -> str:
    """The propagation column, which is a question only an intervention raises."""
    if result["applies_nothing"]:
        return "n/a"
    return "yes" if result["committed_model_changes"] else "**no**"


def _pair_index(report: dict) -> list[tuple[str, str, list[str], str]]:
    """Per class pair: the experiments that separate it and the best tier reached.

    Read this before the summary table. An axis can look alive there because
    SOME pair of its classes is separable, while the pair that would actually
    settle it is separable nowhere -- which is a reason to stop spending on that
    axis, not a detail.
    """
    order = {USABLE_ASSAY: 0, MAPPED_COMPOSITE: 1, NO_ASSAY: 2}
    found: dict[tuple[str, str], tuple[list[str], str]] = {}
    for result in report["results"]:
        for fork in result["forks"]:
            for pair in fork["pairs"]:
                key = (fork["fork"], f"{pair['left']} vs {pair['right']}")
                experiments, tier = found.setdefault(key, ([], NO_ASSAY))
                if not pair["hits"]:
                    continue
                experiments.append(result["experiment"])
                best = min((h["readout_tier"] for h in pair["hits"]), key=order.get)
                if order[best] < order[tier]:
                    found[key] = (experiments, best)
    return [
        (fork_id, pair_key, experiments, tier if experiments else "unreachable")
        for (fork_id, pair_key), (experiments, tier) in found.items()
    ]


def render(report: dict, task: str = "build-stage3-design") -> str:
    lines: list[str] = []
    a = lines.append
    # The banner carries no generation date. A wall-clock stamp made an
    # unchanged report rewrite itself on a new day, so a clean checkout went
    # dirty for nothing; pinned by
    # test_generated_date_determinism.ClockFrozenRegenerationTest.
    a("# Stage 3 — which single experiment separates which maternal mechanism")
    a("")
    a(
        "> **Generated file — do not edit.** Regenerate with "
        f"`pixi run {task}`. Computed by conditioning the committed "
        f"`{report['model_version']}` network, and each mechanism class's in-memory rule "
        "substitution, on every candidate experiment's controlled inputs and "
        "intervention clamps. No MaBoSS run; no committed file is modified."
    )
    a("")
    a(
        "Latent variables marginalised: "
        + ", ".join(f"`{n}`" for n in report["latent"])
        + ". Experimenter-controlled inputs are conditioned on, never "
        "marginalised."
    )
    a("")
    a("## Readouts the observation layer can actually validate")
    a("")
    a("| Node | Analyte | Tier |")
    a("|---|---|---|")
    for node, (tier, note) in sorted(report["readout_tiers"].items()):
        analyte = report["analytes"].get(node) or note or "—"
        a(f"| `{node}` | {analyte} | `{tier}` |")
    a("")
    a(
        "Everything else is `no_assay`. A separation reported below at a node "
        "absent from this table is a difference between two model states."
    )
    a("")

    a("## Summary: what each candidate experiment separates")
    a("")
    a(
        "| Experiment | Protocol | Perturbations | Forks separated | "
        "…on a usable assay | …at `mapped_composite` only | "
        "…at `no_assay` only | …with opposite predictions | "
        "Committed model propagates downstream? |"
    )
    a("|---|---|---|---|---|---|---|---|---|")
    for r in report["results"]:
        a(
            f"| `{r['experiment']}` | `{r['protocol_status']}` | "
            f"{r['perturbations']} | "
            f"{', '.join(r['forks_separated_any']) or '—'} | "
            f"**{', '.join(r['forks_separated_usable_assay']) or 'none'}** | "
            f"{', '.join(r['forks_separated_mapped_composite']) or '—'} | "
            f"{', '.join(r['forks_separated_no_assay_only']) or '—'} | "
            f"**{', '.join(r['forks_separated_usable_opposite']) or 'none'}** | "
            f"{_propagation_cell(r)} |"
        )
    a("")
    a(
        "> The three tier columns partition the fourth: every fork an arm "
        "separates appears in exactly one of them. `CD98` lands in the "
        "`no_assay` column for **every** arm in the catalogue, which is the "
        "single fact about that axis worth carrying — it is separable in many "
        "arms and decidable in none of them."
    )
    a("")
    a(
        "> The last column is about INTERVENTIONS only, and reads `n/a` for the "
        "observation-only arms. An arm that applies nothing has an empty "
        "downstream set for any network whatever — the two marginals are "
        "computed from identical inputs — so printing **no** there would be a "
        "demerit the computation never tested."
    )
    a(
        "> For an intervention, a **no** is not a disqualification — a predicted "
        "null is falsifiable — but it means a negative result is "
        "indistinguishable from failed target engagement unless the design "
        "carries its own engagement control."
    )
    a("")

    a("## Which experiment separates which class pair")
    a("")
    a(
        "The inverse of the summary table, and the one that catches a fork no "
        "candidate can close. A pair listed with `(none)` is unreachable by "
        "every experiment in this catalogue, whatever the readout; a pair "
        "reachable only at `no_assay` is unreachable today."
    )
    a("")
    a("| Fork | Pair | Separated by | Best readout tier |")
    a("|---|---|---|---|")
    for fork_id, pair_key, experiments, tier in _pair_index(report):
        a(
            f"| {fork_id} | `{pair_key}` | "
            + (", ".join(f"`{x}`" for x in experiments) or "**(none)**")
            + f" | `{tier}` |"
        )
    a("")

    a("## Forks")
    a("")
    for fork in FORKS:
        a(f"### {fork.fork_id} — {fork.axis}")
        a("")
        a(f"*{fork.question}*")
        a("")
        if fork.gap_id:
            a(f"Recorded evidence gap: `{fork.gap_id}`.")
            a("")
        a(
            "`role` says what an outcome favouring the class would LICENSE — a "
            "rule change directly, or only opening an evidence gap. It is not "
            "a claim about how well supported the class already is, which is "
            "the separate `prior support` column and may be `none`."
        )
        a("")
        a(
            "| Class | Rule | Role (what an outcome licenses) | Prior support | Provenance |"
        )
        a("|---|---|---|---|---|")
        for klass in fork.classes:
            a(
                f"| `{klass.class_id}` | {klass.label} | `{klass.role}` | "
                f"{klass.prior_support} | {klass.provenance} |"
            )
        a("")
        for klass in fork.classes:
            if klass.evidence:
                a(f"* `{klass.class_id}` — {klass.evidence}")
        a("")
        if fork.note:
            a(f"> {fork.note}")
            a("")

    a("## Per-experiment detail")
    a("")
    for r in report["results"]:
        a(f"### `{r['experiment']}` — {r['label']}")
        a("")
        a(f"Background `{r['background']}`; {r['kind']}; `{r['protocol_status']}`.")
        a("")
        a(f"* **Assay:** {r['assay_note']}")
        a(f"* **Feasibility:** {r['feasibility']}")
        changes = r["committed_model_changes"]
        if r["applies_nothing"]:
            propagation = "n/a — this arm applies no intervention"
        elif changes:
            propagation = ", ".join(f"`{n}`" for n in changes)
        else:
            propagation = "**nothing propagates**"
        a(f"* **Committed model, downstream of the intervention:** {propagation}")
        a("")
        any_hit = False
        for fork in r["forks"]:
            for pair in fork["pairs"]:
                if not pair["hits"]:
                    continue
                any_hit = True
                a(f"**{fork['fork']}: {pair['left']} vs {pair['right']}**")
                a("")
                a(
                    f"| Node | {pair['left']} | {pair['right']} | opposite | "
                    "readout tier | analyte |"
                )
                a("|---|---|---|---|---|---|")
                for h in pair["hits"]:
                    a(
                        f"| `{h['node']}` | {h['left']} | {h['right']} | "
                        f"{'**yes**' if h['opposite'] else 'no'} | "
                        f"`{h['readout_tier']}` | {h['analyte'] or '—'} |"
                    )
                a("")
        if not any_hit:
            a("Separates no fork: every class predicts the same maternal state.")
            a("")
    return "\n".join(lines) + "\n"


def _mechanism_tested(result: dict) -> str:
    """The axes this arm separates on a readout that exists, derived.

    Hand-written, this column said things like "CD98 regulation" for an arm
    whose only CD98 separation is unmeasurable. Derived, it cannot.
    """
    axes = []
    for fork in FORKS:
        if fork.fork_id in result["forks_separated_usable_assay"]:
            axes.append(f"{fork.axis} (`usable_assay`)")
        elif fork.fork_id in result["forks_separated_mapped_composite"]:
            axes.append(f"{fork.axis} (`mapped_composite`)")
    return "; ".join(axes) or "**nothing measurable**"


def _separated_cell(result: dict) -> str:
    """Forks separated on a readout that exists, with every pair named.

    One rule, applied by the generator, so no cell can be an exception to it.
    Everything reachable only at `no_assay` is excluded here and appears in the
    `no_assay only` column of the summary and in the pair index.
    """
    parts = []
    for fork in result["forks"]:
        if fork["fork"] not in set(result["forks_separated_usable_assay"]) | set(
            result["forks_separated_mapped_composite"]
        ):
            continue
        for pair in fork["pairs"]:
            usable = sorted({h["node"] for h in pair["usable"]})
            composite = sorted(
                {
                    h["node"]
                    for h in pair["hits"]
                    if h["readout_tier"] == MAPPED_COMPOSITE
                }
            )
            if not usable and not composite:
                continue
            # The tiers are never merged into one list. A `mapped_composite`
            # node is one the map itself says cannot validate its node, so a
            # separation resting only on those is not runnable today, and a
            # reader must be able to see which is which without looking it up.
            nodes = ", ".join(f"**`{n}`**" for n in usable)
            if composite:
                nodes += (", " if usable else "") + ", ".join(
                    f"`{n}` (composite)" for n in composite
                )
            parts.append(f"{pair['left']}/{pair['right'].split('-')[-1]} on {nodes}")
    if not parts:
        excluded = ", ".join(result["forks_separated_no_assay_only"])
        return "**none**" + (
            f" (reaches {excluded}, at `no_assay`)" if excluded else ""
        )
    return "; ".join(parts)


def render_tables(report: dict, root: Path) -> str:
    """The three tables the selection document cites instead of restating.

    v0.4 only. Its prose argues about the frozen v0.4 model by name, so
    rendering it for another version would print v0.4 claims under a v0.5
    heading; the U8 rerank reports its own comparison instead.
    """
    if report["model_version"] != MODEL_VERSION:
        raise ValueError(
            f"render_tables is written about {MODEL_VERSION}, not "
            f"{report['model_version']}"
        )
    structure = load_structure(MODEL_VERSION, root)
    lines: list[str] = []
    a = lines.append
    a("# Stage 3 — decision tables")
    a("")
    a(
        "> **Generated file — do not edit.** Regenerate with "
        "`pixi run build-stage3-design`. "
        "[`../stage3_experiment_selection.md`](../stage3_experiment_selection.md) "
        "cites these tables and deliberately does not restate them: five review "
        "rounds on that document found one class of defect and nothing else -- a "
        "statement about the work that the work contradicted, usually a "
        "hand-written sentence refuted by a computed cell."
    )
    a("")

    a("## A. What the committed model collapses")
    a("")
    facts = load_identifiability(MODEL_VERSION, root)
    inputs = [n for n in structure.free if n.startswith("IN_")]
    relays = [n for n in structure.free if n.startswith("X_")]
    other = [n for n in structure.free if not n.startswith(("IN_", "X_"))]
    never_set = sorted(set(inputs) - set(facts.controlled))
    a(
        f"`{MODEL_VERSION}`: **{len(structure.node_ids)} nodes**, "
        f"**{structure.distinct_function_count} distinct Boolean functions** over "
        f"**{len(structure.free)} free variables**. Every group below realises one "
        "function, so no experiment separates its members while the rules say "
        "what they say."
    )
    a("")
    a(
        "**Free and latent are different sets, and the decomposition is counted "
        "here rather than written by hand.** The "
        f"{len(structure.free)} free variables are "
        f"{len(inputs)} declared `IN_*` inputs, {len(relays)} `X_*` relays and "
        + ", ".join(f"`{n}`" for n in other)
        + f". Of those, **{len(facts.latent)} are latent** — the free variables "
        "no arm assigns, whose per-unit value is unknown and is marginalised "
        f"over: " + ", ".join(f"`{n}`" for n in facts.latent) + ". "
        f"**{len(facts.controlled)}** are assigned by some recorded arm"
        + (
            ", and "
            + ", ".join(f"`{n}`" for n in never_set)
            + " is declared but assigned by no RECORDED arm -- a condition cfg "
            "may still set it, and `hormone_treated_hand2_loss.cfg` does; it is "
            "simply not an arm the repository holds an observation for"
            if never_set
            else ""
        )
        + ". *Free* is a property of the rules; *latent* is a property of the "
        "design."
    )
    a("")
    a("| Size | Class | Contains a usable assay? |")
    a("|---|---|---|")
    usable = {
        node
        for node, (tier, _note) in report["readout_tiers"].items()
        if tier == USABLE_ASSAY
    }
    for klass in sorted(structure.alias_classes, key=lambda c: (-len(c), c)):
        if len(klass) < 2:
            continue
        hit = sorted(set(klass) & usable)
        a(
            f"| {len(klass)} | "
            + " ".join(f"`{n}`" for n in klass)
            + " | "
            + (", ".join(f"`{n}`" for n in hit) if hit else "no")
            + " |"
        )
    a("")
    if structure.unread_inputs:
        a(
            "Inputs **no rule reads**, so the model predicts they do nothing: "
            + ", ".join(f"`{n}`" for n in sorted(structure.unread_inputs))
            + "."
        )
        a("")

    a("## B. Candidate comparison")
    a("")
    a(
        "Computed columns come from the same evaluation as "
        "[`stage3_experiment_design.md`](stage3_experiment_design.md); the "
        "protocol, assay and feasibility columns are curated declarations on "
        "each `Experiment` in `src/dt_adoc/experiments/stage3_design.py`. "
        "Neither is retyped anywhere."
    )
    a("")
    a(
        "**Bold** nodes carry a usable assay; `(composite)` marks a node the "
        "observation map maps but says cannot validate, so a separation resting "
        "only on those is not runnable today."
    )
    a("")
    a(
        "| Experiment | Axis separated on a readout that exists | Class pairs "
        "separated | Protocol | Assay | Perturbations | Propagates? |"
    )
    a("|---|---|---|---|---|---|---|")
    for r in report["results"]:
        mark = "**" if r["experiment"] == RECOMMENDED else ""
        a(
            f"| {mark}`{r['experiment']}`{mark} | {_mechanism_tested(r)} | "
            f"{_separated_cell(r)} | `{r['protocol_status']}` | "
            f"{r['assay_note']} | {r['perturbations']} | "
            f"{_propagation_cell(r)} |"
        )
    a("")
    a("Feasibility, as declared per experiment:")
    a("")
    for r in report["results"]:
        a(f"* `{r['experiment']}` — {r['feasibility']}")
    a("")

    a(f"## C. `{RECOMMENDED}`: predictions by mechanism class")
    a("")
    a(
        "The outcome table of the recommended arm, on the nodes the observation "
        "layer can validate. The **model action** each row licenses is a curated "
        "judgement and lives in §5 of the selection document; the predictions "
        "are computed and live here."
    )
    a("")
    recommended = next(r for r in report["results"] if r["experiment"] == RECOMMENDED)
    fork = next(f for f in recommended["forks"] if f["fork"] == RECOMMENDED_FORK)
    readouts = [
        node
        for node in sorted(report["readout_tiers"])
        if report["readout_tiers"][node][0] == USABLE_ASSAY
    ]
    a(
        "| Class | "
        + " | ".join(
            f"`{n}` — {report['analytes'].get(n, 'unmapped').replace(' (', ', ').rstrip(')')}"
            for n in readouts
        )
        + " |"
    )
    a("|---" * (len(readouts) + 1) + "|")
    for klass in next(f for f in FORKS if f.fork_id == RECOMMENDED_FORK).classes:
        values = fork["predictions"][klass.class_id]
        a(
            f"| `{klass.class_id}` ({klass.role}) | "
            + " | ".join(
                (
                    "**ON**"
                    if values[n] == 1.0
                    else "**OFF**"
                    if values[n] == 0.0
                    else str(values[n])
                )
                for n in readouts
            )
            + " |"
        )
    a("")
    a(
        "Distinct predicted patterns: "
        + str(
            len(
                {
                    tuple(fork["predictions"][k.class_id][n] for n in readouts)
                    for k in next(
                        f for f in FORKS if f.fork_id == RECOMMENDED_FORK
                    ).classes
                }
            )
        )
        + f", over {len(next(f for f in FORKS if f.fork_id == RECOMMENDED_FORK).classes)} classes."
    )
    a("")
    a("## D. Mechanism classes")
    a("")
    a(
        "`role` records what an outcome favouring the class would LICENSE -- a "
        "rule change directly, or only opening an evidence gap. It is **not** a "
        "claim that the repository already supports the class: prior support is "
        "the separate column, and `none` is an admissible entry that `SEC-b` "
        "actually carries."
    )
    a("")
    a("| Fork | Class | Rule | Role | Prior support | Provenance |")
    a("|---|---|---|---|---|---|")
    for fork_def in FORKS:
        for klass in fork_def.classes:
            a(
                f"| {fork_def.fork_id} | `{klass.class_id}` | {klass.label} | "
                f"`{klass.role}` | {klass.prior_support} | {klass.provenance} |"
            )
    a("")

    a("## E. What the committed scRNA layer can and cannot settle")
    a("")
    a(
        "Derived from `config/scrna_observation_map.tsv`, scoped to the "
        "quantities each fork is actually DECIDED on -- the separating nodes at "
        "the best readout tier any arm reaches for it, plus the interventions "
        "of the arms that reach it. This answers one question and not a wider "
        "one: **can evidence already in hand move a fork, before any new "
        "biological material is spent?**"
    )
    a("")
    a(
        "The verdict is a function of the **separating** quantities only. The "
        "intervention is listed after the `·` as context and does not enter it: "
        "being able to see what an arm perturbs constrains nothing if the "
        "consequence that tells the classes apart cannot be seen. An earlier "
        "version let it in, and `GP130` and `PC6` -- identical separators -- "
        "came out with different verdicts."
    )
    a("")
    a("| Fork | Axis | Decided at | scRNA verdict | Deciding quantities |")
    a("|---|---|---|---|---|")
    for entry in _scrna_assessment(report, root):
        quantities = (
            "; ".join(
                f"`{node}` ({level}, {role})"
                for node, level, role in entry["separating"]
            )
            or "—"
        )
        inputs = "; ".join(
            f"`{node}` ({level})" for node, level in entry["interventions"]
        )
        if inputs:
            quantities += f" · intervention: {inputs}"
        a(
            f"| {entry['fork']} | {entry['axis']} | `{entry['decided_at']}` | "
            f"**{entry['verdict']}** | {quantities} |"
        )
    a("")
    _activated, _statuses = _scrna_can_alter_a_readout_tier(root)
    a(
        "> Two caveats apply to **every** row and are why no verdict above is "
        "`SUPPORTED` or `CONTRADICTED`. The first is that **no row of the scRNA "
        "map carries an ACTIVE status** -- the statuses present are "
        + ", ".join(f"`{x}`" for x in _statuses)
        + ", counted from the file rather than asserted -- so nothing there is "
        "activated, and `config/external_data_manifest.tsv` records that no "
        "model node is conditioned on the object and that it constrains "
        "nothing. The second is that the map records near-total confounding "
        "between cell label and condition (Luminal-like epithelium 0.8% HT "
        "against HT epithelium I 79.1%), so a between-condition contrast in "
        "that data is not separable from a between-label one."
    )
    a("")
    conditions, donors = _scrna_conditions(root)
    a(
        "> **Why the `SEC` fork cannot be decided there, stated as a design "
        "fact rather than as a label.** `CONSTRUCTION_ROLE_ONLY` says the "
        "deciding readouts helped build v0.4, so they cannot serve as "
        "independent validation of it. That alone would not settle the "
        "question, because Stage 3 is choosing an experiment to CALIBRATE an "
        "underidentified twin, and construction-role data may legitimately "
        "inform calibration provided nothing later claims it as held-out "
        "validation. The decisive reason is the design of the deposited "
        "experiment itself: it contains "
        + f"**{len(conditions)} conditions ({', '.join(conditions)})** across "
        + f"{len(donors)} donors, and `HT` moves E2, MPA, cAMP and XAV939 "
        "**together**. The contrast that separates `SEC-a` from `SEC-b` is an "
        "E2 dropout against a matched full cocktail, and that contrast does not "
        "exist in the data. No amount of detection quality creates it."
    )
    a("")
    a(
        "> **Controlled inputs are known, not inferred.** `IN_E2` and `IN_cAMP` "
        "appear in the map as `not_observable`, and that is the wrong frame for "
        "reading this table: they are experimenter-set, so their values are "
        "known from the protocol and never need to be recovered from RNA. The "
        "real limitation is causal rather than observational -- `CNT` versus "
        "`HT` is a bundled intervention, so a transcript programme that differs "
        "between them cannot be attributed to E2, to MPA, to cAMP or to XAV939 "
        "individually. That is the same bundling `U1` records for the ADOC "
        "secretome, in the same protocol, and it is why the recommended arm is "
        "a single-component dropout."
    )
    a("")

    a("## F. What no scRNA result can change (a conditional invariance)")
    a("")
    a(
        'Asked because a reviewer was right that "it is not what the '
        'recommendation turns on" is not an argument. What is proved here is '
        'narrower than "the preference is invariant", and the heading says so:'
    )
    a("")
    a(
        "> Under the frozen v0.4 model and the current observation-activation "
        "policy, no scRNA finding can add or remove an arm from the set that "
        "separates a fork on an already-usable assay."
    )
    a("")
    a(
        "Preference also weighs which uncertainty stays credible, how many "
        "classes an arm separates, target-engagement ambiguity, assay cost and "
        "robustness. A strong scRNA finding can move that uncertainty set "
        "without touching any `readout_tier`, so this bounds the candidate set "
        "and not the ordering within it."
    )
    a("")
    activated, statuses = _scrna_can_alter_a_readout_tier(root)
    a(
        f"1. **The ranking criterion is a tier, and scRNA cannot set one.** An "
        f"arm is preferred here for separating a fork on a readout that EXISTS, "
        f"and that tier is computed by `_readout_tier` from "
        f"`config/observation_model_map.tsv` **and nothing else**. Every row of "
        f"`config/scrna_observation_map.tsv` carries "
        f"`activation_status` in {{{', '.join('`' + x + '`' for x in statuses)}}}"
        + (
            " -- which includes an active status, so this step does NOT hold "
            "and the argument below must be rerun."
            if activated
            else " -- none of them active. So no scRNA finding promotes any "
            "node to `usable_assay`."
        )
    )
    a("")
    a(
        "2. **The forks an AC04 result bears on are not decided at that tier.** "
        "`GP130` is decided at `mapped_composite_not_validating` and `CD98` at "
        "`no_assay` (table E). Strong support for the `E_LIF`/`E_GP130_STAT3`/"
        "`E_CD98_CD9` aliasing leaves both where they are; strong contradiction "
        "makes both *more* worth resolving and still leaves both where they "
        "are, because step 1 says the tier cannot move. A fork that matters more "
        "but still cannot be read does not make its arm more informative."
    )
    a("")
    a(
        "3. **The arms that separate a fork on a usable assay are fixed under "
        "both extremes**, and none of them is decided by AC04:"
    )
    a("")
    a("| Arm | Fork it decides on a usable assay |")
    a("|---|---|")
    for result in report["results"]:
        if result["forks_separated_usable_assay"]:
            a(
                f"| `{result['experiment']}` | "
                + ", ".join(result["forks_separated_usable_assay"])
                + " |"
            )
    a("")
    a(
        'So the candidate set for "preferred" is invariant: no arm can enter it '
        "and none can leave. That does not by itself exclude RE-ORDERING within "
        "it -- an `AC03` within-condition divergence would bear on `HH`, which "
        "is a candidate fork and the runner-up's -- and section 3a of the "
        "selection document gives the separate design reason why no prior shift "
        "closes the gap between the runner-up and the recommended arm."
    )
    a("")
    a(
        "> **What this does not prove.** It shows no admissible scRNA finding "
        "changes the experiment CHOICE. It does not show such a finding would be "
        "uninteresting: contradicting AC04 would be evidence that the epithelial "
        "receptivity layer is mis-specified, which is a reason to develop an "
        "assay for it, and that is a different decision from which arm to run "
        "next with the assays that exist."
    )
    a("")

    return "\n".join(lines) + "\n"


def build(root: Path | None = None) -> tuple[Path, Path, Path]:
    active = root or repo_root()
    report = evaluate(active)
    md = active / OUT_MD
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render(report), encoding="utf-8")
    tables = active / OUT_TABLES
    tables.write_text(render_tables(report, active), encoding="utf-8")
    tsv = active / OUT_TSV
    with tsv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(TSV_COLUMNS)
        writer.writerows(_rows(report))
    return md, tsv, tables


if __name__ == "__main__":  # pragma: no cover
    for written in build():
        print(f"wrote {written}")
