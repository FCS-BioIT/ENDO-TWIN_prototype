"""v0.5.2 guards: two absorbed conjuncts removed, in a new version.

The 2026-09-28 reconciliation of the 163-paper literature re-audit, items C1
and C5. Each check below guards a way this unit could look finished without
being finished:

1. **v0.5.2 is emitted, not hand-edited.** It rebuilds byte for byte from v0.5.1
   through ``dt_adoc.reporting.v052_increment``, differs from v0.5.1 in exactly
   the declared files, and changes exactly the two rules. v0.5.1 is untouched;
   its own guard is ``tests/unit/test_v05_u5b_readout_repair.py``.
2. **The composed function of every node is unchanged.** This is checked node
   by node over all 2**19 assignments, not inferred from "the conjuncts are
   absorbed". The blast radius, which unlike U5b's is not a leaf, is pinned to
   the seven nodes the pre-registration names.
3. **The attribution variants are never committed as model versions.** The
   pre-registration's precedence is recorded by commit hash in
   ``docs/v052_paep_hand2_cleanup.md``, not asserted here, because the review
   gate reads a synthetic snapshot without the repository's history.
4. **No simulation runs here.**
"""

from __future__ import annotations

import csv
import hashlib
import sys
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.model.topology import parse_bnd_rules, reconcile
from dt_adoc.reporting.u5b_increment import adjudications_for_increment
from dt_adoc.reporting.v052_increment import (
    CHANGED_FILES,
    CHANGES,
    LOCAL_ADJUDICATIONS,
    MODEL_DIR,
    PARENT_DIR,
    build_increment,
    structural_identity,
)

PARENT = ROOT / PARENT_DIR
MODEL = ROOT / MODEL_DIR

#: Pre-registration section 1, stated there before v0.5.2 existed.
PREREGISTERED_AFFECTED = {
    "E_ESTROGENIC_PROLIFERATION",
    "E_RECEPTIVE_SURFACE",
    "OUT_EPITHELIAL_RECEPTIVE",
    "OUT_MATERNAL_ADHESION_COMPETENCE",
    "OUT_STABLE_ADHESION",
    "X_ADHESION_ROUTE_REDUNDANT",
    "X_ADHESION_ROUTE_SPP1",
}


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
        self.assertEqual(set(child), set(parent), "no file added or removed")
        differing = {n for n in parent if parent[n] != child[n]}
        self.assertEqual(differing, set(CHANGED_FILES))

    def test_exactly_the_two_rules_changed_and_they_are_the_repairs(self) -> None:
        before = parse_bnd_rules(PARENT / "network.bnd")
        after = parse_bnd_rules(MODEL / "network.bnd")
        self.assertEqual(sorted(before), sorted(after), "no node added or removed")
        changed = {n: (before[n], after[n]) for n in before if before[n] != after[n]}
        self.assertEqual(
            changed,
            {
                "OUT_EPITHELIAL_RECEPTIVE": (
                    "E_RECEPTIVE_SURFACE and E_PAEP",
                    "E_RECEPTIVE_SURFACE",
                ),
                "E_ESTROGENIC_PROLIFERATION": (
                    "IN_E2 and S_FGF_MITOGENIC and not S_HAND2",
                    "IN_E2 and S_FGF_MITOGENIC",
                ),
            },
        )

    def test_the_parent_still_carries_both_conjuncts(self) -> None:
        text = (PARENT / "network.bnd").read_text(encoding="utf-8")
        self.assertIn("logic = E_RECEPTIVE_SURFACE and E_PAEP;", text)
        self.assertIn("logic = IN_E2 and S_FGF_MITOGENIC and not S_HAND2;", text)

    def test_the_provenance_records_the_increment_and_its_hashes_hold(self) -> None:
        record = tomllib.loads((MODEL / "provenance.toml").read_text(encoding="utf-8"))
        self.assertEqual(record["model_version"], "adoc-literature-superset-v0.5.2")
        self.assertEqual(record["family_id"], "adoc_literature_superset_v052")
        increment = record["increment"]
        self.assertEqual(increment["mechanism_changes"], 2)
        self.assertEqual(increment["changes"], ["C1", "C5"])
        self.assertEqual(increment["parent_model_version"], PARENT_DIR.name)
        self.assertEqual(increment["retired_edges"], ["LE077", "LE094"])
        self.assertEqual(
            sorted(increment["files_differing_from_parent"]), sorted(CHANGED_FILES)
        )
        self.assertEqual(increment["files_added"], [])
        for change in CHANGES.values():
            prefix = change.change_id.lower()
            with self.subTest(change=change.change_id):
                self.assertEqual(increment[f"{prefix}_rule_changed"], change.node)
                self.assertEqual(
                    increment[f"{prefix}_logic_before"], change.logic_before
                )
                self.assertEqual(increment[f"{prefix}_logic_after"], change.logic_after)
        self.assertEqual(
            increment["parent_provenance_sha256"], _sha(PARENT / "provenance.toml")
        )
        self.assertEqual(
            increment["parent_network_bnd_sha256"], _sha(PARENT / "network.bnd")
        )
        self.assertEqual(
            increment["parent_baseline_cfg_sha256"], _sha(PARENT / "baseline.cfg")
        )
        for key, path in record["artifacts"].items():
            with self.subTest(artifact=key):
                self.assertTrue(path.startswith(MODEL_DIR.as_posix() + "/"))
                self.assertEqual(
                    record["artifact_hashes"][f"{key}_sha256"], _sha(ROOT / path)
                )
        self.assertEqual(
            record["artifact_hashes"]["topology_sha256"], _sha(MODEL / "topology.tsv")
        )
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

    def test_the_retirements_are_derived_by_the_repositorys_own_parity_code(
        self,
    ) -> None:
        table = reconcile(
            parse_bnd_rules(MODEL / "network.bnd"),
            _tsv(MODEL / "edge_evidence.tsv"),
            adjudications_for_increment(ROOT, MODEL / LOCAL_ADJUDICATIONS),
        )
        self.assertEqual(table, _tsv(MODEL / "topology.tsv"))
        retired = {
            (r["source"], r["target"], r["edge_id"], r["exemption_id"])
            for r in table
            if r["provenance_status"] == "retired"
        }
        self.assertTrue(
            {
                ("E_PAEP", "OUT_EPITHELIAL_RECEPTIVE", "LE077", "INC-V052-C1"),
                ("S_HAND2", "E_ESTROGENIC_PROLIFERATION", "LE094", "INC-V052-C5"),
            }
            <= retired
        )
        # U5b's retirements carry over unchanged.
        self.assertTrue(
            {
                ("S_PRL", "OUT_STROMAL_DECIDUALIZED", "LE079", "INC-U5B-01"),
                ("S_IGFBP1", "OUT_STROMAL_DECIDUALIZED", "LE080", "INC-U5B-02"),
            }
            <= retired
        )
        ids = {r["edge_id"] for r in _tsv(MODEL / "edge_evidence.tsv")}
        self.assertTrue({"LE077", "LE094"} <= ids, "curated history is kept")

    def test_the_parents_adjudications_are_carried_verbatim(self) -> None:
        parent_rows = _tsv(PARENT / LOCAL_ADJUDICATIONS)
        rows = _tsv(MODEL / LOCAL_ADJUDICATIONS)
        self.assertEqual(rows[: len(parent_rows)], parent_rows)
        self.assertEqual(
            [r["exemption_id"] for r in rows[len(parent_rows) :]],
            ["INC-V052-C1", "INC-V052-C5"],
        )

    def test_the_shared_adjudication_file_was_not_edited(self) -> None:
        shared = _sha(ROOT / "config/topology_parity_exemptions.tsv")
        for version in (
            "adoc-literature-superset-v0.4.0",
            "adoc-literature-superset-v0.5.0",
            PARENT_DIR.name,
        ):
            record = tomllib.loads(
                (ROOT / "models/superset" / version / "provenance.toml").read_text(
                    encoding="utf-8"
                )
            )
            with self.subTest(version=version):
                self.assertEqual(
                    record["source_hashes"]["topology_adjudications_sha256"], shared
                )

    def test_no_attribution_variant_is_committed_as_a_model_version(self) -> None:
        names = {p.name for p in (ROOT / "models/superset").iterdir()}
        self.assertFalse({n for n in names if n.endswith(("c1only", "c5only"))})


class StructuralIdentityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.identity = structural_identity(ROOT)

    def test_no_nodes_composed_function_differs(self) -> None:
        self.assertEqual(self.identity["enumerated_assignments"], 2**19)
        self.assertEqual(
            self.identity["free_variables"], self.identity["free_variables_parent"]
        )
        self.assertEqual(self.identity["nodes_whose_composed_function_differs"], [])

    def test_the_blast_radius_is_the_preregistered_seven_nodes(self) -> None:
        self.assertEqual(
            self.identity["rules_changed"],
            ["E_ESTROGENIC_PROLIFERATION", "OUT_EPITHELIAL_RECEPTIVE"],
        )
        self.assertEqual(
            self.identity["readers_of_changed_nodes"],
            {
                "E_ESTROGENIC_PROLIFERATION": ["E_RECEPTIVE_SURFACE"],
                "OUT_EPITHELIAL_RECEPTIVE": ["OUT_MATERNAL_ADHESION_COMPETENCE"],
            },
        )
        self.assertEqual(set(self.identity["affected_nodes"]), PREREGISTERED_AFFECTED)


class InterventionalDifferenceTest(unittest.TestCase):
    """Conditions cannot separate the versions; three internal clamps can.

    The exhaustive enumeration is committed in separating_clamps.json (minutes
    of truth tables). Here each listed clamp is re-verified directly, and the
    artifact is bound to the committed rules and generator by hash.
    """

    ARTIFACT = ROOT / "docs/v052_paep_hand2/separating_clamps.json"
    EXPECTED = frozenset(
        {
            ("E_PAEP", 0),
            ("E_RECEPTIVE_SURFACE", 1),
            ("S_FGF_MITOGENIC", 1),
        }
    )

    @classmethod
    def setUpClass(cls) -> None:
        import json

        cls.record = json.loads(cls.ARTIFACT.read_text(encoding="utf-8"))

    def test_the_artifact_is_bound_to_the_committed_rules_and_generator(self) -> None:
        self.assertEqual(
            self.record["parent_network_bnd_sha256"], _sha(PARENT / "network.bnd")
        )
        self.assertEqual(self.record["network_bnd_sha256"], _sha(MODEL / "network.bnd"))
        self.assertEqual(
            self.record["generator_sha256"],
            _sha(SRC / "dt_adoc/reporting/v052_interventions.py"),
        )

    def test_exactly_the_three_expected_clamps_separate_the_versions(self) -> None:
        found = {
            (r["clamped_node"], r["value"]) for r in self.record["separating_clamps"]
        }
        self.assertEqual(found, self.EXPECTED)

    def test_each_listed_clamp_does_separate_them(self) -> None:
        from dt_adoc.reporting.v052_interventions import _CONSTANT, _composed

        parent = parse_bnd_rules(PARENT / "network.bnd")
        child = parse_bnd_rules(MODEL / "network.bnd")
        free = tuple(n for n in parent if parent[n].strip() == n)
        for row in self.record["separating_clamps"]:
            node, value = row["clamped_node"], row["value"]
            with self.subTest(clamp=f"{node}={value}"):
                a = _composed({**parent, node: _CONSTANT[value]}, free)
                b = _composed({**child, node: _CONSTANT[value]}, free)
                self.assertEqual(
                    sorted(n for n in a if a[n] != b[n]),
                    row["nodes_whose_function_differs"],
                )


class EvidenceRecordTest(unittest.TestCase):
    """C1 and C5 rest on docs/v052_paep_hand2/evidence.tsv, not on the audit."""

    RECORD = ROOT / "docs/v052_paep_hand2/evidence.tsv"

    def test_every_change_has_evidence_and_every_row_is_complete(self) -> None:
        rows = _tsv(self.RECORD)
        self.assertEqual({r["change_id"] for r in rows}, set(CHANGES))
        for row in rows:
            with self.subTest(row=row["first_author"], change=row["change_id"]):
                self.assertTrue(all(value.strip() for value in row.values()))
                self.assertTrue(row["does_not_support"].strip())

    def test_every_cited_pdf_is_the_one_hashed(self) -> None:
        """PDFs are gitignored, so a checkout without them skips, never passes."""
        rows = [r for r in _tsv(self.RECORD) if r["pdf_sha256"] != "not_applicable"]
        missing = [
            r["local_pdf"] for r in rows if not (ROOT / r["local_pdf"]).is_file()
        ]
        if missing:
            self.skipTest(f"{len(missing)} cited PDF(s) not in this checkout")
        for row in rows:
            with self.subTest(pdf=row["local_pdf"]):
                self.assertEqual(_sha(ROOT / row["local_pdf"]), row["pdf_sha256"])

    def test_registered_references_carry_the_registered_doi(self) -> None:
        registry = {
            r["ref_id"]: r["doi"]
            for r in _tsv(ROOT / "context/literature/references.tsv")
        }
        for row in _tsv(self.RECORD):
            if row["ref_id"].startswith("REF-"):
                with self.subTest(ref=row["ref_id"]):
                    self.assertEqual(registry[row["ref_id"]], row["doi"])


if __name__ == "__main__":
    unittest.main()


class Run2ArtifactTest(unittest.TestCase):
    """Run 2 is the one addendum 01 registered, and its numbers recompute."""

    DIR = ROOT / "docs/v052_paep_hand2"

    @classmethod
    def setUpClass(cls) -> None:
        import json

        cls.settings = json.loads(
            (cls.DIR / "transient_run_settings.json").read_text(encoding="utf-8")
        )
        cls.rows = _tsv(cls.DIR / "transient_comparison.tsv")
        cls.blocks = _tsv(cls.DIR / "transient_blocks.tsv")

    def test_the_run_is_the_registered_run2(self) -> None:
        s = self.settings
        self.assertEqual(s["run_id"], "run2")
        self.assertEqual(s["snap_threshold"], 1e-12)
        self.assertEqual(
            s["seed_rule"],
            {"20000": "1000001 + r * 20000", "2000": "1400001 + r * 2000"},
        )
        prov = s["provenance"]
        self.assertEqual(
            prov["addendum_sha256"],
            _sha(self.DIR / "transient_preregistration_addendum_01.md"),
        )
        self.assertEqual(
            prov["preregistration_sha256"],
            _sha(self.DIR / "transient_preregistration.md"),
        )

    def test_the_models_simulated_are_the_committed_ones(self) -> None:
        models = self.settings["provenance"]["models"]
        for version, directory in ((PARENT_DIR.name, PARENT), (MODEL_DIR.name, MODEL)):
            with self.subTest(version=version):
                self.assertEqual(
                    models[version]["network_bnd_sha256"],
                    _sha(directory / "network.bnd"),
                )

    def test_run2_seeds_are_disjoint_from_run1(self) -> None:
        run1 = _tsv(self.DIR / "run1_invalid/transient_blocks.tsv")

        def ranges(rows: list[dict[str, str]]) -> set[tuple[int, int]]:
            return {
                tuple(int(x) for x in r["trajectory_seed_range"].split(".."))
                for r in rows
            }

        new, old = ranges(self.blocks), ranges(run1)
        self.assertTrue(new and old)
        for a, b in new:
            for c, d in old:
                self.assertTrue(b < c or d < a, f"{a}..{b} overlaps {c}..{d}")

    def test_every_primary_interval_recomputes_from_the_blocks(self) -> None:
        import math
        from statistics import mean, stdev

        by_key: dict[tuple[str, str, str, str], list[float]] = {}
        for b in self.blocks:
            key = (b["comparison"], b["trajectory_count"], b["cell"], b["node_id"])
            by_key.setdefault(key, []).append(float(b["paired_time_averaged"]))
        checked = 0
        for r in self.rows:
            if r["family"] != "primary" or r["estimand"] != "time_averaged":
                continue
            diffs = by_key[
                (r["comparison"], r["trajectory_count"], r["cell"], r["node_id"])
            ]
            with self.subTest(row=f"{r['comparison']}:{r['cell']}:{r['node_id']}"):
                self.assertAlmostEqual(mean(diffs), float(r["mean"]), places=12)
                se = stdev(diffs) / math.sqrt(len(diffs))
                self.assertAlmostEqual(se, float(r["se"]), places=12)
                checked += 1
        self.assertGreater(checked, 0)

    def test_every_verdict_follows_the_table(self) -> None:
        for r in self.rows:
            low, high = float(r["low"]), float(r["high"])
            verdict = r["verdict"]
            with self.subTest(row=f"{r['comparison']}:{r['cell']}:{r['node_id']}"):
                if verdict == "WITHIN_TOLERANCE":
                    self.assertTrue(-0.005 <= low and high <= 0.005)
                elif verdict == "BEYOND_TOLERANCE":
                    self.assertTrue(high < -0.005 or low > 0.005)
                elif verdict == "EXACTLY_IDENTICAL":
                    self.assertEqual((float(r["mean"]), float(r["sd"])), (0.0, 0.0))
