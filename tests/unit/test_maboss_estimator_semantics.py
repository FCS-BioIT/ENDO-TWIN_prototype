"""Pin the estimator facts `docs/maboss_estimator_semantics.md` rests on.

The document's central claim -- that MaBoSS's NODE-level error column is a sum
of per-state standard errors and therefore not a standard error of the node
marginal -- is the kind of claim that decides whether a maintainer surfaces that
column as an uncertainty. It is checkable from runtime behaviour without reading
C++, so it is checked here rather than left as a citation.

These tests exercise `cmaboss` directly rather than through the repository's
adapter, because the property under test is the simulator's, not ours.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models" / "superset" / "adoc-literature-superset-v0.4.0"
NETWORK = MODEL_DIR / "network.bnd"
CONFIG = MODEL_DIR / "conditions" / "hormone_treated_maternal.cfg"


def _run():
    import cmaboss

    sim = cmaboss.MaBoSSSim(network=str(NETWORK), config=str(CONFIG))
    return sim.run(only_last_state=False).get_nodes_probtraj()


class NodeProbtrajShape(unittest.TestCase):
    """The raw return is a 4-tuple; the repository's adapter keeps only part."""

    def test_raw_result_carries_values_times_names_and_errors(self) -> None:
        values, times, names, errors = _run()
        self.assertEqual(values.shape, errors.shape)
        self.assertEqual(values.shape[0], len(times))
        self.assertEqual(values.shape[1], len(names))
        self.assertIn("OUT_STABLE_ADHESION", names)


class NodeErrorIsNotAStandardError(unittest.TestCase):
    """The §3b finding, asserted from behaviour.

    A node marginal that is deterministically 1.0 has zero sampling error. If
    the reported error is nonzero there, the column cannot be a standard error
    of that marginal -- which is exactly what a sum over the contributing
    states' standard errors produces, because the spread of the underlying
    states cancels in the marginal and does not cancel in the sum.
    """

    def test_a_saturated_node_still_reports_a_nonzero_error(self) -> None:
        values, _times, names, errors = _run()
        index = names.index("OUT_STROMAL_DECIDUALIZED")
        value = values[-1, index]
        error = errors[-1, index]
        self.assertAlmostEqual(
            value,
            1.0,
            places=9,
            msg="this node is no longer saturated at the declared horizon, so "
            "pick another saturated node or the demonstration does not apply",
        )
        self.assertGreater(
            error,
            0.0,
            "the node error column is zero on a saturated marginal, so it may "
            "now be a genuine standard error and docs/maboss_estimator_"
            "semantics.md section 3b must be re-derived",
        )

    def test_the_error_column_is_not_a_binomial_standard_error(self) -> None:
        """Rules out the specific withdrawn interpretation, not merely 'some' error.

        A binomial SE at p and N is sqrt(p(1-p)/N) and vanishes as p -> 1. The
        reported error does not, so no binomial model reproduces this column.

        SCOPE. This is a statement about the SIMULATOR's error column, not about
        binomial intervals generally. They remain correct for experimental count
        data -- R41b reports a Wilson interval on 9/19 attached blastocysts --
        and for the degenerate simulator case where a node does not transition
        inside the tick window, where the per-trajectory contribution really is
        a 0/1 indicator. See docs/maboss_estimator_semantics.md section 3d.
        """
        import math

        values, _times, names, errors = _run()
        index = names.index("OUT_STROMAL_DECIDUALIZED")
        value = float(values[-1, index])
        error = float(errors[-1, index])
        for sample_count in (2000, 20000, 100000):
            binomial = math.sqrt(max(value * (1.0 - value), 0.0) / sample_count)
            with self.subTest(sample_count=sample_count):
                self.assertGreater(
                    error,
                    binomial * 100,
                    "the reported error is within two orders of magnitude of a "
                    "binomial SE, so the claim that it is not a binomial "
                    "quantity needs re-deriving",
                )


class ReportedProbabilitiesAreNotPathCounts(unittest.TestCase):
    """`0.00005` is not "one trajectory in N", and this shows why.

    The estimator divides accumulated dwell TIME by (tick x trajectories), so a
    reported value has no reason to be a multiple of 1/N. One counterexample
    refutes the path-count reading, and that refutation is what several
    withdrawn interpretations in this repository turned on.

    IMPORTANT subtlety, recorded because a first version of this test got it
    wrong. A node that never transitions INSIDE a tick window contributes a full
    window of dwell time per trajectory, so the time-average degenerates exactly
    to a path fraction and IS a multiple of 1/N. Saturated free variables behave
    that way -- a 50/50 istate reports 0.4999 at N=10000 -- and pointing at one
    of those proves nothing. The counterexample has to be a node still in
    transit when it is read.
    """

    def test_committed_run_values_are_not_multiples_of_one_over_n(self) -> None:
        """Asserted against the numbers the repository actually reports.

        `docs/concordance/run_settings.json` is what the concordance table and
        every narrative built on it cite. If those values were path counts the
        withdrawn readings would have been right, so they are the values that
        matter, not a fresh toy run.
        """
        import json

        settings = json.loads(
            (ROOT / "docs" / "concordance" / "run_settings.json").read_text()
        )
        trajectories = int(
            settings["provenance"].get("trajectories", 20000)
            if isinstance(settings.get("provenance"), dict)
            else 20000
        )
        offenders: list[tuple[str, str, float]] = []
        for arm in settings["arms"]:
            for node, by_seed in arm["node_by_seed"].items():
                for value in by_seed:
                    if not 0.0 < value < 1.0:
                        continue
                    scaled = value * trajectories
                    if abs(scaled - round(scaled)) > 1e-3:
                        offenders.append((arm["arm_id"], node, value))
        self.assertTrue(
            offenders,
            "every committed value is a multiple of 1/N, so the path-count "
            "reading is no longer refuted by the recorded run and "
            "docs/maboss_estimator_semantics.md section 1 must be re-derived",
        )

    def test_a_node_in_transit_is_not_a_multiple_of_one_over_n(self) -> None:
        """The same refutation, self-contained, from a node read mid-transition.

        Early tick windows catch nodes that switch inside the window, which is
        where the time-average and the path fraction genuinely differ.
        """
        values, _times, names, _errors = _run()
        sample_count = 10000
        offenders = [
            (names[col], float(values[row, col]))
            for row in range(1, min(40, values.shape[0]))
            for col in range(values.shape[1])
            if 0.0 < values[row, col] < 1.0
            and abs(
                values[row, col] * sample_count - round(values[row, col] * sample_count)
            )
            > 1e-3
        ]
        self.assertTrue(
            offenders,
            "no in-transit value departs from a multiple of 1/N, so this "
            "demonstration no longer supports the time-average reading",
        )


if __name__ == "__main__":
    unittest.main()
