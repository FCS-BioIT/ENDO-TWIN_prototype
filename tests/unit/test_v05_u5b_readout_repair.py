"""U5b guards: one rule repaired, in a new version, with its transient measured.

`docs/v05_mechanistic_integration_plan.md` §17 U5b. Four things are asserted here
rather than described, because each is a way this unit could look finished and
not be:

1. **v0.5.1 is emitted, not hand-edited.** It rebuilds byte for byte from v0.5.0
   through `dt_adoc.reporting.u5b_increment`, differs from v0.5.0 in exactly the
   declared files, and changes exactly one rule. v0.5.0 is untouched (its own
   identity guard is `tests/unit/test_v05_scaffold.py`).
2. **The composed function of every node is unchanged**, checked node by node
   over all 2**19 assignments rather than inferred from "the conjuncts are
   absorbed" -- and the one structural fact that DOES move, the interventional
   inertness of the two markers, is pinned so it cannot be lost from the record.
3. **The transient comparison is what was pre-registered**: the constants match
   the frozen file, the seed blocks are disjoint, and every primary interval is
   recomputed here from the committed per-block values.
4. **No simulation runs here.** The paired run is minutes of MaBoSS; this module
   reads its committed artifacts, and the integration suite re-runs the pairing.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import re
import sys
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.topology import parse_bnd_rules, reconcile
from dt_adoc.reporting import u5b_readout_transient as transient
from dt_adoc.reporting.structure import load_structure
from dt_adoc.reporting.u5b_increment import (
    ADDED_FILES,
    CHANGED_FILES,
    LOCAL_ADJUDICATIONS,
    MODEL_DIR,
    PARENT_DIR,
    REPAIRED_NODE,
    adjudications_for_increment,
    build_increment,
    structural_identity,
)

PARENT = ROOT / PARENT_DIR
MODEL = ROOT / MODEL_DIR
RECORD = ROOT / "docs/v05_u5b_readout_repair.md"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(directory: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(directory)): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def _tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class IncrementTest(unittest.TestCase):
    def test_the_committed_directory_rebuilds_byte_for_byte(self) -> None:
        built = build_increment(ROOT)
        on_disk = _files(MODEL)
        self.assertEqual(sorted(built), sorted(on_disk))
        for name in sorted(built):
            with self.subTest(file=name):
                self.assertEqual(built[name], on_disk[name])

    def test_only_the_declared_files_differ_from_the_parent(self) -> None:
        parent, child = _files(PARENT), _files(MODEL)
        self.assertEqual(set(child) - set(parent), set(ADDED_FILES))
        self.assertEqual(set(parent) - set(child), set())
        differing = {n for n in parent if parent[n] != child[n]}
        self.assertEqual(differing, set(CHANGED_FILES))

    def test_exactly_one_rule_changed_and_it_is_the_repair(self) -> None:
        before = parse_bnd_rules(PARENT / "network.bnd")
        after = parse_bnd_rules(MODEL / "network.bnd")
        self.assertEqual(sorted(before), sorted(after), "no node added or removed")
        changed = {n: (before[n], after[n]) for n in before if before[n] != after[n]}
        self.assertEqual(
            changed,
            {
                REPAIRED_NODE: (
                    "S_DECIDUALIZED and S_PRL and S_IGFBP1",
                    "S_DECIDUALIZED",
                )
            },
        )

    def test_the_parent_still_carries_the_unrepaired_rule(self) -> None:
        self.assertIn(
            "logic = S_DECIDUALIZED and S_PRL and S_IGFBP1;",
            (PARENT / "network.bnd").read_text(encoding="utf-8"),
        )

    def test_the_provenance_records_the_increment_and_its_hashes_hold(self) -> None:
        record = tomllib.loads((MODEL / "provenance.toml").read_text(encoding="utf-8"))
        self.assertEqual(record["model_version"], "adoc-literature-superset-v0.5.1")
        increment = record["increment"]
        self.assertEqual(increment["mechanism_changes"], 1)
        self.assertEqual(increment["rule_changed"], REPAIRED_NODE)
        self.assertEqual(increment["parent_model_version"], PARENT_DIR.name)
        self.assertEqual(increment["retired_edges"], ["LE079", "LE080"])
        self.assertEqual(
            sorted(increment["files_differing_from_parent"]), sorted(CHANGED_FILES)
        )
        self.assertEqual(increment["files_added"], sorted(ADDED_FILES))
        self.assertNotIn("scaffold", record, "an increment is not a scaffold")
        self.assertEqual(
            increment["parent_provenance_sha256"], _sha(PARENT / "provenance.toml")
        )
        self.assertEqual(
            increment["parent_network_bnd_sha256"], _sha(PARENT / "network.bnd")
        )
        self.assertEqual(
            increment["parent_baseline_cfg_sha256"], _sha(PARENT / "baseline.cfg")
        )
        # Every recorded artifact hash is the file's actual hash, and every path
        # names this directory, not the parent.
        for key, path in record["artifacts"].items():
            with self.subTest(artifact=key):
                self.assertTrue(path.startswith(MODEL_DIR.as_posix() + "/"))
                self.assertEqual(
                    record["artifact_hashes"][f"{key}_sha256"], _sha(ROOT / path)
                )
        self.assertEqual(
            record["artifact_hashes"]["topology_sha256"], _sha(MODEL / "topology.tsv")
        )
        # Both derivation inputs of topology.tsv are hashed: the shared
        # adjudications and the version-local ones this increment adds.
        self.assertEqual(
            record["source_hashes"]["topology_adjudications_sha256"],
            _sha(ROOT / "config/topology_parity_exemptions.tsv"),
        )
        self.assertEqual(
            record["source_hashes"]["topology_increment_adjudications_sha256"],
            _sha(MODEL / LOCAL_ADJUDICATIONS),
        )
        for name, digest in record["condition_hashes"].items():
            cfg = MODEL / "conditions" / (name.removesuffix("_cfg_sha256") + ".cfg")
            with self.subTest(condition=name):
                self.assertEqual(digest, _sha(cfg))

    def test_the_retirement_is_derived_by_the_repositorys_own_parity_code(self) -> None:
        table = reconcile(
            parse_bnd_rules(MODEL / "network.bnd"),
            _tsv(MODEL / "edge_evidence.tsv"),
            adjudications_for_increment(ROOT, MODEL / LOCAL_ADJUDICATIONS),
        )
        self.assertEqual(table, _tsv(MODEL / "topology.tsv"))
        retired = {
            (r["source"], r["edge_id"], r["exemption_id"])
            for r in table
            if r["provenance_status"] == "retired" and r["target"] == REPAIRED_NODE
        }
        self.assertEqual(
            retired,
            {("S_IGFBP1", "LE080", "INC-U5B-02"), ("S_PRL", "LE079", "INC-U5B-01")},
        )
        # History kept: the curated rows are still in edge_evidence.tsv.
        ids = {r["edge_id"] for r in _tsv(MODEL / "edge_evidence.tsv")}
        self.assertTrue({"LE079", "LE080"} <= ids)

    def test_the_shared_adjudication_file_was_not_edited(self) -> None:
        """v0.4.0 and v0.5.0 pin its hash; the retirement is version-local."""
        shared = _sha(ROOT / "config/topology_parity_exemptions.tsv")
        for version in ("adoc-literature-superset-v0.4.0", PARENT_DIR.name):
            record = tomllib.loads(
                (ROOT / "models/superset" / version / "provenance.toml").read_text(
                    encoding="utf-8"
                )
            )
            with self.subTest(version=version):
                self.assertEqual(
                    record["source_hashes"]["topology_adjudications_sha256"], shared
                )


class StructuralIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.identity = structural_identity(ROOT)
        cls.before = load_structure(PARENT_DIR.name, ROOT)
        cls.after = load_structure(MODEL_DIR.name, ROOT)

    def test_no_nodes_composed_function_differs(self) -> None:
        self.assertEqual(self.identity["enumerated_assignments"], 2**19)
        self.assertEqual(self.identity["nodes"], 59)
        self.assertEqual(
            self.identity["free_variables"], self.identity["free_variables_parent"]
        )
        self.assertEqual(self.identity["rules_changed"], [REPAIRED_NODE])
        self.assertEqual(self.identity["nodes_whose_composed_function_differs"], [])

    def test_the_blast_radius_is_the_one_leaf(self) -> None:
        self.assertEqual(self.identity["readers_of_repaired_node"], [])
        self.assertIn(
            "S_DECIDUALIZED",
            re.findall(r"\b\w+\b", self.identity["adhesion_competence_rule"]),
        )

    def test_the_audited_numbers_are_re_derived_not_inherited(self) -> None:
        def numbers(facts):
            alias = facts.alias_classes
            return (
                len(facts.node_ids),
                len(facts.free),
                facts.distinct_function_count,
                len(alias),
                len(next(c for c in alias if "E_PAEP" in c)),
                len(next(c for c in alias if "S_DECIDUALIZED" in c)),
            )

        self.assertEqual(numbers(self.after), (59, 19, 35, 8, 9, 6))
        self.assertEqual(numbers(self.after), numbers(self.before))
        self.assertEqual(
            sorted(map(sorted, self.after.alias_classes)),
            sorted(map(sorted, self.before.alias_classes)),
        )

    def test_what_does_move_structurally_is_exactly_this(self) -> None:
        """Two edges, one depth, and the markers' INTERVENTIONAL inertness.

        `load_structure` calls a node phenotype-inert when pinning it ON or OFF
        changes no output. In v0.5.0, clamping S_PRL or S_IGFBP1 OFF switches
        the readout off; in v0.5.1 it cannot. So the fixed point of an
        UNPERTURBED run cannot move, but a perturbation that clamped a marker
        would read differently -- which is the leak being removed, and must be
        recorded as a change rather than hidden inside "nothing moves".
        """
        self.assertEqual(
            sorted(set(self.before.edges) ^ set(self.after.edges)),
            [
                ("S_IGFBP1", REPAIRED_NODE, "activation"),
                ("S_PRL", REPAIRED_NODE, "activation"),
            ],
        )
        self.assertEqual(
            sorted(set(self.after.phenotype_inert) - set(self.before.phenotype_inert)),
            ["S_IGFBP1", "S_PRL"],
        )
        self.assertEqual(
            set(self.before.phenotype_inert) - set(self.after.phenotype_inert), set()
        )
        self.assertEqual(self.before.absorbed_edges, self.after.absorbed_edges)
        self.assertEqual(
            self.before.never_binding_inhibitions, self.after.never_binding_inhibitions
        )
        moved = {
            n: (self.before.depth[n], self.after.depth[n])
            for n in self.before.depth
            if self.before.depth[n] != self.after.depth[n]
        }
        self.assertEqual(moved, {REPAIRED_NODE: (7, 6)})

    def test_no_catalogued_perturbation_clamps_either_marker(self) -> None:
        """Why the interventional change reaches no committed arm today."""
        for path in [
            ROOT / "config/perturbations.yaml",
            ROOT / "config/protocols.yaml",
            *sorted((MODEL / "conditions").glob("*.cfg")),
        ]:
            text = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotRegex(text, r"\bS_PRL\b|\bS_IGFBP1\b")


class TransientArtifactTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.settings = json.loads(
            (ROOT / transient.SETTINGS_JSON).read_text(encoding="utf-8")
        )
        cls.rows = _tsv(ROOT / transient.COMPARISON_TSV)
        cls.blocks = _tsv(ROOT / transient.BLOCKS_TSV)
        cls.prereg = (ROOT / transient.PREREGISTRATION).read_text(encoding="utf-8")

    def test_the_run_is_the_preregistered_one(self) -> None:
        s = self.settings
        self.assertEqual(
            s["provenance"]["preregistration_sha256"],
            _sha(ROOT / transient.PREREGISTRATION),
        )
        self.assertEqual(s["tolerance"], 0.005)
        self.assertIn("`δ = 0.005`", self.prereg)
        self.assertEqual(s["replicates"], 20)
        self.assertIn("`R = 20`", self.prereg)
        self.assertEqual(s["trajectory_counts"], [20_000, 2_000])
        self.assertEqual(s["governing_trajectory_count"], 20_000)
        self.assertIn("`seed_r = 1 + r·20,000`", self.prereg)
        self.assertIn("`seed_r = 400,001 + r·2,000`", self.prereg)
        self.assertEqual(s["arms"], list(transient.ARMS))
        self.assertEqual(len(s["cells"]), 10)
        for cell in s["cells"]:
            self.assertIn(f"`{cell}`", self.prereg)
        self.assertEqual(s["families"]["primary_intervals"], 20)

    def test_the_models_simulated_are_the_committed_ones(self) -> None:
        models = self.settings["provenance"]["models"]
        for directory in (PARENT, MODEL):
            with self.subTest(model=directory.name):
                self.assertEqual(
                    models[directory.name]["network_bnd_sha256"],
                    _sha(directory / "network.bnd"),
                )
                self.assertEqual(
                    models[directory.name]["baseline_cfg_sha256"],
                    _sha(directory / "baseline.cfg"),
                )

    def test_seed_blocks_are_disjoint_between_replicates_and_counts(self) -> None:
        ranges = set()
        for row in self.blocks:
            low, high = (int(x) for x in row["trajectory_seed_range"].split(".."))
            self.assertEqual(high - low + 1, int(row["trajectory_count"]))
            self.assertEqual(
                low,
                transient.replicate_seed(
                    int(row["replicate"]), int(row["trajectory_count"])
                ),
            )
            ranges.add((low, high))
        ordered = sorted(ranges)
        self.assertEqual(len(ordered), 2 * transient.REPLICATES)
        for (_, high), (low, _) in itertools.pairwise(ordered):
            self.assertLess(high, low, "two replicate blocks share a trajectory seed")

    def test_every_primary_interval_recomputes_from_the_committed_blocks(self) -> None:
        q = self.settings["families"]["t_quantile"]["primary"]
        by_key: dict[tuple[str, str, str], list[float]] = {}
        for row in self.blocks:
            for estimand in transient.ESTIMANDS:
                by_key.setdefault(
                    (row["trajectory_count"], row["cell"], estimand), []
                ).append(float(row[f"paired_{estimand}"]))
        primary = [r for r in self.rows if r["family"] == "primary"]
        self.assertEqual(len(primary), 2 * 20)
        for row in primary:
            diffs = by_key[(row["trajectory_count"], row["cell"], row["estimand"])]
            self.assertEqual(len(diffs), transient.REPLICATES)
            recomputed = transient.classify(diffs, q)
            with self.subTest(
                cell=row["cell"], estimand=row["estimand"], n=row["trajectory_count"]
            ):
                self.assertAlmostEqual(
                    recomputed["mean"], float(row["mean"]), places=12
                )
                self.assertAlmostEqual(recomputed["se"], float(row["se"]), places=12)
                self.assertEqual(recomputed["verdict"], row["verdict"])

    def test_the_paired_difference_is_the_difference_of_the_two_arms(self) -> None:
        for row in self.blocks:
            for estimand in transient.ESTIMANDS:
                with self.subTest(cell=row["cell"], r=row["replicate"], e=estimand):
                    self.assertAlmostEqual(
                        float(row[f"paired_{estimand}"]),
                        float(row[f"repaired_{estimand}"])
                        - float(row[f"parent_{estimand}"]),
                        places=12,
                    )

    def test_every_verdict_follows_the_preregistered_table(self) -> None:
        tol = self.settings["tolerance"]
        for row in self.rows:
            low, high = float(row["low"]), float(row["high"])
            with self.subTest(cell=row["cell"], node=row["node_id"], e=row["estimand"]):
                if row["verdict"] == "WITHIN_TOLERANCE":
                    self.assertTrue(-tol <= low and high <= tol)
                elif row["verdict"] == "BEYOND_TOLERANCE":
                    self.assertTrue(high < -tol or low > tol)
                elif row["verdict"] == "EXACTLY_IDENTICAL":
                    self.assertEqual(float(row["sd"]), 0.0)
                    self.assertEqual(float(row["mean"]), 0.0)
                else:
                    self.assertEqual(row["verdict"], "INDETERMINATE")

    def test_the_pairing_gives_exact_identity_where_the_rules_never_disagree(
        self,
    ) -> None:
        """Pre-registered expectation 1: if this fails the run is invalid."""
        held = self.settings["expectations"][
            "1_exact_identity_where_rules_never_disagree"
        ]
        self.assertTrue(held["held"], held)
        for row in self.rows:
            if row["cell"] in transient.EXACT_IDENTITY_CELLS:
                with self.subTest(cell=row["cell"], node=row["node_id"]):
                    self.assertEqual(row["verdict"], "EXACTLY_IDENTICAL")

    def test_no_other_node_moves_beyond_tolerance(self) -> None:
        """Pre-registered expectation 2's falsifying half: BEYOND is a defect."""
        governing = [
            r
            for r in self.rows
            if r["family"] == "blast_radius" and r["trajectory_count"] == "20000"
        ]
        self.assertEqual(
            len(governing), self.settings["families"]["blast_radius_intervals"]
        )
        self.assertEqual(
            [r for r in governing if r["verdict"] == "BEYOND_TOLERANCE"], []
        )

    def test_the_stability_check_is_recorded_for_every_primary_interval(self) -> None:
        stability = self.settings["stability"]
        self.assertEqual(len(stability), 20)
        for entry in stability:
            with self.subTest(cell=entry["cell"], e=entry["estimand"]):
                expected = entry["verdict_governing"] if entry["stable"] else "UNSTABLE"
                self.assertEqual(entry["reported_verdict"], expected)
                self.assertEqual(
                    entry["stable"],
                    entry["absolute_gap"] <= entry["bound"]
                    and entry["verdict_governing"] == entry["verdict_check"],
                )

    def test_the_record_quotes_the_reported_verdicts(self) -> None:
        text = RECORD.read_text(encoding="utf-8")
        for key, verdict in self.settings["primary_reported_verdicts"].items():
            cell, estimand = key.split(":")
            with self.subTest(cell=cell, estimand=estimand):
                line = next(
                    ln for ln in text.splitlines() if ln.startswith(f"| `{cell}` |")
                )
                self.assertIn(verdict, line)
        self.assertIn("no detected transient change at this precision", text)
        self.assertIn('not "no change"', text)

    def test_quoted_primary_means_match_the_artifact(self) -> None:
        """Every number the record's primary table prints is the artifact's."""
        text = RECORD.read_text(encoding="utf-8")
        governing = {
            (r["cell"], r["estimand"]): r
            for r in self.rows
            if r["family"] == "primary" and r["trajectory_count"] == "20000"
        }
        for (cell, estimand), row in governing.items():
            line = next(
                ln for ln in text.splitlines() if ln.startswith(f"| `{cell}` |")
            )
            with self.subTest(cell=cell, estimand=estimand):
                self.assertIn(f"{float(row['mean']):+.4f}", line)


if __name__ == "__main__":
    unittest.main()
