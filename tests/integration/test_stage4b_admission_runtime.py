"""G13: admitting real direct interventions (Stage 4b), runtime half.

Gate G13 of ``docs/stage4b_direct_admission.md`` §7, executed through the
production runner, unpatched, against sandboxes built by
``tests/fixtures/o8_markerless/sandbox.py``. Every compound is synthetic
(``tests/fixtures/stage4b/admission.py``); nothing in the repository is edited.

- An approved **null** target licenses and executes, and the run records
  ``phenotype_claim_blocked`` (§5.6): the test that a structural null did not
  quietly become a refusal.
- A ``scope_relevant`` unrepresented target executes, and the run records
  ``compound_claim_blocked`` (§3.5, owner decision 4).
- **N+1**: adding a compound appends to four files -- the evidence register, the
  declarations, the ledger and the library -- and regenerates the two generated
  expressivity tables exactly as the committed generator writes them, while
  ``models/``, ``src/`` and ``config/node_entity_map.tsv`` stay byte-identical
  and compound N's run does not move.
- **Class agreement**: one member of each expressivity class, run bounded, moves
  the observed readouts the artefact says it moves and no others, within a
  tolerance registered below before the test was first run.

No result is interpreted. Where runs are compared it is to check the record or
the plumbing.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.perturbations.adjudication import ENTITY_MAP_PATH, EXPRESSIVITY_ARTEFACTS
from dt_adoc.perturbations.engine import InterventionError
from dt_adoc.reporting import veto_expressivity
from dt_adoc.simulation import runner


def _load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sandbox = _load("o8_sandbox", "tests/fixtures/o8_markerless/sandbox.py")
fixtures = _load("g13_fixtures", "tests/fixtures/stage4b/admission.py")
Compound = fixtures.Compound
V060 = fixtures.V060
CHALLENGE = "adhesion_challenge_hormone_treated"
SEED = 1
SAMPLE_COUNT = 500

# --- The class-agreement check, registered before it was first run ------------
#
# It compares a finite run with an asymptotic value (§7), so it tests agreement
# of *class* -- which observed readouts move, and in which direction -- never
# equality of a marginal.
#
# CLASS_TRAJECTORIES: 2000 trajectories per arm, one seed, from the baseline
# istates under the reference context's condition cfg, to the baseline cfg's
# max_time = 20.
# CLASS_TOLERANCE: 0.10 on the difference of a readout's final marginal between
# the arm and its matched unperturbed run (same cfg, same seed). Derivation: the
# Monte-Carlo standard error of a difference of two proportions at N = 2000 is at
# most sqrt(2 * 0.25 / 2000) = 0.0158, so 0.10 is more than six standard errors;
# and the smallest non-zero effect the artefact records on O in the reference
# context is 0.42 (class A2, adhesion), so 0.10 sits well below every effect the
# check must see. A readout the artefact says does not move must stay within
# 0.10; one it says moves must move by more than 0.10, in the artefact's
# direction. The value is not to be tuned against this check's own outcome: a
# failure is a finding about convergence or the classification.
CLASS_TRAJECTORIES = 2000
CLASS_TOLERANCE = 0.10
CLASS_SEED = 1
#: One member of each class of §5.3, with the declaration that admits it alone.
CLASS_MEMBERS = {
    "null": Compound(
        "g13_null_ihh", ("E_IHH",), ("IHH@expression",), declaration_id="DTD-910"
    ),
    "A1": Compound(
        "g13_a1_lif", ("E_LIF",), ("LIF@expression",), declaration_id="DTD-911"
    ),
    "A2": Compound(
        "g13_a2_spp1",
        ("X_SPP1_LUMEN_FREE",),
        ("SPP1@extracellular",),
        declaration_id="DTD-912",
    ),
    "A3": Compound(
        "g13_a3_spgr",
        ("S_PGR",),
        ("PGR@activity",),
        reached=("stroma", f"source:{fixtures.README}"),
        declaration_id="DTD-913",
    ),
    "A4": Compound(
        "g13_a4_epgr",
        ("E_PGR",),
        ("PGR@activity",),
        reached=("epithelium", f"source:{fixtures.README}"),
        declaration_id="DTD-914",
    ),
}


def _run_lineage(root: Path, interventions: tuple[str, ...] = ()):
    lineage = protocol_lineage(CHALLENGE, model_version=V060, root=root)
    results, continuation = [], None
    for index, protocol_id in enumerate(lineage):
        run = runner.run_protocol(
            protocol_id,
            model_version=V060,
            root=root,
            continuation=continuation,
            interventions=interventions,
            seed=SEED,
            sample_count=SAMPLE_COUNT,
        )
        results.extend(run.step_results)
        if index + 1 < len(lineage):
            continuation = runner.protocol_continuation(
                lineage[index + 1], run, model_version=V060, root=root
            )
    return results


def _outputs(result) -> dict[str, object]:
    return {
        "nodes_probtraj": result.nodes_probtraj.to_dict(),
        "last_nodes_probtraj": result.last_nodes_probtraj.to_dict(),
        "network_sha256": result.executed_network["network_sha256"],
    }


class _Sandboxes(unittest.TestCase):
    def sandbox(self, *compounds: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return sandbox.build_sandbox(Path(tmp.name), tuple(compounds))


class ClaimFlagTest(_Sandboxes):
    def test_an_approved_null_target_executes_with_phenotype_claim_blocked(
        self,
    ) -> None:
        root = self.sandbox()
        null = Compound("g13_null", ("E_HBEGF",), ("HBEGF@expression",))
        fixtures.add(sandbox, root, null)
        results = _run_lineage(root, ("g13_null",))
        self.assertTrue(results)
        record = results[-1].executed_network
        self.assertIn("E_HBEGF", record["intervention_overrides"])
        admission = record["direct_admission"]
        self.assertTrue(admission["phenotype_claim_blocked"])
        self.assertFalse(admission["compound_claim_blocked"])
        (effect,) = admission["effects"]
        self.assertEqual(effect["expressivity_class"], "null")
        self.assertTrue(effect["structurally_null_on_observed"])
        (intervention,) = admission["interventions"]
        self.assertEqual(intervention["declaration_id"], "DTD-900")
        self.assertEqual(intervention["expressivity_class"], "null")
        self.assertIn("g13_null", intervention["class_members"])
        for key in (
            "node_entity_map",
            "target_declarations",
            "expressivity_artefact",
            "expressivity_invariance",
        ):
            self.assertEqual(len(admission[key]["sha256"]), 64)

    def test_a_scope_relevant_target_executes_with_compound_claim_blocked(self) -> None:
        root = self.sandbox()
        stat3 = Compound(
            "g13_stat3",
            ("E_GP130_STAT3",),
            ("STAT3@activity",),
            unrepresented=f"STAT3@activity|scope_relevant|floor:S_STAT3|{fixtures.README}",
        )
        fixtures.add(sandbox, root, stat3)
        record = _run_lineage(root, ("g13_stat3",))[-1].executed_network
        self.assertIn("E_GP130_STAT3", record["intervention_overrides"])
        admission = record["direct_admission"]
        self.assertTrue(admission["compound_claim_blocked"])
        self.assertFalse(admission["phenotype_claim_blocked"])
        (intervention,) = admission["interventions"]
        self.assertEqual(
            intervention["unrepresented_known_targets"],
            [
                {
                    "entity": "STAT3@activity",
                    "class": "scope_relevant",
                    "floor": "floor:S_STAT3",
                    "basis": [fixtures.README],
                }
            ],
        )

    def test_an_out_of_scope_target_is_carried_into_the_claim_boundary(self) -> None:
        root = self.sandbox()
        fixtures.add(
            sandbox,
            root,
            Compound(
                "g13_cyp",
                ("E_GP130_STAT3",),
                ("LIFR@activity", "CYP3A4@activity"),
                unrepresented=f"CYP3A4@activity|out_of_scope|none|{fixtures.README}",
            ),
        )
        record = _run_lineage(root, ("g13_cyp",))[-1].executed_network
        admission = record["direct_admission"]
        self.assertFalse(admission["compound_claim_blocked"])
        self.assertEqual(
            admission["claim_boundary"]["out_of_scope_unrepresented_targets"],
            ["g13_cyp: CYP3A4@activity"],
        )

    def test_a_run_naming_no_direct_row_records_no_admission(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        self.assertIsNone(_run_lineage(root)[-1].executed_network["direct_admission"])
        migrated = _run_lineage(root, ("anti_spp1",))[-1].executed_network
        self.assertIsNone(migrated["direct_admission"])


def _n_plus_one_violations(
    before: dict[str, str],
    after: dict[str, str],
    old_bytes: dict[Path, bytes],
    root: Path,
) -> list[str]:
    """What an admission changed beyond the four appended files and the
    regenerated tables. Empty when the N+1 contract holds."""
    violations = []
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    appended = {str(p) for p in sandbox.COMPOUND_DATA}
    generated = {str(p) for p in sandbox.GENERATED}
    for path in sorted(changed - appended - generated):
        violations.append(f"{path} changed")
    for path in sandbox.COMPOUND_DATA:
        new = (root / path).read_bytes()
        if not new.startswith(old_bytes[path]) or new == old_bytes[path]:
            violations.append(f"{path} was not appended to")
    expected = {
        veto_expressivity.OUTPUT_PATH: veto_expressivity.render(
            veto_expressivity.expressivity(root=root)
        ),
        veto_expressivity.INVARIANCE_PATH: veto_expressivity.render_invariance(
            veto_expressivity.invariance(root=root)
        ),
    }
    for path, text in expected.items():
        if (root / path).read_text(encoding="utf-8") != text:
            violations.append(f"{path} is not what the generator writes")
    if str(ENTITY_MAP_PATH) in changed:
        violations.append(
            f"{ENTITY_MAP_PATH} is a reading of the model, not compound data"
        )
    return violations


class CompoundNPlusOneTest(_Sandboxes):
    """§7: N+1 under the Stage 4b contract.

    Starting from a sandbox holding compound X, adding compound Y step by step:
    evidence, then its declaration, then its approvals, then its rows. Until
    the rows exist Y is unknown and X's run does not move; afterwards Y runs.
    """

    def test_adding_compound_n_plus_one_is_a_four_file_append(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        code_before = sandbox.tree_digest(SRC)
        x_before = [_outputs(r) for r in _run_lineage(root, ("synthetic_compound_x",))]
        before = sandbox.tree_digest(root)
        old_bytes = {p: (root / p).read_bytes() for p in sandbox.COMPOUND_DATA}
        for part in ("evidence", "declaration", "adjudication"):
            sandbox.add_compound(root, "synthetic_compound_y", (part,))
            with self.subTest(after=part):
                with self.assertRaisesRegex(InterventionError, "unknown intervention"):
                    _run_lineage(root, ("synthetic_compound_y",))
                self.assertEqual(
                    [
                        _outputs(r)
                        for r in _run_lineage(root, ("synthetic_compound_x",))
                    ],
                    x_before,
                )
        sandbox.add_compound(root, "synthetic_compound_y", ("library",))
        after = sandbox.tree_digest(root)
        self.assertEqual(_n_plus_one_violations(before, after, old_bytes, root), [])
        # models/, src/ and the entity map, byte for byte.
        for path, digest in before.items():
            if path.startswith("models/") or path == str(ENTITY_MAP_PATH):
                self.assertEqual(after[path], digest, path)
        self.assertEqual(sandbox.tree_digest(SRC), code_before)
        record = _run_lineage(root, ("synthetic_compound_y",))[-1].executed_network
        self.assertEqual(
            {e["target_node"] for e in record["direct_admission"]["effects"]},
            {"E_HBEGF", "S_TAZ_ECM"},
        )
        # Adding N+1 cannot move compound N.
        self.assertEqual(
            [_outputs(r) for r in _run_lineage(root, ("synthetic_compound_x",))],
            x_before,
        )

    def test_an_admission_that_edits_the_entity_map_is_refused(self) -> None:
        """The one move that would let an admission clear its own C3 or C5
        refusal by re-reading what a node means (§3.2)."""
        root = self.sandbox("synthetic_compound_x")
        before = sandbox.tree_digest(root)
        old_bytes = {p: (root / p).read_bytes() for p in sandbox.COMPOUND_DATA}
        sandbox.add_compound(root, "synthetic_compound_y")
        path = root / ENTITY_MAP_PATH
        path.write_text(
            path.read_text(encoding="utf-8").replace("\tWWTR1\t", "\tTAZ\t"),
            encoding="utf-8",
        )
        violations = _n_plus_one_violations(
            before, sandbox.tree_digest(root), old_bytes, root
        )
        self.assertIn(
            f"{ENTITY_MAP_PATH} is a reading of the model, not compound data",
            violations,
        )
        # And the loader refuses the result too: Y's declaration now names an
        # entity no node carries.
        with self.assertRaisesRegex(InterventionError, r"\(C6\)|\(C7\)"):
            _run_lineage(root, ("synthetic_compound_y",))

    def test_a_hand_edited_artefact_is_not_a_regeneration(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        before = sandbox.tree_digest(root)
        old_bytes = {p: (root / p).read_bytes() for p in sandbox.COMPOUND_DATA}
        sandbox.add_compound(root, "synthetic_compound_y")
        path = root / EXPRESSIVITY_ARTEFACTS[V060][0]
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assertIn(
            f"{veto_expressivity.OUTPUT_PATH} is not what the generator writes",
            _n_plus_one_violations(before, sandbox.tree_digest(root), old_bytes, root),
        )


class ClassAgreementTest(unittest.TestCase):
    """§7: one member of each class, run bounded, agrees with the artefact's
    class on O. Registered constants are at the top of this module."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = sandbox.build_sandbox(Path(cls._tmp.name) / "root")
        for compound in CLASS_MEMBERS.values():
            fixtures.add(sandbox, cls.root, compound)
        cls.cfg = (
            cls.root
            / "models/superset"
            / V060
            / "conditions"
            / f"{veto_expressivity.REFERENCE_CONTEXT}.cfg"
        )
        with (cls.root / EXPRESSIVITY_ARTEFACTS[V060][0]).open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.artefact = {r["arm"]: r for r in csv.DictReader(handle, delimiter="\t")}
        cls.control = cls.simulate(())

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    @classmethod
    def simulate(cls, interventions: tuple[str, ...]) -> dict[str, float]:
        result = runner.run_cmaboss_condition(
            model_version=V060,
            condition_cfg=cls.cfg,
            root=cls.root,
            interventions=interventions,
            seed=CLASS_SEED,
            sample_count=CLASS_TRAJECTORIES,
        )
        return result.last

    def observed(self) -> tuple[str, ...]:
        nodes = set(self.control) | {veto_expressivity.ADHESION_ASSAY_NODE}
        return veto_expressivity._observed_sets(self.root, nodes)[0]

    def test_the_artefact_names_the_registered_classes(self) -> None:
        classes = {}
        for label, compound in CLASS_MEMBERS.items():
            (target,) = compound.targets
            classes[label] = self.artefact[target]["observed_class"]
        self.assertEqual(classes["null"], "null")
        self.assertEqual(len(set(classes.values())), 5)

    def test_each_class_moves_exactly_the_readouts_the_artefact_names(self) -> None:
        observed = self.observed()
        self.assertEqual(
            set(observed), {"E_PAEP", "S_IGFBP1", "S_PRL", "OUT_STABLE_ADHESION"}
        )
        for label, compound in CLASS_MEMBERS.items():
            (target,) = compound.targets
            expected = {
                node: float(value)
                for node, value in (
                    item.split(":")
                    for item in self.artefact[target][
                        "observed_effect_reference_context"
                    ].split(";")
                    if item
                )
            }
            arm = self.simulate((compound.name,))
            for node in observed:
                delta = arm[node] - self.control[node]
                with self.subTest(cls=label, target=target, node=node, delta=delta):
                    if node in expected:
                        self.assertGreater(abs(delta), CLASS_TOLERANCE)
                        self.assertEqual(delta > 0, expected[node] > 0)
                    else:
                        self.assertLessEqual(abs(delta), CLASS_TOLERANCE)


if __name__ == "__main__":
    unittest.main()
