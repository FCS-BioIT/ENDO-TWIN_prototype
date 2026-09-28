"""The scRNA observability map must not drift from the model or its sources.

The map's value is that it keeps TWO things apart that an earlier revision of
this very docstring collapsed. It used to say "an observation of `S_PRL`
resolves a six-member equivalence class, not `S_PRL`" -- which is exactly the
interpretation the branch has since rejected, because it blames the assay for
the rules.

The corrected invariant:

* `S_PRL` and `S_IGFBP1` are **separately measurable biological states** --
  distinct transcripts, in distinct cells. The measurement resolves them.
* Under **unmodified v0.4** they happen to realise the same Boolean function, so
  the MODEL cannot represent a difference between them.
* A measured divergence therefore **falsifies the aliasing**; it does not
  indicate inadequate measurement resolution.

Function equality is also not interventional equivalence: clamping `S_PRL`
overrides only `S_PRL`'s rule. This repository proves the asymmetry in its own
numbers, and the tests below pin it -- `E_CD98_CD9` is phenotype-inert while
`E_GP130_STAT3`, in the same class, is not.

These tests re-derive every derived column rather than trusting the committed
file, and fingerprint the canonical records the construction-role set depends
on, so neither the model nor its evidence sources can move underneath the map
while the suite stays green.
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class MapMatchesTheModel(unittest.TestCase):
    def test_loading_revalidates_every_derived_column(self) -> None:
        """The loader re-derives alias class, size, members, inertness, class."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = load_scrna_observation_map(ROOT)
        self.assertEqual(len(rows), 59)

    def test_regenerating_reproduces_the_committed_file_byte_for_byte(self) -> None:
        """The committed artifact is what the generator produces, not a fork."""
        import tempfile

        from dt_adoc.scrna.observability import write_map

        committed = (ROOT / "config" / "scrna_observation_map.tsv").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            target = write_map(ROOT, Path(tmp) / "regenerated.tsv")
            self.assertEqual(target.read_bytes(), committed)

    def test_every_model_node_has_exactly_one_row(self) -> None:
        from dt_adoc.reporting.structure import load_structure
        from dt_adoc.scrna.observability import (
            MODEL_VERSION,
            load_scrna_observation_map,
        )

        facts = load_structure(MODEL_VERSION, ROOT)
        rows = load_scrna_observation_map(ROOT)
        nodes = [row["model_node"] for row in rows]
        self.assertEqual(sorted(nodes), sorted(facts.node_ids))
        self.assertEqual(len(nodes), len(set(nodes)))


class MeasurementReachIsKeptApartFromModelReach(unittest.TestCase):
    """The distinction this map exists to hold, and once got backwards.

    An earlier revision said an observation "resolves the CLASS, not this node"
    and that conditioning one member "conditions the others identically". Both
    blamed the assay for the rules. These tests pin the corrected separation.
    """

    def test_an_aliased_row_states_a_model_limit_not_a_measurement_limit(
        self,
    ) -> None:
        from dt_adoc.scrna.observability import load_scrna_observation_map

        for row in load_scrna_observation_map(ROOT):
            if int(row["v04_class_size"]) > 1:
                with self.subTest(node=row["model_node"]):
                    text = row["v04_representational_resolution"]
                    self.assertIn("under UNMODIFIED v0.4 rules", text)
                    self.assertIn("FALSIFY", text)
                    self.assertNotIn("resolves the CLASS", text)

    def test_separately_measurable_nodes_say_so_even_when_aliased(self) -> None:
        """PRL and IGFBP1: the model conflates them, the measurement does not."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = {r["model_node"]: r for r in load_scrna_observation_map(ROOT)}
        self.assertEqual(
            rows["S_PRL"]["v04_function_class"],
            rows["S_IGFBP1"]["v04_function_class"],
        )
        for node in ("S_PRL", "S_IGFBP1"):
            with self.subTest(node=node):
                self.assertIn(
                    "separately quantifiable", rows[node]["measurement_resolution"]
                )

    def test_identical_function_does_not_mean_identical_intervention(self) -> None:
        """The in-repo counterexample, asserted so it cannot be forgotten.

        E_CD98_CD9 and E_GP130_STAT3 realise the same Boolean function and
        differ in phenotype-inertness. If that ever stops being true, the
        argument in docs/scrna_observability.md needs another example.
        """
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = {r["model_node"]: r for r in load_scrna_observation_map(ROOT)}
        self.assertEqual(
            rows["E_CD98_CD9"]["v04_function_class"],
            rows["E_GP130_STAT3"]["v04_function_class"],
        )
        self.assertNotEqual(
            rows["E_CD98_CD9"]["phenotype_inert"],
            rows["E_GP130_STAT3"]["phenotype_inert"],
        )

    def test_observable_states_span_fewer_model_signatures(self) -> None:
        """The headline, stated as a model deficit rather than a data ceiling."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = load_scrna_observation_map(ROOT)
        observable = [
            r for r in rows if r["measurement_observability"] != "not_observable"
        ]
        signatures = {
            r["v04_function_class"] or f"SINGLETON:{r['model_node']}"
            for r in observable
        }
        self.assertEqual(len(observable), 27)
        self.assertEqual(
            len(signatures),
            9,
            "the number of distinct v0.4 signatures spanned by observable states "
            "changed; docs/scrna_observability.md states nine and must be "
            "re-derived",
        )

    def test_only_a_free_variable_takes_a_prior_directly(self) -> None:
        """Derived nodes cannot be 'conditioned' without editing their rule."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = load_scrna_observation_map(ROOT)
        direct = sorted(
            r["model_node"]
            for r in rows
            if r["conditioning_compatibility"] == "istate_prior"
        )
        self.assertEqual(direct, ["E_KLF12_HIGH"])
        for row in rows:
            if row["conditioning_compatibility"] == "rule_override_required":
                with self.subTest(node=row["model_node"]):
                    self.assertNotEqual(row["evidence_class"], "hand_set_free")

    def test_abundance_is_never_recorded_as_activity(self) -> None:
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = {r["model_node"]: r for r in load_scrna_observation_map(ROOT)}
        for node in ("E_ITGAVB3_5", "E_CD98_CD9"):
            with self.subTest(node=node):
                self.assertEqual(
                    rows[node]["measurement_observability"],
                    "proxy_abundance_not_activity",
                )


class EvidenceRolesAreDecidedPerMeasurement(unittest.TestCase):
    """A measurement that BUILT the model can never be concordance for it.

    An earlier revision marked every observable row `same_dataset_internal`,
    including the scRNA detections of PRL, IGFBP1 and BMP2 -- which are
    construction-role records in `config/evidence_roles.yaml`. That is exactly
    the circularity AGENTS.md forbids.
    """

    def test_construction_features_force_the_construction_role(self) -> None:
        from dt_adoc.scrna.observability import (
            construction_features,
            load_scrna_observation_map,
        )

        built = construction_features(ROOT)
        for row in load_scrna_observation_map(ROOT):
            used = {
                f.strip() for f in row["measurement_features"].split(";") if f.strip()
            }
            if used & built:
                with self.subTest(node=row["model_node"]):
                    self.assertEqual(row["evidence_role"], "construction")


class ConstructionProvenanceCannotDriftSilently(unittest.TestCase):
    """The construction set must not be an independent duplicate list.

    Review finding: the module DESCRIBED these features as derived from
    `config/evidence_roles.yaml` and `context/phase1-readouts.tsv` while actually
    relying on a hand-written frozenset. If the canonical records moved, the map
    would keep a stale membership and every test would stay green.

    The repair is split, because the canonical records are only partly
    structured: `P1-EPI-STATE` and `P1-STR-STATE` carry parseable
    `multi_analyte_composite:` fields and are DERIVED; `P1-IHH-BMP` and
    `P1-SPP1` have no mapping row at all and say only "active in manuscript
    interpretation", so a two-symbol curated residue stands in for them under a
    fingerprint guard. These tests hold that split honest.
    """

    def test_the_derived_half_really_comes_from_the_canonical_records(self) -> None:
        """Not a copy: read the composites directly and compare."""
        import csv as _csv

        from dt_adoc.scrna.observability import derived_construction_features

        expected: set[str] = set()
        path = ROOT / "config" / "observation_model_map.tsv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in _csv.DictReader(handle, delimiter="\t"):
                protein = row["protein"]
                if row["registered_readout_id"] in {
                    "P1-EPI-STATE",
                    "P1-STR-STATE",
                } and protein.startswith("multi_analyte_composite:"):
                    for analyte in protein.split(":", 1)[1].split(";"):
                        name = analyte.strip()
                        if name:
                            expected.add("IGFBP1" if name == "IGFBP-1" else name)
        self.assertEqual(derived_construction_features(ROOT), frozenset(expected))
        self.assertIn("PAEP", expected)
        self.assertIn("IGFBP1", expected)

    def test_the_curated_residue_is_only_what_cannot_be_derived(self) -> None:
        """Two symbols, and neither is obtainable from a structured field."""
        from dt_adoc.scrna.observability import (
            CURATED_PATHWAY_CONSTRUCTION_FEATURES,
            derived_construction_features,
        )

        self.assertEqual(
            CURATED_PATHWAY_CONSTRUCTION_FEATURES, frozenset({"IHH", "NR2F2"})
        )
        self.assertFalse(
            CURATED_PATHWAY_CONSTRUCTION_FEATURES & derived_construction_features(ROOT),
            "a curated symbol is now derivable, so the residue should shrink",
        )

    def test_construction_status_is_not_broadened_beyond_the_composites(self) -> None:
        """The review's explicit warning, pinned.

        Secretoglobins are named in the manuscript and appear in
        E_SECRETORY_STATE's feature list, but are NOT in the registered
        P1-EPI-STATE composite. An earlier revision listed them as construction
        analytes anyway. Construction status must not widen just because an
        analyte appears somewhere in the same paper.
        """
        from dt_adoc.scrna.observability import construction_features

        built = construction_features(ROOT)
        for symbol in ("SCGB1D2", "SCGB2A1"):
            with self.subTest(symbol=symbol):
                self.assertNotIn(symbol, built)

    def test_a_change_to_the_canonical_records_trips_the_guard(self) -> None:
        """The fingerprint is pinned and recomputes from the live records."""
        from dt_adoc.scrna.observability import (
            CONSTRUCTION_SOURCE_FINGERPRINT,
            construction_source_fingerprint,
        )

        self.assertEqual(
            construction_source_fingerprint(ROOT),
            CONSTRUCTION_SOURCE_FINGERPRINT,
            "the canonical construction records changed; re-adjudicate the "
            "curated residue against the new records and then update the pin -- "
            "updating the pin alone defeats the guard",
        )

    def test_the_guard_covers_the_prose_the_curated_half_rests_on(self) -> None:
        """A change to the unstructured targets must also trip it.

        The curated residue was adjudicated from those readouts' prose, so the
        fingerprint has to cover the prose, not only the structured fields.
        """
        import shutil
        import tempfile

        from dt_adoc.scrna.observability import construction_source_fingerprint

        # The three records the fingerprint reads, mutated in a copy rather than
        # in the checkout.
        records = (
            Path("config/evidence_roles.yaml"),
            Path("config/observation_model_map.tsv"),
            Path("context/phase1-readouts.tsv"),
        )
        with tempfile.TemporaryDirectory() as raw:
            copy = Path(raw)
            for relative in records:
                (copy / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, copy / relative)
            baseline = construction_source_fingerprint(copy)
            self.assertEqual(
                baseline,
                construction_source_fingerprint(ROOT),
                "the copy does not hold every record the fingerprint reads",
            )
            readouts = copy / "context" / "phase1-readouts.tsv"
            original = readouts.read_text(encoding="utf-8")
            mutated = original.replace(
                "active in manuscript interpretation",
                "active in manuscript interpretation (reworded)",
                1,
            )
            self.assertNotEqual(original, mutated, "the prose under test moved")
            readouts.write_text(mutated, encoding="utf-8")
            self.assertNotEqual(construction_source_fingerprint(copy), baseline)

    def test_the_known_construction_nodes_are_labelled(self) -> None:
        """The specific rows the review named."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        rows = {r["model_node"]: r for r in load_scrna_observation_map(ROOT)}
        for node in ("S_PRL", "S_IGFBP1", "S_BMP2", "E_SECRETORY_STATE"):
            with self.subTest(node=node):
                self.assertEqual(rows[node]["evidence_role"], "construction")

    def test_not_every_observable_row_is_construction(self) -> None:
        """The role is decided per measurement, not applied wholesale."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        roles = {
            r["evidence_role"]
            for r in load_scrna_observation_map(ROOT)
            if r["measurement_observability"] != "not_observable"
        }
        self.assertEqual(roles, {"construction", "same_dataset_internal"})

    def test_no_row_claims_held_out_or_external_validation(self) -> None:
        """These cells are the study's own, so neither role is available."""
        from dt_adoc.scrna.observability import load_scrna_observation_map

        for row in load_scrna_observation_map(ROOT):
            with self.subTest(node=row["model_node"]):
                self.assertNotIn(row["evidence_role"], {"held_out", "external"})


class TheRdsVerifierIsSelfConsistent(unittest.TestCase):
    """The structural check is scripted, but never run against 2.9 GB here.

    AGENTS.md forbids loading the multi-gigabyte object merely to test runtime
    availability, so these check what needs no RDS: that the expectations agree
    with each other and with the manifest.
    """

    def test_sample_and_population_counts_both_total_the_cell_count(self) -> None:
        from dt_adoc.scrna.verify_rds import EXPECTED_CELLS, expectation_totals

        samples, populations = expectation_totals()
        self.assertEqual(samples, EXPECTED_CELLS)
        self.assertEqual(populations, EXPECTED_CELLS)

    def test_the_verifier_and_the_manifest_agree(self) -> None:
        from dt_adoc.scrna.verify_rds import ASSET_ID, manifest_row

        row = manifest_row(ROOT)
        self.assertEqual(row["asset_id"], ASSET_ID)
        self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
        self.assertGreater(int(row["size_bytes"]), 0)


if __name__ == "__main__":
    unittest.main()
