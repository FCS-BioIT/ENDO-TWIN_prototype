from __future__ import annotations

import contextlib
import importlib
import io
import sys
import unittest
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class _BlockMabossFinder(MetaPathFinder):
    def find_spec(self, fullname: str, path=None, target=None):
        if fullname == "maboss" or fullname.startswith("maboss."):
            raise ModuleNotFoundError("blocked maboss import for CLI boundary test")
        return PathFinder.find_spec(fullname, path, target)


class CliImportBoundaryTest(unittest.TestCase):
    def test_non_smoke_command_does_not_require_maboss(self) -> None:
        blocked = _BlockMabossFinder()
        original = sys.modules.pop("dt_adoc.cli", None)
        try:
            sys.meta_path.insert(0, blocked)
            cli = importlib.import_module("dt_adoc.cli")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = cli.main(["path-report", "."])
            self.assertEqual(exit_code, 0)
            self.assertTrue(stdout.getvalue().strip())
        finally:
            sys.meta_path.remove(blocked)
            sys.modules.pop("dt_adoc.cli", None)
            if original is not None:
                sys.modules["dt_adoc.cli"] = original


if __name__ == "__main__":
    unittest.main()
