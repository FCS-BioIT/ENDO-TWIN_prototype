"""Stage 2 of the intervention-layer refactor: the runner routes through the engine.

Gate G7 of ``docs/intervention_layer_refactor_plan.md``. Every v0.5.2 protocol
lineage, and every condition of the v0.5.2 condition suite as a single phase, is
run through the production runner twice, with ``INTERVENTION_ROUTING`` set to
``"engine"`` and to ``"legacy"``. The two must agree bit for bit on everything
the runner returns: the full node trajectories, the full last-state
distributions with their labels, and the merged cfg. Unlike G5 nothing is
projected out, because the engine route leaves every legacy input at the value
the protocol gives it.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import tomllib

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.concordance.simulate import protocol_lineage
from dt_adoc.maboss_adapter import (
    LOGIC_LINE_RE,
    NODE_BLOCK_RE,
    render_network_with_logic_overrides,
)
from dt_adoc.model.runtime import resolve_model
from dt_adoc.perturbations import engine
from dt_adoc.protocols.conditions import protocol_definitions
from dt_adoc.simulation import runner
from tests.unit.checkout_isolation import working_tree_copy

MODEL_VERSION = "adoc-literature-superset-v0.5.2"
MODEL_DIR = ROOT / "models/superset/adoc-literature-superset-v0.5.2"
SEEDS = (1, 2)
SAMPLE_COUNT = 500
LEGACY_INPUTS = ("IN_MIFEPRISTONE", "IN_ANTI_SPP1", "IN_HAND2_LOSS")


def _routing(value: str):
    return mock.patch.object(runner, "INTERVENTION_ROUTING", value)


def _run_lineage(
    final_protocol: str,
    seed: int,
    mode: str | None = None,
    interventions: dict[str, tuple[str, ...]] | None = None,
) -> list[runner.ConditionRunResult]:
    """The production chain: ``run_protocol`` per protocol, ``protocol_continuation``
    between them, as ``concordance.simulate.run_arm`` does.

    ``interventions`` names, per protocol of the lineage, library interventions
    active for that protocol's steps."""
    lineage = protocol_lineage(final_protocol, model_version=MODEL_VERSION, root=ROOT)
    results: list[runner.ConditionRunResult] = []
    continuation = None
    for index, protocol_id in enumerate(lineage):
        run = runner.run_protocol(
            protocol_id,
            model_version=MODEL_VERSION,
            root=ROOT,
            continuation=continuation,
            continuation_mode=mode,
            interventions=(interventions or {}).get(protocol_id, ()),
            seed=seed,
            sample_count=SAMPLE_COUNT,
        )
        results.extend(run.step_results)
        if index + 1 < len(lineage):
            continuation = runner.protocol_continuation(
                lineage[index + 1],
                run,
                model_version=MODEL_VERSION,
                root=ROOT,
                mode=mode,
            )
    return results


def _everything(result: runner.ConditionRunResult) -> dict[str, object]:
    return {
        "nodes_probtraj": result.nodes_probtraj.to_dict(),
        "last_states_probtraj": result.last_states_probtraj.to_dict(),
        "last_nodes_probtraj": result.last_nodes_probtraj.to_dict(),
        "merged_cfg": result.merged_cfg.read_text(encoding="utf-8"),
    }


def _projected(result: runner.ConditionRunResult) -> dict[str, object]:
    """Everything the run reports, with the ``IN_*`` nodes projected out.

    Needed when two routes reach the same biology through different input
    values: ``IN_HAND2_LOSS`` is not internal, so it appears in state labels."""
    traj = result.nodes_probtraj
    keep = [c for c in traj.columns if not str(c).startswith("IN_")]
    last_states = result.last_states_probtraj.iloc[-1]
    projected: dict[frozenset[str], float] = {}
    for label in sorted(last_states.index):
        active = frozenset(
            token.strip()
            for token in str(label).split(" -- ")
            if token.strip()
            and token.strip() != "<nil>"
            and not token.strip().startswith("IN_")
        )
        projected[active] = projected.get(active, 0.0) + float(last_states[label])
    return {
        "times": list(traj.index),
        "columns": keep,
        "trajectory": traj[keep].to_numpy().tolist(),
        "last": {k: v for k, v in result.last.items() if not k.startswith("IN_")},
        "last_states": {k: v for k, v in projected.items() if v != 0.0},
    }


def _suite_conditions() -> list[Path]:
    provenance = tomllib.loads(
        (MODEL_DIR / "provenance.toml").read_text(encoding="utf-8")
    )
    return [MODEL_DIR / path for path in provenance["condition_suite"]["conditions"]]


class InterventionRoutingRuntimeTest(unittest.TestCase):
    def test_every_protocol_lineage_is_bit_identical(self) -> None:
        protocols = sorted(protocol_definitions(ROOT, model_version=MODEL_VERSION))
        self.assertEqual(len(protocols), 15)
        for protocol_id in protocols:
            for seed in SEEDS:
                with self.subTest(protocol=protocol_id, seed=seed):
                    with _routing("legacy"):
                        legacy = _run_lineage(protocol_id, seed)
                    with _routing("engine"):
                        routed = _run_lineage(protocol_id, seed)
                    self.assertEqual(
                        [_everything(r) for r in legacy],
                        [_everything(r) for r in routed],
                    )

    def test_every_suite_condition_is_bit_identical_as_a_single_phase(self) -> None:
        conditions = _suite_conditions()
        self.assertEqual(len(conditions), 21)
        for condition in conditions:
            for seed in SEEDS:
                with self.subTest(condition=condition.name, seed=seed):
                    runs = {}
                    for routing in ("legacy", "engine"):
                        with _routing(routing):
                            runs[routing] = runner.run_cmaboss_condition(
                                model_version=MODEL_VERSION,
                                condition_cfg=condition,
                                root=ROOT,
                                seed=seed,
                                sample_count=SAMPLE_COUNT,
                            )
                    self.assertEqual(
                        _everything(runs["legacy"]), _everything(runs["engine"])
                    )

    def test_the_engine_route_really_renders_the_effect(self) -> None:
        """Bit identity alone would also hold if routing silently did nothing, so the
        network MaBoSS loads is captured: no rule reads a legacy input, and the
        mifepristone phase carries the veto on both PGR nodes."""
        loaded: list[str] = []
        real_load = runner.maboss.load

        def recording_load(network, cfg, **kwargs):
            loaded.append(Path(network).read_text(encoding="utf-8"))
            return real_load(network, cfg, **kwargs)

        with (
            _routing("engine"),
            mock.patch.object(runner.maboss, "load", recording_load),
        ):
            _run_lineage("hormone_treated_mifepristone", SEEDS[0])
        self.assertEqual(len(loaded), 4)
        for text in loaded:
            for match in NODE_BLOCK_RE.finditer(text):
                (logic,) = LOGIC_LINE_RE.findall(match.group(3))
                if match.group(2) not in LEGACY_INPUTS:
                    for name in LEGACY_INPUTS:
                        self.assertNotRegex(logic[1], rf"\b{name}\b", match.group(2))
        vetoed = loaded[3]
        self.assertIn("logic = (IN_PROGESTIN and not 0) and not 1;", vetoed)
        self.assertEqual(vetoed.count("and not 1;"), 2)
        self.assertNotIn("and not 1;", loaded[2])

    def test_each_run_records_and_then_removes_the_network_it_executed(self) -> None:
        """The record reconstructs the executed network exactly, and the temporary
        rendered file is gone once the run returns."""
        loaded: list[tuple[str, str]] = []
        real_load = runner.maboss.load

        def recording_load(network, cfg, **kwargs):
            loaded.append((str(network), Path(network).read_text(encoding="utf-8")))
            return real_load(network, cfg, **kwargs)

        with (
            _routing("engine"),
            mock.patch.object(runner.maboss, "load", recording_load),
        ):
            results = _run_lineage("hormone_treated_mifepristone", SEEDS[0])
        model_text = resolve_model(MODEL_VERSION, ROOT).network_bnd.read_text(
            encoding="utf-8"
        )
        library_sha = hashlib.sha256(
            (ROOT / engine.LIBRARY_PATH).read_bytes()
        ).hexdigest()
        self.assertEqual(len(results), len(loaded))
        for result, (path, text) in zip(results, loaded):
            record = result.executed_network
            self.assertTrue(record["rendered"])
            self.assertEqual(
                record["intervention_overrides"],
                ["E_PGR", "S_HAND2", "S_PGR", "X_SPP1_LUMEN_FREE"],
            )
            self.assertFalse(Path(path).exists(), path)
            self.assertEqual(record["intervention_routing"], "engine")
            self.assertEqual(record["intervention_library"]["sha256"], library_sha)
            self.assertEqual(
                record["source_network"]["path"],
                "models/superset/adoc-literature-superset-v0.5.2/network.bnd",
            )
            self.assertEqual(
                record["network_sha256"], hashlib.sha256(text.encode()).hexdigest()
            )
            rebuilt = render_network_with_logic_overrides(
                model_text, logic_overrides=record["logic_overrides"]
            )
            self.assertEqual(rebuilt, text)
        final_overrides = results[-1].executed_network["logic_overrides"]
        self.assertTrue(final_overrides["E_PGR"].endswith("and not 1"))

    def test_a_failed_run_still_removes_its_rendered_network(self) -> None:
        paths: list[str] = []

        def failing_load(network, cfg, **kwargs):
            paths.append(str(network))
            raise RuntimeError("simulated MaBoSS failure")

        condition = MODEL_DIR / "conditions/hormone_treated_mifepristone.cfg"
        with (
            _routing("engine"),
            mock.patch.object(runner.maboss, "load", failing_load),
            self.assertRaises(RuntimeError),
        ):
            runner.run_cmaboss_condition(
                model_version=MODEL_VERSION, condition_cfg=condition, root=ROOT, seed=1
            )
        self.assertEqual(len(paths), 1)
        self.assertNotEqual(
            paths[0], str(resolve_model(MODEL_VERSION, ROOT).network_bnd)
        )
        self.assertFalse(Path(paths[0]).exists())

    def test_the_legacy_route_records_the_unrendered_model(self) -> None:
        condition = MODEL_DIR / "conditions/hormone_treated_mifepristone.cfg"
        with _routing("legacy"):
            result = runner.run_cmaboss_condition(
                model_version=MODEL_VERSION,
                condition_cfg=condition,
                root=ROOT,
                seed=1,
                sample_count=50,
            )
        record = result.executed_network
        self.assertFalse(record["rendered"])
        self.assertEqual(record["logic_overrides"], {})
        self.assertEqual(record["intervention_overrides"], [])
        self.assertIsNone(record["intervention_library"])
        self.assertEqual(record["network_sha256"], record["source_network"]["sha256"])

    def test_the_smoke_manifest_records_every_executed_v052_network(self) -> None:
        """The run manifest, not only the in-memory record, carries the audit trail.

        The v0.5.2 default smoke list cannot run as declared. Its repaired
        perturbation challenges continue from maternal phases the list omits, and
        it fails on that before any routing code runs. So the production
        ``run_structural_smoke`` is run on the same list with those three
        maternal phases inserted ahead of the challenges that continue from them.
        """
        spec = resolve_model(MODEL_VERSION, ROOT)
        declared = list(spec.default_smoke_protocols)
        lineage: list[str] = []
        for protocol_id in declared:
            parent = protocol_definitions(ROOT, model_version=MODEL_VERSION)[
                protocol_id
            ].continuation_from
            if parent is not None and parent not in lineage:
                grandparent = protocol_definitions(ROOT, model_version=MODEL_VERSION)[
                    parent
                ].continuation_from
                self.assertIn(grandparent, lineage, parent)
                lineage.append(parent)
            lineage.append(protocol_id)
        self.assertEqual(
            sorted(set(lineage) - set(declared)),
            ["hormone_treated_anti_spp1", "hormone_treated_mifepristone", "washout"],
        )
        # The smoke writes under its root; run it on a copy, not the checkout.
        work = working_tree_copy(Path(self.enterContext(tempfile.TemporaryDirectory())))
        narrowed = dataclasses.replace(
            resolve_model(MODEL_VERSION, work), default_smoke_protocols=tuple(lineage)
        )
        with (
            _routing("engine"),
            mock.patch.object(runner, "resolve_model", return_value=narrowed),
        ):
            output_root = runner.run_structural_smoke(
                run_id="intervention-routing-manifest-fixture",
                model_version=MODEL_VERSION,
                root=work,
            )
        manifest = json.loads(
            (output_root / "run_manifest.json").read_text(encoding="utf-8")
        )
        rows = manifest["model"]["executed_networks"]
        stepped = []
        for protocol_id in lineage:
            protocol = protocol_definitions(ROOT, model_version=MODEL_VERSION)[
                protocol_id
            ]
            stepped.extend(protocol_id for _ in protocol.steps)
        self.assertEqual([row["protocol_id"] for row in rows], stepped)
        model_text = spec.network_bnd.read_text(encoding="utf-8")
        library_sha = hashlib.sha256(
            (ROOT / engine.LIBRARY_PATH).read_bytes()
        ).hexdigest()
        for row in rows:
            self.assertTrue(row["rendered"])
            self.assertEqual(row["intervention_routing"], "engine")
            self.assertEqual(
                row["intervention_library"],
                {
                    "path": "config/intervention_library.tsv",
                    "sha256": library_sha,
                    "size_bytes": (ROOT / engine.LIBRARY_PATH).stat().st_size,
                },
            )
            self.assertEqual(
                row["source_network"]["sha256"],
                manifest["model"]["network_bnd"]["sha256"],
            )
            rebuilt = render_network_with_logic_overrides(
                model_text, logic_overrides=row["logic_overrides"]
            )
            self.assertEqual(
                row["network_sha256"],
                hashlib.sha256(rebuilt.encode("utf-8")).hexdigest(),
            )
        vetoed = {
            row["protocol_id"]
            for row in rows
            if row["logic_overrides"]["E_PGR"].endswith("and not 1")
        }
        self.assertEqual(
            vetoed,
            {
                "hormone_treated_mifepristone",
                "adhesion_challenge_hormone_treated_mifepristone",
            },
        )

    def test_a_named_intervention_reproduces_the_declared_arm(self) -> None:
        """Gate G9. The HAND2-loss arm and the control arm have the same four
        phases with the same durations and cfgs, differing only by
        ``IN_HAND2_LOSS``. So naming ``hand2_loss`` on the control arm must
        reproduce the declared arm exactly, on everything that is not an input.

        This is the check that the named path and the marker path are one
        mechanism rather than two that happen to agree.
        """
        maternal = "hormone_treated_hand2_loss"
        challenge = "adhesion_challenge_hormone_treated_hand2_loss"
        for seed in SEEDS:
            with self.subTest(seed=seed):
                with _routing("engine"):
                    declared = _run_lineage(challenge, seed)
                    named = _run_lineage(
                        "adhesion_challenge_hormone_treated",
                        seed,
                        interventions={
                            "hormone_treated_maternal": ("hand2_loss",),
                            "adhesion_challenge_hormone_treated": ("hand2_loss",),
                        },
                    )
                self.assertEqual(len(declared), len(named))
                self.assertEqual(
                    [_projected(r) for r in declared], [_projected(r) for r in named]
                )
                # The marker route still records no named intervention, so the
                # two are distinguishable in provenance even though they agree.
                self.assertEqual(
                    declared[-1].executed_network["named_interventions"], []
                )
                self.assertEqual(
                    named[-1].executed_network["named_interventions"], ["hand2_loss"]
                )
                self.assertEqual(
                    protocol_lineage(maternal, model_version=MODEL_VERSION, root=ROOT)[
                        -1
                    ],
                    maternal,
                )

    def test_a_named_intervention_is_not_a_no_op(self) -> None:
        """The agreement above would be vacuous if naming one changed nothing."""
        with _routing("engine"):
            control = _run_lineage("adhesion_challenge_hormone_treated", SEEDS[0])
            named = _run_lineage(
                "adhesion_challenge_hormone_treated",
                SEEDS[0],
                interventions={"adhesion_challenge_hormone_treated": ("hand2_loss",)},
            )
        self.assertNotEqual(_projected(control[-1]), _projected(named[-1]))

    def test_a_combination_vetoes_the_union_and_runs(self) -> None:
        """A combination is executable and is the union of its members' effects.

        Only the rendering is asserted. What a combination predicts is a result,
        and producing one is a separate unit with its own pre-registration.
        """
        pair = ("mifepristone", "anti_spp1")
        with _routing("engine"):
            results = _run_lineage(
                "adhesion_challenge_hormone_treated",
                SEEDS[0],
                interventions={"adhesion_challenge_hormone_treated": pair},
            )
            singles = {
                member: _run_lineage(
                    "adhesion_challenge_hormone_treated",
                    SEEDS[0],
                    interventions={"adhesion_challenge_hormone_treated": (member,)},
                )[-1]
                for member in pair
            }
        combined = results[-1].executed_network
        self.assertEqual(combined["named_interventions"], list(pair))
        vetoed = {
            node
            for node, logic in combined["logic_overrides"].items()
            if logic.endswith("and not 1")
        }
        union: set[str] = set()
        for single in singles.values():
            union |= {
                node
                for node, logic in single.executed_network["logic_overrides"].items()
                if logic.endswith("and not 1")
            }
        self.assertEqual(vetoed, union)
        self.assertEqual(vetoed, {"E_PGR", "S_PGR", "X_SPP1_LUMEN_FREE"})

    def test_naming_an_already_active_intervention_is_refused(self) -> None:
        """Applying one twice is meaningless here and is refused, not absorbed."""
        with (
            _routing("engine"),
            self.assertRaisesRegex(engine.InterventionError, "twice"),
        ):
            _run_lineage(
                "adhesion_challenge_hormone_treated_hand2_loss",
                SEEDS[0],
                interventions={
                    "adhesion_challenge_hormone_treated_hand2_loss": ("hand2_loss",)
                },
            )

    def test_a_refused_run_leaves_no_merged_cfg_behind(self) -> None:
        """A rejected combination is an ordinary outcome for a screen, so it must
        not leave a temporary directory per rejection. A successful run keeps
        its merged cfg, because the result hands the path back."""
        allocated: list[Path] = []
        real_build = runner.build_condition_cfg

        def recording_build(**kwargs):
            path = real_build(**kwargs)
            allocated.append(path)
            return path

        condition = MODEL_DIR / "conditions/hormone_treated_hand2_loss.cfg"
        with (
            _routing("engine"),
            mock.patch.object(runner, "build_condition_cfg", recording_build),
        ):
            with self.assertRaises(engine.InterventionError):
                runner.run_cmaboss_condition(
                    model_version=MODEL_VERSION,
                    condition_cfg=condition,
                    root=ROOT,
                    interventions=("hand2_loss",),
                    seed=1,
                    sample_count=50,
                )
            self.assertEqual(len(allocated), 1)
            self.assertFalse(allocated[0].parent.exists(), allocated[0])

            kept = runner.run_cmaboss_condition(
                model_version=MODEL_VERSION,
                condition_cfg=condition,
                root=ROOT,
                seed=1,
                sample_count=50,
            )
        self.assertEqual(len(allocated), 2)
        self.assertTrue(allocated[1].exists())
        self.assertEqual(kept.merged_cfg, allocated[1])

    def test_naming_an_intervention_under_legacy_routing_is_refused(self) -> None:
        with _routing("legacy"), self.assertRaises(engine.InterventionError):
            _run_lineage(
                "adhesion_challenge_hormone_treated",
                SEEDS[0],
                interventions={"adhesion_challenge_hormone_treated": ("hand2_loss",)},
            )

    def test_an_inert_member_leaves_a_combination_unchanged(self) -> None:
        with _routing("engine"):
            alone = _run_lineage(
                "adhesion_challenge_hormone_treated",
                SEEDS[0],
                interventions={"adhesion_challenge_hormone_treated": ("anti_spp1",)},
            )
            with_inert = _run_lineage(
                "adhesion_challenge_hormone_treated",
                SEEDS[0],
                interventions={
                    "adhesion_challenge_hormone_treated": ("anti_spp1", "xav939")
                },
            )
        self.assertEqual(_projected(alone[-1]), _projected(with_inert[-1]))

    def test_the_legacy_route_still_reads_the_model_file(self) -> None:
        loaded: list[str] = []
        real_load = runner.maboss.load

        def recording_load(network, cfg, **kwargs):
            loaded.append(str(network))
            return real_load(network, cfg, **kwargs)

        with (
            _routing("legacy"),
            mock.patch.object(runner.maboss, "load", recording_load),
        ):
            _run_lineage("basal_maternal", SEEDS[0])
        self.assertEqual(loaded, [str(resolve_model(MODEL_VERSION, ROOT).network_bnd)])

    def test_a_rendering_without_the_veto_is_refused(self) -> None:
        """Power: with the veto removed the engine's own exhaustive check refuses to
        render the mifepristone phase rather than running a different model."""
        with (
            _routing("engine"),
            mock.patch.object(engine, "activity_veto_logic", lambda logic: logic),
            self.assertRaises(engine.InterventionError),
        ):
            _run_lineage("hormone_treated_mifepristone", SEEDS[0])

    def test_models_the_library_does_not_cover_are_untouched(self) -> None:
        loaded: list[str] = []
        real_load = runner.maboss.load

        def recording_load(network, cfg, **kwargs):
            loaded.append(str(network))
            return real_load(network, cfg, **kwargs)

        version = "adoc-literature-superset-v0.5.1"
        spec = resolve_model(version, ROOT)
        with (
            _routing("engine"),
            mock.patch.object(runner.maboss, "load", recording_load),
        ):
            runner.run_cmaboss_condition(
                model_version=version,
                condition_cfg=spec.model_root
                / "conditions/hormone_treated_mifepristone.cfg",
                root=ROOT,
                seed=1,
                sample_count=50,
            )
        self.assertEqual(loaded, [str(spec.network_bnd)])


if __name__ == "__main__":
    unittest.main()
