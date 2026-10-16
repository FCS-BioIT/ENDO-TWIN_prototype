from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
FIXTURES = ROOT / "tests" / "fixtures"
ENV = {**os.environ, "PYTHONPATH": str(SRC)}


def _run_python(snippet: str) -> dict[str, object]:
    command = [sys.executable, "-c", textwrap.dedent(snippet)]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=ENV,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"subprocess failed rc={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


class InitialStateFormsTest(unittest.TestCase):
    def test_cfg_bracket_istate_form_runs(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_bracket.cfg")!r},
                cmaboss=True,
            )
            res = sim.run()
            print(json.dumps(res.get_last_nodes_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertAlmostEqual(float(payload["A"]), 0.7, delta=0.05)
        self.assertAlmostEqual(float(payload["B"]), 0.4, delta=0.05)

    def test_cfg_deterministic_true_false_form_runs(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_deterministic.cfg")!r},
                cmaboss=True,
            )
            res = sim.run()
            print(json.dumps(res.get_last_nodes_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertAlmostEqual(float(payload["A"]), 1.0, delta=1e-6)
        self.assertAlmostEqual(float(payload["B"]), 0.0, delta=1e-6)

    def test_python_single_node_set_istate_runs(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            sim.network.set_istate("A", [0.25, 0.75])
            sim.network.set_istate("B", [0.9, 0.1])
            res = sim.run()
            print(json.dumps(res.get_last_nodes_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertAlmostEqual(float(payload["A"]), 0.75, delta=0.05)
        self.assertAlmostEqual(float(payload["B"]), 0.1, delta=0.05)

    def test_python_joint_set_istate_runs(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            sim.network.set_istate(["A", "B"], {{(0, 0): 0.5, (1, 1): 0.5}})
            res = sim.run()
            print(json.dumps(res.get_last_states_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertAlmostEqual(float(payload.get("<nil>", 0.0)), 0.5, delta=0.05)
        self.assertAlmostEqual(float(payload.get("A -- B", 0.0)), 0.5, delta=0.05)
        self.assertAlmostEqual(float(payload.get("A", 0.0)), 0.0, delta=0.02)
        self.assertAlmostEqual(float(payload.get("B", 0.0)), 0.0, delta=0.02)

    def test_runtime_capabilities_capture_classic_vs_cmaboss_continuation_api(
        self,
    ) -> None:
        payload = _run_python(
            """
            import json
            from dt_adoc.maboss_adapter import runtime_report
            print(json.dumps(runtime_report()))
            """
        )
        self.assertEqual(payload["installed"], "true")
        self.assertEqual(payload["cmaboss_available"], "true")
        self.assertEqual(payload["classic_continue_from_result_available"], "true")
        self.assertEqual(payload["cmaboss_continue_from_result_available"], "false")


class ContinuationModeTest(unittest.TestCase):
    def test_joint_continuation_preserves_correlated_support(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            from dt_adoc.maboss_adapter import apply_joint_distribution, project_joint_distribution
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            sim.network.set_istate(["A", "B"], {{(0, 0): 0.5, (1, 1): 0.5}})
            source = sim.run()
            projected = project_joint_distribution(
                last_states_probtraj=source.get_last_states_probtraj(),
                memory_nodes=("A", "B"),
                probability_cutoff=0.0,
            )
            sim2 = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            apply_joint_distribution(
                network=sim2.network,
                memory_nodes=("A", "B"),
                distribution=projected["distribution"],
            )
            result = sim2.run()
            print(json.dumps(result.get_last_states_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertAlmostEqual(float(payload.get("<nil>", 0.0)), 0.5, delta=0.05)
        self.assertAlmostEqual(float(payload.get("A -- B", 0.0)), 0.5, delta=0.05)
        self.assertAlmostEqual(float(payload.get("A", 0.0)), 0.0, delta=0.02)
        self.assertAlmostEqual(float(payload.get("B", 0.0)), 0.0, delta=0.02)

    def test_marginal_continuation_introduces_independent_mixed_states(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            from dt_adoc.maboss_adapter import apply_node_marginals_independent
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            sim.network.set_istate(["A", "B"], {{(0, 0): 0.5, (1, 1): 0.5}})
            source = sim.run()
            sim2 = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            apply_node_marginals_independent(network=sim2.network, result=source)
            result = sim2.run()
            print(json.dumps(result.get_last_states_probtraj().iloc[-1].to_dict()))
            """
        )
        self.assertGreater(float(payload.get("A", 0.0)), 0.15)
        self.assertGreater(float(payload.get("B", 0.0)), 0.15)
        self.assertAlmostEqual(float(payload.get("<nil>", 0.0)), 0.25, delta=0.07)
        self.assertAlmostEqual(float(payload.get("A -- B", 0.0)), 0.25, delta=0.07)

    def test_joint_projection_rejects_empty_support_after_cutoff(self) -> None:
        payload = _run_python(
            f"""
            import json
            import maboss
            from dt_adoc.maboss_adapter import project_joint_distribution
            sim = maboss.load(
                {str(FIXTURES / "identity_ab.bnd")!r},
                {str(FIXTURES / "identity_ab_base.cfg")!r},
                cmaboss=True,
            )
            sim.network.set_istate(["A", "B"], {{(0, 0): 0.5, (1, 1): 0.5}})
            source = sim.run()
            try:
                project_joint_distribution(
                    last_states_probtraj=source.get_last_states_probtraj(),
                    memory_nodes=("A", "B"),
                    probability_cutoff=0.6,
                )
            except ValueError as exc:
                print(json.dumps({{"error": str(exc)}}))
            else:
                print(json.dumps({{"error": None}}))
            """
        )
        self.assertIn("retained no probability mass", str(payload["error"]))


if __name__ == "__main__":
    unittest.main()
