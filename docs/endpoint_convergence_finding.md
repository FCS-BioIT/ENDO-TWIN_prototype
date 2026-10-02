# Adhesion endpoints are read before the network converges

Status: diagnostic finding, 2026-07-28. No model, rule, protocol or calibration
file was changed in recording it. Claim level: `structural` — this is a
statement about simulation convergence, not about calibration or biology.

## Summary

The `adoc-literature-superset-v0.3.0` adhesion endpoints are sampled roughly
**4000× earlier than the time they need to reach their logical fixed point**.
Every reported anomaly that led the Phase 1D review to `fail` — the inverted
mifepristone arm, the inert anti-SPP1 arm, the "unresolvably small"
probabilities — is a consequence of that, not of the Boolean model.

Once the readout horizon is long enough for the network to settle, the model's
perturbation behaviour is **directionally correct in every arm tested**.

## Evidence

### The endpoint is still in transit when it is read

`adhesion_challenge_hormone_treated` declares `relative_duration = 1.0`. At the
final row of that phase (seed 1, 20000 trajectories) nothing has plateaued:

| phase-local time | COMPETENCE | OUT_EPITHELIAL_RECEPTIVE | E_RECEPTIVE_SURFACE | S_DECIDUALIZED |
|---|---|---|---|---|
| 0.0 | 0.00000 | 0.00026 | 0.121 | 0.636 |
| 0.5 | 0.00000 | 0.01372 | 0.181 | 0.414 |
| 0.9 (**readout**) | 0.00020 | 0.03765 | 0.213 | 0.357 |

### Extending the horizon recovers the analytic fixed point

Same continuation state, same seed and trajectory count, varying only
`max_time` for the challenge phase:

| max_time | COMPETENCE | OUT_STABLE_ADHESION | OUT_EPITHELIAL_RECEPTIVE |
|---|---|---|---|
| 1.0 (declared) | 0.00020 | 0.00000 | 0.038 |
| 5.0 | 0.10892 | 0.05926 | 0.423 |
| 20.0 | 0.81978 | 0.81897 | 1.000 |
| 60.0 | 0.82035 | 0.82035 | 1.000 |

0.820 is the value predicted analytically from the two static relay draws in
`baseline.cfg` that gate the adhesion-route disjunction:
`1 − (1 − 0.7)(1 − 0.4) = 0.82`. The converged simulation reproduces it to
three decimals, and is stable from `max_time = 20` to `60`.

### More trajectories do not help

Increasing the trajectory budget at the declared horizon tightens the interval
around the *unconverged* value; it does not move it toward the fixed point.
Mean COMPETENCE for `adhesion_challenge_hormone_treated` across 5 seeds:
0.000300 at 2000, 0.000206 at 20000, 0.000353 at 100000 — all ~2300× below the
converged 0.820. A power calculation on the unconverged values suggests
50 000–80 000 trajectories per arm to resolve a 2-fold effect, but that budget
buys precision on a quantity that is not the endpoint of interest.

### Perturbation directions at a converged horizon

`max_time = 20.0`, 20000 trajectories, seeds 1–3, all continuing from the real
`hormone_treated_maternal` state:

| condition | COMPETENCE (sd) | STABLE_ADHESION (sd) | ΔCOMPETENCE vs HT |
|---|---|---|---|
| hormone-treated (reference) | 0.81979 (0.00009) | 0.81883 (0.00019) | — |
| mifepristone | 0.00000 (0.00000) | 0.00000 (0.00000) | −0.81979 |
| anti-SPP1 | 0.39967 (0.00032) | 0.39904 (0.00024) | −0.42012 |
| excess ER stress | 0.57474 (0.00067) | 0.57418 (0.00053) | −0.24505 |
| high ECM stiffness | 0.57474 (0.00067) | 0.57418 (0.00053) | −0.24505 |

Every arm reduces adhesion competence, which is the expected direction in all
four cases. Seed-to-seed SD is at most 0.0007 against effect sizes of 0.245 to
0.820, so these are resolvable by any reasonable criterion — three to four
orders of magnitude clear of the noise floor.

For mifepristone this is the direction the held-out manuscript counts support
(1/8 versus 9/19), and it is the opposite of what the short-horizon run
reported.

## What this does and does not establish

It establishes that the Boolean logic produces the expected qualitative
ordering, and that the previously reported anomalies were measurement
artifacts. It does **not** establish that the model is calibrated: the
converged magnitudes (0.82 for the reference arm) are far from the observed
adhesion frequency (9/19 ≈ 0.47), and the existing calibration in
`config/calibration.yaml` was fitted against short-horizon values. Changing the
horizon would invalidate those fitted numbers and require recalibration.

That is why no duration was changed here. The choice of readout horizon is a
scientific decision with repository-wide consequences and belongs to the model
owner, not to a diagnostic.

## The one genuine model defect found

`IN_ER_STRESS_EXCESS` and `IN_HIGH_ECM_STIFFNESS` are **logically
interchangeable**. They occur in exactly one place in `network.bnd`:

```
Node X_MECHANICAL_PERMISSIVE_ECM {
  logic = S_DECIDUALIZED and S_TAZ_ECM
      and not ((IN_ER_STRESS_EXCESS or IN_HIGH_ECM_STIFFNESS) and X_MECHANICAL_STRESS_RELAY);
}
```

They enter symmetrically through the same disjunction, and appear nowhere else.
Each challenge condition sets exactly one of them TRUE, so the two conditions
describe the **same** executable network. Their bit-identical outputs are
guaranteed by construction and cannot be separated by any seed, trajectory
count or horizon. Distinguishing them requires a mechanistic difference in the
model, which is an evidence question, not a simulation-settings question.

## Recommended next steps, in order

1. Decide the readout horizon. A phase duration that reaches the fixed point
   (≥ 20 relative units for the challenge phase on current rates) makes the
   endpoints interpretable.

   > **Superseded in part, 2026-09-16.** This step used to add that
   > "recalibration against `config/calibration.yaml`'s observed counts must
   > follow". There is no longer any recalibration to do: `adhesion_objective`
   > was the repository's only magnitude-fitted term and was demoted to
   > `diagnostic_ordinal`, with no replacement scalar
   > (`docs/gate3_scope_adjudication.md` §3). The horizon decision still
   > matters — it determines whether the endpoints are interpretable at all —
   > but it no longer feeds a fitting step.
2. Re-run the Phase 1D scientific review against converged outputs. The `fail`
   verdict rests on findings this diagnostic attributes to the horizon.
3. Give ER stress and ECM stiffness distinct mechanisms, or merge them into a
   single declared "adverse mechanics" input and stop reporting them as two
   conditions.
4. Only then consider promoting the superset, activating rule ensembles, or
   producing candidate screens.

---

## Horizon decision: fixed point, not a fitted finite time

Addendum, 2026-07-28. The convergence finding above showed the endpoint is read
before it settles. It did **not** say which horizon is correct. That question is
now decided, and the answer is **not** simply "use 20".

### The tempting option, and why it is rejected

Observed hormone-treated adhesion is 9/19 = 0.474. Simulated competence rises
monotonically from ~0 to 0.820 across the horizon range, so *some* horizon was
mathematically guaranteed to cross 0.474. A sweep (3 seeds, 5000 trajectories)
locates it at `max_time` ~= 8.37, and a direct check at 8.4 reproduces the
observed value almost exactly: competence 0.4765.

That agreement is not evidence. Four things argue against adopting it:

1. **The crossing is guaranteed by monotonicity.** Finding it says the swept
   range brackets the target, not that the dynamics are right at that time.
2. **The two candidate endpoints disagree by a full relative-time unit.**
   `OUT_MATERNAL_ADHESION_COMPETENCE` crosses 0.474 at ~8.37;
   `OUT_STABLE_ADHESION` crosses at ~9.39. There is no single crisp horizon.
3. **Neither genuine test corroborates it.** The untreated arm is
   `0.000000` at *every* horizon from 2 to 20 -- it is horizon-blind by
   construction and cannot test the choice. The held-out mifepristone arm
   *fails*: at horizon 8.4 the model predicts `0.0000` against an observed
   1/8 = 0.125. Direction is right, magnitude is absent.
4. **The fit is fragile.** Local elasticity is ~1.9, so a +/-10% horizon window
   (7.5 to 9.2) spans predicted competence 0.38 to 0.56 -- roughly +/-19% around
   the target.

There is also a self-defeating property. At horizon 8.4 the upstream nodes are
already saturated: `E_PAEP` 0.994, `S_IGFBP1` 0.964, `S_PRL` 0.969. The
secreted-protein constraints carry almost no discriminating power exactly where
the adhesion endpoint would need them to help. A horizon fitted to adhesion buys
its agreement in a regime where the rest of the biology has stopped varying.

### Decision

**Read the endpoint at the logical fixed point** (`max_time` >= 20, converged
0.820), and treat the gap to the observed 0.474 as a calibration target for the
model's own parameters rather than for time.

Under this choice the horizon leaves the fit entirely. What becomes fitted
instead are the two static relay probabilities in `baseline.cfg` that gate the
adhesion-route disjunction and currently yield `1 - (1 - 0.7)(1 - 0.4) = 0.82`.
Recalibrating two structural probabilities against one observed frequency is a
smaller, more auditable and more testable change than adopting an uncalibrated
time value as a permanent model parameter.

Under the rejected finite-time option, `max_time` for the challenge phase would
itself become a fitted parameter -- ambiguous by output node, constrained by
exactly one number, with the other calibration arm horizon-blind and the
held-out arm disagreeing.

### Physical time remains uncalibrated

`provenance.toml` declares `maboss_time_units = "relative_only"`. Whichever
horizon is used, it is a dimensionless MaBoSS relative-time parameter. It is not
"6 days" and must never be reported as a protocol duration. Nothing in this
decision changes that, and no rate, rule, cfg or calibration file was modified
in reaching it.
