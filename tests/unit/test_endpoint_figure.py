"""The functional-endpoint figure's numbers trace to tracked replicate rows.

Guards four things the figure's error bars depend on:

* every plotted simulated value and interval recomputes from
  ``docs/endpoint/endpoint_replicates.tsv``, and every observed count from
  ``config/calibration.yaml``;
* the replicates are what the run settings say -- R per arm and horizon, each on
  a disjoint per-trajectory seed range (MaBoSS seeds trajectory k with seed + k);
* the converged replicate means agree with the exact enumerated fixed-point value,
  so the simulator is checked rather than trusted;
* the committed PNG, source table and sidecar pin each other, the generating
  code is pinned by content (generator hashes and the implementation digest),
  and the recorded generating commit is reachable from the reviewed tree.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
import sys
import unittest
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.reporting.endpoint_figure import (
    FIGURE_PATH,
    SOURCE_DATA_TSV,
    build_source_data,
    load_replicates,
)
from dt_adoc.reporting.endpoint_replicates import (
    ENDPOINT_ARMS,
    HORIZON_CLASSES,
    REPLICATES_TSV,
    RUN_SETTINGS_JSON,
    exact_converged_endpoint,
)

SIDECAR = ROOT / FIGURE_PATH.with_name(FIGURE_PATH.stem + "_metadata.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EndpointFigureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings = json.loads(
            (ROOT / RUN_SETTINGS_JSON).read_text(encoding="utf-8")
        )
        cls.replicates = load_replicates(ROOT)
        with (ROOT / REPLICATES_TSV).open(encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle, delimiter="\t"))

    def test_source_table_recomputes_from_replicates_and_config(self) -> None:
        with (ROOT / SOURCE_DATA_TSV).open(encoding="utf-8") as handle:
            committed = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(committed, build_source_data(ROOT))

    def test_every_arm_and_horizon_has_r_replicates(self) -> None:
        for arm_id, _protocol, _label in ENDPOINT_ARMS:
            for horizon in HORIZON_CLASSES:
                self.assertEqual(
                    len(self.replicates[(arm_id, horizon)]),
                    self.settings["replicates"],
                    (arm_id, horizon),
                )

    def test_replicate_seed_ranges_are_disjoint(self) -> None:
        n = self.settings["trajectory_count"]
        seeds = sorted(self.settings["seeds"])
        self.assertEqual(len(seeds), self.settings["replicates"])
        for low, high in itertools.pairwise(seeds):
            self.assertGreaterEqual(high - low, n)
        for row in self.rows:
            start, end = (int(x) for x in row["trajectory_seed_range"].split(".."))
            self.assertEqual(start, int(row["seed"]))
            self.assertEqual(end - start + 1, int(row["trajectory_count"]))

    def test_converged_means_agree_with_the_exact_fixed_point(self) -> None:
        exact = exact_converged_endpoint(root=ROOT)
        for arm_id, _protocol, _label in ENDPOINT_ARMS:
            values = self.replicates[(arm_id, "converged")]
            reference = exact[arm_id]["exact_converged_value"]
            self.assertEqual(
                reference,
                self.settings["exact_converged"][arm_id]["exact_converged_value"],
            )
            # A converged endpoint is a mixture over free-variable draws; its
            # mean must sit within a few run-to-run SDs of the exact value, with
            # a floor for arms whose spread is exactly zero.
            tolerance = max(5 * (stdev(values) if len(values) > 1 else 0.0), 1e-3)
            self.assertLess(abs(mean(values) - reference), tolerance, arm_id)

    def test_observed_counts_come_from_calibration_yaml(self) -> None:
        observed = self.settings["observed"]
        self.assertEqual(
            {k: (v["successes"], v["trials"]) for k, v in observed.items()},
            {"untreated": (0, 12), "hormone_treated": (9, 19), "mifepristone": (1, 8)},
        )
        self.assertFalse(observed["hormone_treated"]["magnitude_fitted"])

    def test_the_ordinal_claim_holds_at_convergence(self) -> None:
        m = {a: mean(self.replicates[(a, "converged")]) for a, _p, _l in ENDPOINT_ARMS}
        self.assertLess(m["untreated"], m["hormone_treated"])
        self.assertGreater(m["hormone_treated"], m["mifepristone"])

    def test_declared_mifepristone_sits_below_hormone_treated(self) -> None:
        # Quoted by README.md and docs/v05_u5_structural_audit.md section 6: on
        # disjoint blocks the overlapping-seed concordance ordering reverses.
        m = {a: mean(self.replicates[(a, "declared")]) for a, _p, _l in ENDPOINT_ARMS}
        self.assertLess(m["mifepristone"], m["hormone_treated"])

    def test_no_forbidden_uncertainty_is_plotted(self) -> None:
        # Wilson is for embryo counts only; a simulated occupancy never gets a
        # binomial-family interval or MaBoSS's summed node-error column.
        for row in build_source_data(ROOT):
            kind = row["interval_kind"].lower()
            if row["series"].startswith("simulated"):
                self.assertIn("disjoint between replicate indices", kind)
                for forbidden in ("wilson", "binomial", "error column", "trajector"):
                    self.assertNotIn(forbidden, kind)
            elif row["series"] == "observed":
                self.assertIn("wilson", kind)

    def test_figure_source_and_sidecar_pin_each_other(self) -> None:
        meta = json.loads(SIDECAR.read_text(encoding="utf-8"))
        self.assertEqual(meta["figure"]["sha256"], _sha(ROOT / FIGURE_PATH))
        self.assertEqual(meta["source_data_sha256"], _sha(ROOT / SOURCE_DATA_TSV))
        self.assertEqual(meta["replicates_tsv_sha256"], _sha(ROOT / REPLICATES_TSV))
        self.assertEqual(meta["run_settings_sha256"], _sha(ROOT / RUN_SETTINGS_JSON))
        self.assertEqual(
            self.settings["replicates_tsv_sha256"], _sha(ROOT / REPLICATES_TSV)
        )
        self.assertEqual(
            meta["renderer_sha256"],
            _sha(ROOT / "src/dt_adoc/reporting/endpoint_figure.py"),
        )

    def test_generator_files_are_the_ones_that_ran(self) -> None:
        for relative, digest in self.settings["generator_files"].items():
            self.assertEqual(_sha(ROOT / relative), digest, relative)

    def test_the_recorded_implementation_digest_recomputes(self) -> None:
        # Provenance pinned by CONTENT, which verifies in any checkout.
        from dt_adoc.concordance.simulate import implementation_digest

        self.assertEqual(
            self.settings["provenance"]["implementation_digest"],
            implementation_digest(ROOT),
        )

    def test_recorded_commit_is_reachable_from_the_reviewed_tree(self) -> None:
        # Reachability is a property of commits, and a tree has no parents, so
        # "the accepted tree" is resolved to the commit(s) carrying exactly
        # HEAD's tree. In a working checkout that is HEAD itself. In the
        # independent review's detached snapshot HEAD is a parentless
        # `git commit-tree` copy of the reviewed tree, and the real commit
        # carrying the same tree is found on the shared refs. Requiring tree
        # identity ties the ancestry claim to the exact bytes under review.
        commit = self.settings["provenance"]["git_commit"]
        from tests.unit.source_history import REASON_PREFIX, commit_available

        if not commit_available(commit):
            self.skipTest(
                f"{REASON_PREFIX}: recorded commit {commit[:12]} is absent from this "
                "history-free repository (docs/ORIGIN.md)"
            )

        def git(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run(
                ["git", "-C", str(ROOT), *args],
                capture_output=True,
                text=True,
                check=False,
            )

        tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
        self.assertTrue(tree, "HEAD has no tree")
        carriers = ["HEAD"] + [
            line.split()[0]
            for line in git("log", "--all", "--format=%H %T").stdout.splitlines()
            if line and line.split()[1] == tree
        ]
        reachable = [
            c
            for c in carriers
            if git("merge-base", "--is-ancestor", commit, c).returncode == 0
        ]
        self.assertTrue(
            reachable,
            f"{commit} is not an ancestor of any commit carrying tree {tree}: "
            f"checked {carriers}",
        )

    def test_executable_identity_is_computed(self) -> None:
        identity = self.settings["executable_identity"]
        same = all(len(set(v.values())) == 1 for v in identity.values())
        self.assertEqual(self.settings["executable_identical_to_parent"], same)


if __name__ == "__main__":
    unittest.main()
