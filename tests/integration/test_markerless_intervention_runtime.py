"""O8: a markerless intervention runs through the production path.

Gate G10 of ``docs/o8_markerless_interventions.md``. Every run here goes through
the production ``run_protocol``, unpatched, against a sandbox repository built by
``tests/fixtures/o8_markerless/sandbox.py``: a copy of ``models/``, ``config/``
and the evidence register, with synthetic compounds appended to the sandbox's
library and register. Nothing in the repository is edited.

The central check is the N+1 invariant: adding a compound appends to four data
files (evidence register, target declarations, effect-adjudication ledger,
library), regenerates the two Stage 4b expressivity tables with the committed
generator, and changes nothing else a run reads. Since O8b a library row alone
is refused (``docs/o8b_direct_effect_governance.md`` §9); Stage 4b adds the
declaration and keeps ``config/node_entity_map.tsv`` byte-identical
(``docs/stage4b_direct_admission.md`` §3.2, §7).

The compounds run on v0.6.0: since Stage 4b a direct row needs an entity map and
an expressivity artefact for its version, and only v0.6.0 has them. v0.6.0 has
no legacy markers, so a direct row's partner in a combination is a migrated row.

No result is interpreted. Where a run is compared with another it is to show the
plumbing is one mechanism, or that naming a compound is not a no-op.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.maboss_adapter import NODE_BLOCK_RE, render_network_with_logic_overrides
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations.adjudication import (
    ADJUDICATIONS_PATH,
    ENTITY_MAP_PATH,
    TARGET_POLICY_PATH,
)
from dt_adoc.perturbations.engine import (
    DIRECT_BASIS,
    MIGRATED_BASIS,
    InterventionError,
)
from dt_adoc.protocols.conditions import get_protocol
from dt_adoc.reporting import veto_expressivity
from dt_adoc.simulation import runner

_spec = importlib.util.spec_from_file_location(
    "o8_sandbox", ROOT / "tests/fixtures/o8_markerless/sandbox.py"
)
sandbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sandbox)

MODEL_VERSION = sandbox.MODEL_VERSION
#: The marker version the cleanup test needs: it sets a legacy marker.
V052 = "adoc-literature-superset-v0.5.2"
CHALLENGE = "adhesion_challenge_hormone_treated"
SEEDS = (1, 2)
SAMPLE_COUNT = 500


def _run_lineage(
    root: Path, seed: int, interventions: tuple[str, ...] = ()
) -> list[runner.ConditionRunResult]:
    """The production chain, with ``interventions`` named on every protocol."""
    lineage = protocol_lineage(CHALLENGE, model_version=MODEL_VERSION, root=root)
    results: list[runner.ConditionRunResult] = []
    continuation = None
    for index, protocol_id in enumerate(lineage):
        run = runner.run_protocol(
            protocol_id,
            model_version=MODEL_VERSION,
            root=root,
            continuation=continuation,
            interventions=interventions,
            seed=seed,
            sample_count=SAMPLE_COUNT,
        )
        results.extend(run.step_results)
        if index + 1 < len(lineage):
            continuation = runner.protocol_continuation(
                lineage[index + 1], run, model_version=MODEL_VERSION, root=root
            )
    return results


def _outputs(result: runner.ConditionRunResult) -> dict[str, object]:
    """Everything a run returns except the path of its temporary cfg."""
    return {
        "nodes_probtraj": result.nodes_probtraj.to_dict(),
        "last_states_probtraj": result.last_states_probtraj.to_dict(),
        "last_nodes_probtraj": result.last_nodes_probtraj.to_dict(),
        "merged_cfg": result.merged_cfg.read_text(encoding="utf-8"),
        "network_sha256": result.executed_network["network_sha256"],
    }


def _nodes(network_text: str) -> list[str]:
    return [match.group(2) for match in NODE_BLOCK_RE.finditer(network_text)]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class _Sandboxes(unittest.TestCase):
    def sandbox(self, *compounds: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return sandbox.build_sandbox(Path(tmp.name), tuple(compounds))


class MarkerlessExecutionTest(_Sandboxes):
    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )

    def test_the_sandbox_runs_the_repository_bit_for_bit(self) -> None:
        """Without a named compound, a sandbox with one in its library runs the
        lineage exactly as the repository does, so the sandbox itself distorts
        nothing the gates below compare."""
        root = self.sandbox("synthetic_compound_x")
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.assertEqual(
                    [_outputs(r) for r in _run_lineage(root, seed)],
                    [_outputs(r) for r in _run_lineage(ROOT, seed)],
                )

    def test_a_markerless_compound_executes_and_records_its_licence(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        results = _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))
        self.assertTrue(results)
        for result in results:
            record = result.executed_network
            with self.subTest(step=len(results)):
                self.assertEqual(record["intervention_routing"], "engine")
                self.assertEqual(
                    record["named_interventions"], ["synthetic_compound_x"]
                )
                (effect,) = record["named_intervention_effects"]
                self.assertEqual(effect["mapping_basis"], DIRECT_BASIS)
                self.assertEqual(effect["legacy_input_node"], "")
                self.assertEqual(effect["target_node"], "E_GP130_STAT3")
                self.assertEqual(effect["mode"], "activity_veto")
                self.assertEqual(effect["evidence_ids"], ["SYNTHETIC-O8-X"])
                # Why it was licensed (O8b): the approval, bound to this row.
                self.assertEqual(effect["model_version"], MODEL_VERSION)
                self.assertEqual(effect["adjudication_id"], "SYN-X-1")
                self.assertEqual(len(effect["adjudication_sha256"]), 64)
                self.assertEqual(
                    effect["library_row_sha256"],
                    (
                        root
                        / sandbox.FIXTURE_RELATIVE
                        / "synthetic_compound_x.adjudication.tsv"
                    )
                    .read_text(encoding="utf-8")
                    .split("\t")[10],
                )
                for key, path in (
                    ("direct_effect_adjudications", ADJUDICATIONS_PATH),
                    ("direct_effect_target_policy", TARGET_POLICY_PATH),
                ):
                    self.assertEqual(
                        record[key],
                        {
                            "path": str(path),
                            "sha256": _sha(root / path),
                            "size_bytes": (root / path).stat().st_size,
                        },
                    )
                self.assertEqual(
                    record["intervention_library"]["sha256"],
                    _sha(root / sandbox.LIBRARY),
                )
                # Which declaration the admission rests on (Stage 4b, §6.5).
                (admitted,) = record["direct_admission"]["interventions"]
                self.assertEqual(admitted["declaration_id"], "DTD-001")
                self.assertEqual(
                    record["evidence_register"],
                    {
                        "path": str(sandbox.REGISTER),
                        "sha256": _sha(root / sandbox.REGISTER),
                        "size_bytes": (root / sandbox.REGISTER).stat().st_size,
                    },
                )
                # The canonical network is the source: no model file changed.
                self.assertEqual(
                    record["source_network"]["sha256"],
                    hashlib.sha256(self.canonical_text.encode("utf-8")).hexdigest(),
                )
                self.assertIn("E_GP130_STAT3", record["intervention_overrides"])
                logic = record["logic_overrides"]["E_GP130_STAT3"]
                self.assertEqual(logic, "(E_LIF) and not 1")
                # Reconstructible from the record alone.
                rebuilt = render_network_with_logic_overrides(
                    self.canonical_text, logic_overrides=record["logic_overrides"]
                )
                self.assertEqual(
                    hashlib.sha256(rebuilt.encode("utf-8")).hexdigest(),
                    record["network_sha256"],
                )
                # No node was created: the executed network has the canonical
                # node list, and no node is named after the compound.
                self.assertEqual(_nodes(rebuilt), _nodes(self.canonical_text))
                self.assertFalse(
                    [n for n in _nodes(rebuilt) if "SYNTHETIC" in n.upper()]
                )
                self.assertFalse(
                    [n for n in result.last if "SYNTHETIC" in str(n).upper()]
                )

    def test_the_migrated_record_names_its_basis_too(self) -> None:
        """Before Stage 4b the partner was a legacy row on v0.5.2; a direct row
        can no longer run there, so on v0.6.0 it is the migrated one."""
        root = self.sandbox("synthetic_compound_x")
        (result,) = _run_lineage(root, SEEDS[0], ("synthetic_compound_x", "anti_spp1"))[
            -1:
        ]
        bases = {
            e["intervention_id"]: e["mapping_basis"]
            for e in result.executed_network["named_intervention_effects"]
        }
        self.assertEqual(
            bases, {"synthetic_compound_x": DIRECT_BASIS, "anti_spp1": MIGRATED_BASIS}
        )
        unnamed = _run_lineage(root, SEEDS[0])[-1].executed_network
        self.assertEqual(unnamed["named_intervention_effects"], [])
        self.assertIsNone(unnamed["evidence_register"])
        self.assertIsNone(unnamed["direct_effect_adjudications"])
        self.assertIsNone(unnamed["direct_effect_target_policy"])
        self.assertIsNone(unnamed["direct_admission"])
        migrated_only = _run_lineage(root, SEEDS[0], ("anti_spp1",))[
            -1
        ].executed_network
        self.assertIsNone(migrated_only["direct_effect_adjudications"])
        self.assertIsNone(migrated_only["direct_admission"])
        (record,) = migrated_only["named_intervention_effects"]
        self.assertNotIn("adjudication_id", record)

    def test_two_approvals_of_one_row_are_distinguishable(self) -> None:
        """The same row under two approvals that differ only in rationale runs the
        same network and leaves different records."""
        records = []
        for rationale in ("first reading", "second reading"):
            root = self.sandbox("synthetic_compound_x")
            path = root / ADJUDICATIONS_PATH
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace("Synthetic approval so that", f"{rationale}: so that"),
                encoding="utf-8",
            )
            records.append(
                _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))[
                    -1
                ].executed_network
            )
        first, second = records
        self.assertEqual(first["network_sha256"], second["network_sha256"])
        self.assertNotEqual(
            first["named_intervention_effects"][0]["adjudication_sha256"],
            second["named_intervention_effects"][0]["adjudication_sha256"],
        )
        self.assertNotEqual(
            first["direct_effect_adjudications"]["sha256"],
            second["direct_effect_adjudications"]["sha256"],
        )

    def test_naming_it_is_not_a_no_op(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        control = _run_lineage(root, SEEDS[0])[-1]
        named = _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))[-1]
        self.assertNotEqual(_outputs(control), _outputs(named))
        self.assertLess(named.last["E_GP130_STAT3"], control.last["E_GP130_STAT3"])

    def test_it_composes_with_migrated_and_direct_compounds(self) -> None:
        root = self.sandbox("synthetic_compound_x", "synthetic_compound_y")
        trio = ("synthetic_compound_x", "synthetic_compound_y", "mifepristone")
        record = _run_lineage(root, SEEDS[0], trio)[-1].executed_network
        vetoed = {
            node
            for node, logic in record["logic_overrides"].items()
            if logic.endswith("and not 1")
        }
        self.assertEqual(
            vetoed, {"E_GP130_STAT3", "E_HBEGF", "S_TAZ_ECM", "E_PGR", "S_PGR"}
        )
        for logic in record["logic_overrides"].values():
            self.assertLessEqual(logic.count("and not 1"), 1)

    def test_removing_the_row_makes_it_unavailable(self) -> None:
        root = self.sandbox()
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            _run_lineage(ROOT, SEEDS[0], ("synthetic_compound_x",))


class CompoundNPlusOneTest(_Sandboxes):
    """The scalability invariant, executed, under the O8b contract.

    Starting from a sandbox that holds compound X, adding compound Y must:

    - be refused before its data exist;
    - stay refused with Y's evidence alone;
    - license nothing with Y's declaration but no library row, and leave X's run
      bit-identical;
    - license nothing with Y's approval but no library row, and leave X's run
      bit-identical;
    - refuse Y's library rows without an approval (a separate sandbox, since a
      refused row refuses the library);
    - run once evidence, declaration, approval and rows are all appended;
    - append to exactly four files, the register, the declarations, the ledger
      and the library, each only by appending rows; and regenerate the two
      expressivity tables to exactly what the committed generator writes, which
      is the only other change;
    - leave every model file and ``config/node_entity_map.tsv`` byte-identical
      to the repository's, and leave the code that runs untouched;
    - leave X's run bit-identical, so adding N+1 cannot move compound N.
    """

    def test_adding_compound_n_plus_one_is_a_data_append(self) -> None:
        root = self.sandbox("synthetic_compound_x")
        code_before = sandbox.tree_digest(SRC)
        x_before = [
            _outputs(r) for r in _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))
        ]
        # 1. Before its data exist.
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            _run_lineage(root, SEEDS[0], ("synthetic_compound_y",))

        before = sandbox.tree_digest(root)
        old_bytes = {path: (root / path).read_bytes() for path in sandbox.COMPOUND_DATA}
        # 2. Evidence alone is not enough.
        sandbox.add_compound(root, "synthetic_compound_y", ("evidence",))
        with self.assertRaisesRegex(InterventionError, "unknown intervention"):
            _run_lineage(root, SEEDS[0], ("synthetic_compound_y",))
        # 3. A declaration without rows licenses nothing and moves nothing.
        # 4. Nor does an approval without a matching row.
        for part in ("declaration", "adjudication"):
            sandbox.add_compound(root, "synthetic_compound_y", (part,))
            with self.subTest(part=part):
                with self.assertRaisesRegex(InterventionError, "unknown intervention"):
                    _run_lineage(root, SEEDS[0], ("synthetic_compound_y",))
                self.assertEqual(
                    [
                        _outputs(r)
                        for r in _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))
                    ],
                    x_before,
                )
        # 5. The rows complete it.
        sandbox.add_compound(root, "synthetic_compound_y", ("library",))
        after = sandbox.tree_digest(root)

        # 6. The four files changed by appending, and the expressivity tables
        # by regeneration only; models/, src/ and the entity map did not.
        changed = {
            path
            for path in before.keys() | after.keys()
            if before.get(path) != after.get(path)
        }
        appended = {str(path) for path in sandbox.COMPOUND_DATA}
        self.assertEqual(changed - appended, {str(p) for p in sandbox.GENERATED})
        self.assertLessEqual(appended, changed)
        for path in sandbox.COMPOUND_DATA:
            self.assertTrue(
                (root / path).read_bytes().startswith(old_bytes[path]), path
            )
        self.assertEqual(
            (root / veto_expressivity.OUTPUT_PATH).read_text(encoding="utf-8"),
            veto_expressivity.render(veto_expressivity.expressivity(root=root)),
        )
        self.assertEqual(
            (root / veto_expressivity.INVARIANCE_PATH).read_text(encoding="utf-8"),
            veto_expressivity.render_invariance(
                veto_expressivity.invariance(root=root)
            ),
        )
        self.assertEqual(
            {p: h for p, h in after.items() if p.startswith("models/")},
            {f"models/{p}": h for p, h in sandbox.tree_digest(ROOT / "models").items()},
        )
        self.assertEqual(
            (root / ENTITY_MAP_PATH).read_bytes(), (ROOT / ENTITY_MAP_PATH).read_bytes()
        )

        y = _run_lineage(root, SEEDS[0], ("synthetic_compound_y",))[-1]
        vetoed = {
            node
            for node, logic in y.executed_network["logic_overrides"].items()
            if logic.endswith("and not 1")
        }
        self.assertEqual(vetoed, {"E_HBEGF", "S_TAZ_ECM"})
        self.assertEqual(
            {
                e["target_node"]: e["adjudication_id"]
                for e in y.executed_network["named_intervention_effects"]
            },
            {"E_HBEGF": "SYN-Y-1", "S_TAZ_ECM": "SYN-Y-2"},
        )
        self.assertEqual(
            _nodes(
                render_network_with_logic_overrides(
                    (
                        root / "models/superset" / MODEL_VERSION / "network.bnd"
                    ).read_text(encoding="utf-8"),
                    logic_overrides=y.executed_network["logic_overrides"],
                )
            ),
            _nodes(
                (ROOT / "models/superset" / MODEL_VERSION / "network.bnd").read_text(
                    encoding="utf-8"
                )
            ),
        )
        # 7. X is bit-identical before and after.
        x_after = [
            _outputs(r) for r in _run_lineage(root, SEEDS[0], ("synthetic_compound_x",))
        ]
        self.assertEqual(x_after, x_before)
        self.assertEqual(sandbox.tree_digest(SRC), code_before)

    def test_library_rows_without_an_approval_are_refused(self) -> None:
        """3. Evidence, declaration and rows, no approval: refused, for Y and for
        the library."""
        root = self.sandbox("synthetic_compound_x")
        sandbox.add_compound(
            root, "synthetic_compound_y", ("evidence", "declaration", "library")
        )
        for name in ("synthetic_compound_y", "synthetic_compound_x"):
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(InterventionError, "no adjudication"),
            ):
                _run_lineage(root, SEEDS[0], (name,))


class ProtocolCleanupTest(_Sandboxes):
    """A refused later step must not orphan the earlier steps' merged cfgs.

    No committed protocol has more than one step, so the two-step protocol is
    built from a real one: the second step is the first with ``IN_HAND2_LOSS``
    set, so naming ``hand2_loss`` runs step one and is refused at step two. It
    needs a legacy marker and no direct row, so it stays on v0.5.2.
    """

    def test_a_refused_later_step_removes_the_earlier_steps_cfgs(self) -> None:
        real = get_protocol("hormone_treated_maternal", ROOT, model_version=V052)
        (step,) = real.steps
        second = dataclasses.replace(
            step,
            step_id=f"{step.step_id}_second",
            relative_order=step.relative_order + 1,
            input_states={**step.input_states, "IN_HAND2_LOSS": True},
        )
        two_step = dataclasses.replace(real, steps=(step, second))
        allocated: list[Path] = []
        real_build = runner.build_condition_cfg

        def recording_build(**kwargs):
            path = real_build(**kwargs)
            allocated.append(path)
            return path

        with (
            mock.patch.object(runner, "get_protocol", return_value=two_step),
            mock.patch.object(runner, "build_condition_cfg", recording_build),
            self.assertRaisesRegex(InterventionError, "twice"),
        ):
            runner.run_protocol(
                "hormone_treated_maternal",
                model_version=V052,
                root=ROOT,
                interventions=("hand2_loss",),
                seed=1,
                sample_count=50,
            )
        self.assertEqual(len(allocated), 2)
        for path in allocated:
            self.assertFalse(path.parent.exists(), path)


if __name__ == "__main__":
    unittest.main()
