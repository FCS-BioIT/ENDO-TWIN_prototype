"""U2 -- the Gate-3a repairs the plan asks for are blocked, and stay blocked in v0.5.

`docs/v05_mechanistic_integration_plan.md` named U2 "the first concrete
deliverable": de-alias `S_PRL` from `S_IGFBP1`, and add a day-3 maternal
protocol stage. **Neither may be done on the evidence in hand**, and two
completed analysis units say so -- `docs/prl_igfbp1_temporal_axis.md` and
`docs/gate3a_closure_audit.md`, both of which postdate the
`docs/v05_plan_review.md` section U2 was derived from. The reasoning is in
`docs/v05_u2_gate3a_blocked.md`; this module is the part a future round cannot
argue with.

WHY THIS MODULE EXISTS SEPARATELY FROM `test_prl_igfbp1_axis.py`. That suite
pins these facts against `adoc-literature-superset-v0.4.0` only. v0.4 is now
immutable, so its assertions can no longer fail; the model that can change is
v0.5. A de-aliased `S_PRL` in v0.5's `network.bnd`, or a day-3 arm in v0.5's
conditions, would have passed the whole suite in silence while doing exactly
what the plan told the next session to do.

WHAT "EXCHANGEABLE" MEANS HERE, AND WHY THE GUARD IS SEMANTIC. Two nodes are
exchangeable when nothing in the model distinguishes them: same Boolean
function, same effective transition rates, same effective initial state under
every committed condition. An earlier version of this module tested that by
grepping the `.cfg` files for `rate_up`/`rate_down`, which was **the wrong
layer in both directions**. MaBoSS rate expressions live in the `.bnd` node
block -- which is exactly where U7 plans to put the mutation interface -- so a
`rate_up` on `S_PRL` alone would have passed; and any unrelated future rate
anywhere in a cfg would have failed it even with the two nodes still perfectly
exchangeable. The assertions below compare **the two nodes to each other**
instead, so they say what they mean and survive U7.

WHAT A FAILURE HERE MEANS. Not "loosen the test". The blocker for de-aliasing is
a MEASUREMENT: an assay-compatible binarisation threshold for IGFBP-1 not drawn
from the same day-0/3/6 series that serves as diagnostic OM-002. The blocker for
a day-3 arm is different and is NOT an assay -- it is that the model has no
physical-time semantics to attach "24 h" to. If a failure here is legitimate,
the finding documents change first and cite the new evidence; the tests follow.
"""

from __future__ import annotations

import hashlib
import re
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.identifiability import repo_root, resolve_model

ROOT = repo_root()

#: Every superset the repository can still execute. v0.4 is immutable and is
#: covered by `test_v04_immutability.py`; it is included anyway because a guard
#: that silently stops covering a model is how this gap appeared in the first
#: place.
GUARDED_MODELS = (
    "adoc-literature-superset-v0.4.0",
    "adoc-literature-superset-v0.5.0",
)

ALIASED_PAIR = ("S_PRL", "S_IGFBP1")

_NODE_RE = re.compile(r"^\s*Node\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{")
_ATTR_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*;\s*$")
_ISTATE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*istate\s*=\s*(.+?)\s*;\s*$"
)


def node_attributes(bnd: Path) -> dict[str, dict[str, str]]:
    """Every attribute of every node block -- `logic`, and any rate expression.

    Deliberately not restricted to `logic`: a rate declared on one node of the
    pair and not the other is precisely what this module has to catch, and it
    lives here rather than in the cfg.
    """
    nodes: dict[str, dict[str, str]] = {}
    current: str | None = None
    for line in bnd.read_text(encoding="utf-8").splitlines():
        node = _NODE_RE.match(line)
        if node:
            current = node.group(1)
            nodes[current] = {}
            continue
        if current is None:
            continue
        if line.strip().startswith("}"):
            current = None
            continue
        attr = _ATTR_RE.match(line)
        if attr:
            nodes[current][attr.group(1)] = attr.group(2)
    return nodes


def abstracted(expression: str | None, node: str) -> str | None:
    """A node's own name replaced by a placeholder, so two nodes compare equal.

    U7's mutation interface is per-node by construction --
    `rate_up = $Low_S_PRL ? 0 : (...)` -- so the two nodes' rate expressions
    differ textually while being the same rule applied to each. Comparing raw
    strings would fail on exactly the symmetric interface U7 is meant to add,
    which is the same over-broadness that made the previous cfg-grep useless.
    What must fail is an ASYMMETRY: a rate on one node that the other does not
    have, or a different rule applied to each.
    """
    if expression is None:
        return None
    return expression.replace(node, "<SELF>")


def effective_istates(baseline: Path, condition: Path | None) -> dict[str, str]:
    """Last assignment wins, baseline first and then the condition overlay.

    This is what makes a per-condition override visible. Checking `baseline.cfg`
    alone -- as an earlier version did -- would miss a condition that sets
    `S_PRL.istate` without setting `S_IGFBP1.istate`.
    """
    states: dict[str, str] = {}
    for path in (baseline, condition):
        if path is None:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _ISTATE_RE.match(line)
            if match:
                states[match.group(1)] = match.group(2)
    return states


class AliasStaysInPlaceTest(unittest.TestCase):
    """`S_PRL` and `S_IGFBP1` remain indistinguishable to the model.

    Under one Boolean function, equal effective rates and equal effective
    initial states, the two nodes' onset distributions are identical at every
    horizon and under every seed. Individual stochastic trajectories can still
    fire them in either order -- that is ordinary transition timing, not
    evidence -- but there is **no systematic directional information** to
    recover. That is why "simulate the transient and see which comes first" is
    not a deliverable that can succeed as the model stands.
    """

    def test_the_two_nodes_share_one_boolean_function(self) -> None:
        for model in GUARDED_MODELS:
            with self.subTest(model=model):
                nodes = node_attributes(resolve_model(model, ROOT).network_bnd)
                first, second = ALIASED_PAIR
                self.assertEqual(
                    nodes[first].get("logic", "").strip(),
                    nodes[second].get("logic", "").strip(),
                    "S_PRL was de-aliased from S_IGFBP1. The ordering that "
                    "would justify it is not established, and the one repair "
                    "that survives on the merits needs a binarisation threshold "
                    "that may not be drawn from diagnostic OM-002 -- see "
                    "docs/v05_u2_gate3a_blocked.md.",
                )
                self.assertEqual(
                    nodes[first].get("logic", "").strip(), "S_DECIDUALIZED"
                )

    def test_no_declared_rate_distinguishes_the_two_nodes(self) -> None:
        """Compared node against node, in the `.bnd`, where MaBoSS rates live.

        Stated as equality rather than absence on purpose: U7 may legitimately
        give every gateable node a `rate_up`/`rate_down` mutation interface, and
        that must not fail here -- which is why the comparison abstracts each
        node's own name out of its expression first. What must fail is a rate
        that applies to one of these two and not the other, or a different rule
        applied to each. Both the symmetric U7 form and a one-sided rate were
        exercised against this assertion before it was committed.
        """
        for model in GUARDED_MODELS:
            with self.subTest(model=model):
                nodes = node_attributes(resolve_model(model, ROOT).network_bnd)
                first, second = ALIASED_PAIR
                for attribute in ("rate_up", "rate_down"):
                    with self.subTest(attribute=attribute):
                        self.assertEqual(
                            abstracted(nodes[first].get(attribute), first),
                            abstracted(nodes[second].get(attribute), second),
                            f"{attribute} distinguishes {first} from {second}. "
                            f"prl_igfbp1_temporal_axis.md section 6 rejects "
                            f"introducing a differential rate: it would fit a "
                            f"rate to an assay artifact.",
                        )

    def test_the_two_nodes_carry_no_other_asymmetric_attribute(self) -> None:
        """Whatever U7 or a later unit adds, it must be added to both or neither."""
        for model in GUARDED_MODELS:
            with self.subTest(model=model):
                nodes = node_attributes(resolve_model(model, ROOT).network_bnd)
                first, second = ALIASED_PAIR
                self.assertEqual(sorted(nodes[first]), sorted(nodes[second]))

    def test_their_effective_istate_agrees_under_every_condition(self) -> None:
        """Baseline plus each condition overlay, not baseline alone."""
        for model in GUARDED_MODELS:
            spec = resolve_model(model, ROOT)
            conditions = sorted(Path(spec.condition_dir).glob("*.cfg"))
            self.assertTrue(conditions)
            first, second = ALIASED_PAIR
            for condition in [None, *conditions]:
                states = effective_istates(spec.baseline_cfg, condition)
                label = "baseline" if condition is None else condition.name
                with self.subTest(model=model, condition=label):
                    self.assertIn(first, states)
                    self.assertIn(second, states)
                    self.assertEqual(
                        states[first],
                        states[second],
                        f"{label} gives {first} and {second} different initial "
                        f"states, which distinguishes their transients.",
                    )


class NoDayThreeArmTest(unittest.TestCase):
    """Day 3 and day 6 are the same Boolean input condition.

    `config/adoc_outlet_conditions.tsv` gives COND-DAY3-SAMPLE and
    COND-DAY6-SAMPLE identical `agents`, `agent_concentrations` and
    `condition_normalized`, which is what makes the arm the same. Ten other
    fields DO differ -- including `collection_duration` (blank against 48) and
    `collection_duration_state` -- so this is deliberately not phrased as "only
    elapsed time differs", which an earlier revision said and which the table
    contradicts. (The count was eleven until `applies_to_sheets` stopped
    differing when PAEP was removed from the day-6 row under SOFIA-COMM-007; no
    argument here rests on it.) A Boolean arm
    expresses an input vector, not an elapsed time, and `config/calibration.yaml`
    records `duration_units: relative_only` with no physical-time calibration
    claimed. An arm named for day 3 would carry inputs identical to
    `hormone_treated_maternal` and could not be identified with day 3 at all.

    NOTE the blocker here is NOT the assay. It is that the model has no physical
    -time semantics for "24 h" to attach to. Supplying a better IGFBP-1 assay
    would not unblock it; a calibrated time axis would, and this project
    explicitly disclaims one.

    WHAT REPLACED THE ARM, AND WHY IT IS NOT THE SAME THING (unit U2b,
    2026-09-18). Day 3 is now represented as an OBSERVATION CHECKPOINT on the
    existing continuous `hormone_treated_maternal` trajectory --
    `config/observation_checkpoints.tsv`, read by
    `src/dt_adoc/observations/checkpoints.py`. That is not the arm this class
    forbids and does not weaken it: a checkpoint creates no condition cfg, no
    protocol and no input vector, and an interior one is assigned **no
    simulation time and no value at all** -- it carries its experimental hours,
    fraction and order, and nothing else. So it attaches no "24 h" to anything,
    which is the same prohibition this class enforces, arrived at from the
    observation side. If a future edit gives an interior checkpoint a position,
    proportionally or by ordinal rank, it has done what this class forbids by
    another route; `tests/unit/test_observation_checkpoints.py` fails on
    exactly that.
    """

    def test_no_day3_arm_exists_in_any_guarded_model(self) -> None:
        for model in GUARDED_MODELS:
            conditions = Path(resolve_model(model, ROOT).condition_dir)
            for pattern in ("*day3*", "*day_3*", "*day-3*", "*24h*", "*_d3*"):
                with self.subTest(model=model, pattern=pattern):
                    self.assertEqual(
                        sorted(p.name for p in conditions.glob(pattern)),
                        [],
                        "A day-3 protocol arm was created. It cannot be "
                        "identified with day 3 without a physical-time "
                        "calibration this project disclaims; see "
                        "docs/prl_igfbp1_temporal_axis.md section 2.",
                    )

    def test_v05_keeps_every_v04_condition(self) -> None:
        """A superset, not an equality.

        An earlier version froze v0.5's condition suite to exactly v0.4's 21
        files, which would have blocked any legitimate future arm for an
        unrelated reason. What must not happen is a v0.4 arm going missing.
        """
        names = {
            model: {
                p.name
                for p in Path(resolve_model(model, ROOT).condition_dir).glob("*.cfg")
            }
            for model in GUARDED_MODELS
        }
        v04, v05 = (names[model] for model in GUARDED_MODELS)
        self.assertEqual(len(v04), 21)
        self.assertTrue(v04 <= v05, f"v0.5 dropped conditions: {sorted(v04 - v05)}")

    def test_no_new_v05_condition_merely_renames_an_existing_arm(self) -> None:
        """The day-3 failure mode without the word "day" in the filename.

        Copying `hormone_treated_maternal.cfg` to a new name is how a day-3 arm
        arrives past the pattern check above. A genuinely new arm has a
        genuinely different input vector, so this permits one while rejecting a
        copy. v0.4's own suite already contains byte-identical pairs, which is
        why this applies only to files v0.5 adds.
        """
        v04_dir, v05_dir = (
            Path(resolve_model(model, ROOT).condition_dir) for model in GUARDED_MODELS
        )
        existing = {
            hashlib.sha256(p.read_bytes()).hexdigest(): p.name
            for p in sorted(v04_dir.glob("*.cfg"))
        }
        v04_names = {p.name for p in v04_dir.glob("*.cfg")}
        for path in sorted(v05_dir.glob("*.cfg")):
            if path.name in v04_names:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(added=path.name):
                self.assertNotIn(
                    digest,
                    existing,
                    f"{path.name} is byte-identical to {existing.get(digest)}; a "
                    f"new arm that duplicates an existing input vector adds no "
                    f"condition, only a name.",
                )


if __name__ == "__main__":
    unittest.main()
