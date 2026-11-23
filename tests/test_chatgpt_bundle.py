from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]


class ChatGPTBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "scripts").mkdir(parents=True)
        (self.root / "tests").mkdir()
        shutil.copy(
            ROOT / "scripts/make_chatgpt_results_bundle.sh",
            self.root / "scripts/make_chatgpt_results_bundle.sh",
        )
        shutil.copy(
            ROOT / "scripts/validate_chatgpt_bundle.py",
            self.root / "scripts/validate_chatgpt_bundle.py",
        )
        shutil.copy(
            ROOT / "scripts/export_protein_readout_tables.py",
            self.root / "scripts/export_protein_readout_tables.py",
        )
        for path, content in {
            "README.md": "# Synthetic DT_ADOC\n",
            "docs/legacy/IMPLEMENTATION_PLAN.md": "# Plan\n",
            "docs/legacy/IMPLEMENTATION_STATUS.md": "# Status\n",
            "docs/legacy/REQUIREMENTS_COVERAGE.tsv": "requirement_id\tstatus\nREQ-001\tpassed\n",
            "THIRD_PARTY_NOTICES.md": "# Notices\n",
            "pixi.toml": '[workspace]\nname = "synthetic"\n',
            "pixi.lock": "version: 6\n",
            ".gitignore": "output/\n",
            "data/README.md": "# Data contract\n",
            "data/private.rds": "must not be bundled\n",
            "src/run.py": "print('model')\n",
            "docs/method.md": "# Method\n",
            "context/context.md": "# Context\n",
            "context/literature/README.md": "# Literature\n",
            "context/literature/knowledge-base.yaml": "schema_version: '1.0'\n",
            "context/upstream/upstream_versions.yaml": 'schema_version: "1.0"\n',
            "models/model.bnd": "node A { logic = A; }\n",
            "models/model.cfg": "sample_count = 10;\n",
            "output/results/run-1/table.tsv": "phenotype\tprobability\nA\t0.5\n",
            "output/results/run-1/raw/probtraj.csv": "time,A\n0,0.5\n",
            "output/smoke/phase1-run-1/run_manifest.json": '{\n  "run_id": "phase1-run-1"\n}\n',
            "output/smoke/phase1-run-1/report/smoke_report.md": "# Smoke\n",
            "output/smoke/phase1-run-1/tables/phenotype_probabilities.tsv": "protocol_id\tOUT_STABLE_ADHESION\nht\t0.4\n",
            "output/results/run-1/plot.pdf": "must not be bundled\n",
            "output/results/run-1/checkpoints/partial.tsv": "must not be bundled\n",
            "output/results/run-1/report.xlsx": "must not be bundled\n",
            "docs/assets/adoc_maboss_pathway_dynamics.gif": "GIF89a-fake-bytes\n",
            "docs/assets/adoc_maboss_pathway_dynamics_preview.png": "\x89PNG-fake-bytes\n",
            "docs/assets/adoc_maboss_pathway_dynamics_metadata.json": '{"frames": 10}\n',
            "models/superset/adoc-literature-superset-v0.3.0/literature_superset_network.mmd": "graph TD\nA-->B\n",
            "output/smoke/phase1-run-1/raw/basal_nodes_probtraj.tsv": (
                "Time\tNodeA\n0\t0.1\n"
            ),
            "output/smoke/phase1-run-1/raw/basal_last_nodes_probtraj.tsv": (
                "Time\tNodeA\n0\t0.9\n"
            ),
        }.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        protein_workbook = self.root / "data/proteinas secretadas ADOC.xlsx"
        workbook = Workbook()
        paep = workbook.active
        paep.title = "PAEP"
        paep.append(["sample", "value", "blank", "formula"])
        paep.append(["A", 0, None, "=1+1"])
        prl = workbook.create_sheet("PRL ")
        prl.append(["day", "value"])
        prl.append(["Day 0", 0])
        workbook.save(protein_workbook)
        workbook.close()
        # A second data/ workbook standing in for the annotation workbook, which
        # is gitignored because it carries the lab's own cell-source codes. It
        # must never reach the bundle: the export ships to an external service.
        # The marker is an invented sentinel, never a real cell-source code --
        # a real one must not appear in a tracked file (see
        # tests/unit/test_annotation_workbook.py, which assembles its patterns
        # from fragments for exactly that reason).
        annotation = self.root / "data/secreción proteinas ADOC anotaciones.xlsx"
        self.annotation_marker = "SENTINEL-CELLSOURCE-XYZ"
        annotation_wb = Workbook()
        sheet = annotation_wb.active
        sheet.title = "PAEP"
        sheet.append(["concentracion", "abs muestra- abs control negativo"])
        sheet.append([self.annotation_marker])
        annotation_wb.save(annotation)
        annotation_wb.close()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def make_bundle(self) -> tuple[subprocess.CompletedProcess[str], Path]:
        bundle = self.root / "share.tar.gz"
        result = subprocess.run(
            [
                "bash",
                str(self.root / "scripts/make_chatgpt_results_bundle.sh"),
                "--output",
                str(bundle),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        return result, bundle

    def test_bundle_contents_manifest_and_exclusions(self) -> None:
        result, bundle = self.make_bundle()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(bundle.is_file())
        with tarfile.open(bundle, "r:gz") as archive:
            names = {
                member.name.removeprefix("DT_ADOC_chatgpt_bundle/")
                for member in archive.getmembers()
                if member.isfile()
            }
            manifest = archive.extractfile(
                "DT_ADOC_chatgpt_bundle/CHATGPT_BUNDLE_MANIFEST.tsv"
            )
            self.assertIsNotNone(manifest)
            rows = list(
                csv.DictReader(
                    manifest.read().decode("utf-8").splitlines(), delimiter="\t"
                )
            )
            paep_export = archive.extractfile(
                "DT_ADOC_chatgpt_bundle/input_tables/protein_readouts/"
                "sheets/sheet_01_PAEP.tsv"
            )
            self.assertIsNotNone(paep_export)
            paep_rows = list(
                csv.reader(
                    paep_export.read().decode("utf-8").splitlines(),
                    delimiter="\t",
                )
            )
            sheet_manifest = archive.extractfile(
                "DT_ADOC_chatgpt_bundle/input_tables/protein_readouts/"
                "WORKBOOK_SHEETS.tsv"
            )
            self.assertIsNotNone(sheet_manifest)
            sheet_rows = list(
                csv.DictReader(
                    sheet_manifest.read().decode("utf-8").splitlines(),
                    delimiter="\t",
                )
            )
        self.assertIn("src/run.py", names)
        self.assertIn("docs/legacy/IMPLEMENTATION_PLAN.md", names)
        self.assertIn("docs/legacy/IMPLEMENTATION_STATUS.md", names)
        self.assertIn("docs/legacy/REQUIREMENTS_COVERAGE.tsv", names)
        self.assertIn("THIRD_PARTY_NOTICES.md", names)
        self.assertIn("pixi.lock", names)
        self.assertIn("docs/method.md", names)
        self.assertIn("context/context.md", names)
        self.assertIn("context/literature/README.md", names)
        self.assertIn("context/literature/knowledge-base.yaml", names)
        self.assertIn("context/upstream/upstream_versions.yaml", names)
        self.assertIn("models/model.bnd", names)
        self.assertIn("output/results/run-1/table.tsv", names)
        self.assertIn("output/results/run-1/raw/probtraj.csv", names)
        self.assertIn("output/smoke/phase1-run-1/run_manifest.json", names)
        self.assertIn("output/smoke/phase1-run-1/report/smoke_report.md", names)
        self.assertIn(
            "output/smoke/phase1-run-1/tables/phenotype_probabilities.tsv",
            names,
        )
        self.assertIn("data/README.md", names)
        self.assertIn("docs/assets/adoc_maboss_pathway_dynamics.gif", names)
        self.assertIn("docs/assets/adoc_maboss_pathway_dynamics_preview.png", names)
        self.assertIn("docs/assets/adoc_maboss_pathway_dynamics_metadata.json", names)
        self.assertIn(
            "models/superset/adoc-literature-superset-v0.3.0/"
            "literature_superset_network.mmd",
            names,
        )
        self.assertIn("output/smoke/phase1-run-1/raw/basal_nodes_probtraj.tsv", names)
        self.assertNotIn("output/results/run-1/report.xlsx", names)
        trajectory_rows = [
            row
            for row in rows
            if row["path"] == "output/smoke/phase1-run-1/raw/basal_nodes_probtraj.tsv"
        ]
        self.assertEqual(len(trajectory_rows), 1)
        self.assertEqual(
            trajectory_rows[0]["inclusion_reason"],
            "node-probability-trajectory-sample",
        )
        gif_rows = [
            row
            for row in rows
            if row["path"] == "docs/assets/adoc_maboss_pathway_dynamics.gif"
        ]
        self.assertEqual(len(gif_rows), 1)
        self.assertTrue(gif_rows[0]["inclusion_reason"])
        self.assertIn(
            "input_tables/protein_readouts/proteinas secretadas ADOC.xlsx",
            names,
        )
        self.assertIn("input_tables/protein_readouts/sheets/sheet_01_PAEP.tsv", names)
        self.assertEqual(paep_rows[1], ["A", "0", "", "=1+1"])
        self.assertEqual(sheet_rows[1]["sheet_name"], "PRL ")
        self.assertNotIn("data/private.rds", names)
        self.assertNotIn("output/results/run-1/plot.pdf", names)
        self.assertNotIn("output/results/run-1/checkpoints/partial.tsv", names)
        self.assertEqual(
            {row["path"] for row in rows},
            names - {"CHATGPT_BUNDLE_MANIFEST.tsv"},
        )

    def test_latest_nested_smoke_run_is_selected(self) -> None:
        flat_manifest = self.root / "output/smoke/phase1-run-1/run_manifest.json"
        for path, content in {
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/run_manifest.json": '{\n  "run_id": "phase1d-superset-smoke"\n}\n',
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/report/smoke_report.md": "# Superset Smoke\n",
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/tables/phenotype_probabilities.tsv": "protocol_id\tOUT_STABLE_ADHESION\nht\t0.2\n",
        }.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        nested_manifest = (
            self.root
            / "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/run_manifest.json"
        )
        newer_mtime = flat_manifest.stat().st_mtime + 10
        os.utime(nested_manifest, (newer_mtime, newer_mtime))
        result, bundle = self.make_bundle()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tarfile.open(bundle, "r:gz") as archive:
            names = {
                member.name.removeprefix("DT_ADOC_chatgpt_bundle/")
                for member in archive.getmembers()
                if member.isfile()
            }
        self.assertIn(
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/run_manifest.json",
            names,
        )
        self.assertIn(
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/report/smoke_report.md",
            names,
        )
        self.assertIn(
            "output/smoke/adoc-literature-superset-v0.3.0/phase1d-superset-smoke/tables/phenotype_probabilities.tsv",
            names,
        )
        self.assertNotIn("output/smoke/phase1-run-1/run_manifest.json", names)

    def test_missing_node_probtraj_sample_does_not_fail(self) -> None:
        raw_dir = self.root / "output/smoke/phase1-run-1/raw"
        for path in raw_dir.glob("*_nodes_probtraj.tsv"):
            path.unlink()
        result, bundle = self.make_bundle()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tarfile.open(bundle, "r:gz") as archive:
            names = {
                member.name.removeprefix("DT_ADOC_chatgpt_bundle/")
                for member in archive.getmembers()
                if member.isfile()
            }
        self.assertNotIn(
            "output/smoke/phase1-run-1/raw/basal_nodes_probtraj.tsv", names
        )

    def test_still_forbidden_extensions_remain_excluded(self) -> None:
        result, bundle = self.make_bundle()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with tarfile.open(bundle, "r:gz") as archive:
            names = {
                member.name.removeprefix("DT_ADOC_chatgpt_bundle/")
                for member in archive.getmembers()
                if member.isfile()
            }
        self.assertNotIn("data/private.rds", names)
        self.assertNotIn("output/results/run-1/plot.pdf", names)
        self.assertNotIn("output/results/run-1/report.xlsx", names)

    def test_the_annotation_workbook_never_reaches_the_bundle(self) -> None:
        """The bundle ships to an external service, so a source carrying the
        lab's own cell-source codes must not be in it.

        Two mechanisms protect this and both are exercised here: `.xlsx` is a
        forbidden extension, and nothing tree-copies `data/` -- only an explicit
        allowlist naming the measurement workbook. The content check is the one
        that matters: a future `copy_tree data` would pass a name-only check.
        """
        result, bundle = self.make_bundle()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        marker = self.annotation_marker.encode()
        leaks: list[str] = []
        with tarfile.open(bundle, "r:gz") as archive:
            names = {
                member.name.removeprefix("DT_ADOC_chatgpt_bundle/")
                for member in archive.getmembers()
                if member.isfile()
            }
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                handle = archive.extractfile(member)
                if handle is not None and marker in handle.read():
                    leaks.append(member.name)
        self.assertEqual(sorted(n for n in names if "anotaciones" in n), [])
        self.assertEqual(
            leaks,
            [],
            "annotation-workbook content reached the external bundle: " + str(leaks),
        )
        # The measurement workbook IS expected, via the explicit allowlist.
        self.assertIn(
            "input_tables/protein_readouts/proteinas secretadas ADOC.xlsx", names
        )

    def test_the_bundle_script_keeps_its_two_structural_data_guards(self) -> None:
        """A name-only grep would not catch a future `copy_tree data`, so assert
        the guards themselves: `.xlsx` forbidden, and `data/` never tree-copied.
        """
        script = (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "make_chatgpt_results_bundle.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("*.xlsx", script)
        self.assertNotIn("copy_tree data", script)
        for line in script.splitlines():
            stripped = line.strip()
            if stripped.startswith("copy_tree"):
                self.assertNotIn(
                    " data",
                    stripped,
                    f"data/ must never be tree-copied into the bundle: {stripped}",
                )

    def test_existing_output_is_not_overwritten(self) -> None:
        bundle = self.root / "share.tar.gz"
        bundle.write_text("keep")
        result = subprocess.run(
            [
                "bash",
                str(self.root / "scripts/make_chatgpt_results_bundle.sh"),
                "--output",
                str(bundle),
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(bundle.read_text(), "keep")
        self.assertIn("Refusing to overwrite", result.stderr)

    def test_validator_rejects_path_traversal(self) -> None:
        archive_path = self.root / "unsafe.tar.gz"
        source = self.root / "payload.txt"
        source.write_text("unsafe")
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(source, arcname="../payload.txt")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.root / "scripts/validate_chatgpt_bundle.py"),
                str(archive_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe archive member path", result.stdout)


if __name__ == "__main__":
    unittest.main()
