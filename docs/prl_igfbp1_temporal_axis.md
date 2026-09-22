# Gate 3a — the PRL / IGFBP-1 temporal axis, and why no variant is adopted

Status: analysis finding, 2026-09-16. **No topology, rule, istate, rate,
protocol or recorded output changes.** The unit was opened to find a rule or
topology variant that expresses the recorded IGFBP-1-before-PRL onset order.
The conclusion is that no such variant should be adopted, because the
observation that would motivate it is not a kinetic ordering.

## 1. The two nodes are exchangeable by construction — a proof, not a sample

```
Node S_DECIDUALIZED { logic = S_PGR and S_PKA and S_BMP2; }
Node S_PRL          { logic = S_DECIDUALIZED; }
Node S_IGFBP1       { logic = S_DECIDUALIZED; }

S_PRL.istate = FALSE;   S_IGFBP1.istate = FALSE;
```

and no `rate_up` or `rate_down` is declared in `baseline.cfg` or in any
condition `.cfg`, so both take the MaBoSS default. Identical Boolean function,
identical initial state, identical transition rate: the two nodes are
**exchangeable**, and their onset distributions are identical at every horizon
and under every seed. This does not need simulating and cannot be fixed by
simulating harder — any apparent difference in a run is node-ordering noise.

## 2. Day 3 and day 6 are the same input condition

`config/adoc_outlet_conditions.tsv`:

| | COND-DAY3-SAMPLE | COND-DAY6-SAMPLE |
|---|---|---|
| agents | E2;MPA;cAMP;XAV939 | E2;MPA;cAMP;XAV939 |
| concentrations | E2 10 nM; MPA 1 µM; cAMP 0.25 mM; XAV939 10 µM | *identical* |
| hours after cocktail start | 24 | 96 |

The treatment is **the same**; only elapsed time differs. So no new protocol arm
can express day 3 as against day 6 — the Boolean input vector is identical, and
the difference is purely a horizon. `config/calibration.yaml` records
`duration_units: relative_only` and "No physical-time calibration is claimed",
and COND-DAY3-SAMPLE's own note says the 24 h is "Wall-clock bench time only:
never a MaBoSS horizon or transition rate".

**A day-3 arm is therefore deliberately not created.** It would carry inputs
identical to `hormone_treated_maternal`, it could not be identified with day 3
without a physical-time calibration this project explicitly disclaims, and by §1
it would show `S_PRL` and `S_IGFBP1` identical anyway. Creating it would add an
arm that cannot inform the question it was created for.

> **Addendum, 2026-09-18 (unit U2b).** This section conflated two things that
> the repository has since separated: *representing* day 3 and *identifying* it
> with 24 h. The second is impossible here, and everything above about it
> stands. The first is not, and this section wrongly implied it was. Day 3 is a
> position inside the full-cocktail phase, which the model already runs as one
> continuous trajectory; it is now declared as an observation checkpoint in
> [`config/observation_checkpoints.tsv`](../config/observation_checkpoints.tsv)
> as an **ordered observation carrying no simulation time**, with no arm, no
> reset and no hours-to-relative-time factor. The experimental-to-MaBoSS
> alignment §2 says is impossible is therefore still impossible, and nothing
> below rests on one — see
> [`observation_checkpoints.md`](observation_checkpoints.md). **This changes
> nothing in §§3–6.** The blocker this unit identified was never the protocol
> set: it is the confounded observation (§3, §4) and the unregistered
> binarisation threshold (§5), and both are untouched. No variant is adopted
> and no rate is introduced, then or now.

## 3. The observed ordering is confounded, on the stromal outlet

Restricted to the **bottom (stromal) outlet**, which is the like-for-like
comparison — the PRL sheet is bottom-only (SOFIA-COMM-006), so pooling the
IGFBP-1 top series would compare different compartments:

| day | IGFBP-1 detected (LOD 5) | median detected | PRL detected (LOD 10) | median detected |
|---|---|---|---|---|
| 0 | **4/5** | 237 pg/mL | **0/6** | — |
| 3 | 5/5 | 9 451 pg/mL | 1/6 | 114 pg/mL |
| 6 | 3/5 | 10 123 pg/mL | 3/6 | 1 083 pg/mL |

**The magnitude gap is 83× at day 3 and 9× at day 6, on top of a 2× lower
detection limit.** Two analytes with *identical* underlying onset kinetics would
still show IGFBP-1 crossing detection first, by a wide margin, on those numbers
alone. A detection-fraction ordering therefore cannot establish a kinetic
ordering, and this is before any of the recorded structural caveats:
the column-to-chip mapping is **lost** (not merely unverified), rows are **not
paired across days**, chips are not independent patients, and n is 5 and 6.

Note also that IGFBP-1 detection **falls** from 5/5 at day 3 to 3/5 at day 6,
with two units reading exactly zero. `SOFIA-COMM-002` establishes those zeros are
genuine measured non-detects rather than censoring, and OM-002 records that the
same two column positions also drop to zero in the top outlet — more consistent
with chip-level dropout than with secretion ceasing. An ordering argument built
on a series that is non-monotonic in its own late timepoint is weak.

## 4. It is not "two induced genes with a lag"

The more important point. IGFBP-1 is detected in **4 of 5 stromal units at day
0, before any hormone is added**, at a median of 237 pg/mL. PRL is detected in
**0 of 6**. That is not a difference in induction *timing*; it is the difference
between a **constitutive** and an **induced** analyte, and those call for
different model repairs.

This contradicts `SOFIA-STR-001`'s summary that both were "undetectable day 0".
The conflict is **already recorded** in OM-002's censoring note and is not
rediscovered here.

## 5. Whether IGFBP-1 is "ON at baseline" is a threshold choice, not an observation

`S_IGFBP1 = S_DECIDUALIZED` asserts IGFBP-1 is OFF without decidualization. The
day-0 data appear to contradict that — but only under a binarisation that puts
the ON/OFF boundary below 237 pg/mL. Put it above, and the current encoding is
right and day-0 secretion is "low but off".

There is **no pre-registered binarisation threshold for IGFBP-1**, and the
repository has already recorded the governing rule, in OM-001's note about the
analogous PAEP threshold:

> The `E_PAEP` OFF/ON binarization threshold is implicit and unrecorded … **It
> must never be chosen from these same observations while they also serve as the
> feasibility gate.**

`OM-002` is `active_diagnostic` — the day-0/3/6 IGFBP-1 series *is* the
diagnostic. So choosing a threshold from it in order to justify a topology
change, and then letting OM-002 evaluate the changed model, is precisely the
leakage that rule forbids. **The question is not answerable from the data in
hand.**

## 6. Conclusion: no variant adopted, and no rate introduced

Four candidate repairs were considered and none survives:

| candidate | why not |
|---|---|
| give `S_PRL` an extra causal step so it turns on later | the ordering it targets is not established (§3, §4); and the best human evidence for these two promoters, REF-061 (Tamura 2014), shows db-cAMP raises IGFBP-1 and PRL mRNA **together** with C/EBPβ occupancy and that C/EBPβ knockdown abolishes **both** — it argues against a differential upstream regulator on the cAMP arm |
| give `S_IGFBP1` a hormone-independent basal route | the best-supported repair of the four, and still blocked: it rests entirely on a binarisation threshold that §5 shows cannot be chosen from these observations |
| `IGFBP1-fb` (S_IGFBP1 → S_DECIDUALIZED) | separately excluded: a 14-node cycle the enumerator cannot evaluate, plus calibration leakage through OM-002 |
| differential transition rates | would fit a rate to an assay artifact. The instruction was to reach for rates only if Boolean topology cannot express the ordering; the prior question is whether there is an ordering to express, and §3–§5 say it is not established |

**The axis is recorded as blocked on measurement, not on modelling.** What would
unblock it, in order of value:

1. **Independent, assay-compatible binarisation evidence for IGFBP-1.** This is
   the actual blocker, but it is *not* automatically the cheapest item, and an
   earlier version of this list wrongly said it was. A concentration threshold
   borrowed from another study is transferable only if that study is compatible
   in the things that set the number — collection geometry, accumulation time,
   medium, dilution and normalisation — or if it establishes a genuine
   *biological* state boundary rather than an assay-specific cut. Absent that,
   importing a threshold does not remove the artifact; it replaces one
   unregistered calibration choice with another, and hides it behind a citation.
2. **Paired per-chip PRL and IGFBP-1 at the same timepoints**, so an ordering is
   a within-unit comparison rather than a cross-series one. The mapping is
   recorded as lost; recovering it is a metadata request, not an experiment.
3. **A normalised or absolute-quantified readout** that removes the 83× magnitude
   confound — without it, no detection-fraction comparison can support a timing
   claim.

## What this unit did not do

It did not create a day-3 arm (§2), propose a rule variant (§6), introduce a
transition rate (§6), or alter any recorded output. It did not re-derive the
day-0 contradiction, which OM-002 already records. The structural facts above
are pinned by `tests/unit/test_prl_igfbp1_axis.py`; the *judgements* in §5 and
§6 are arguments from those facts, not facts, and no test asserts them.
