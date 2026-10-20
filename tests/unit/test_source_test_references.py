"""A source comment that names a test must name one that exists.

Narrow on purpose. This is not prose validation: it checks exactly one
mechanical claim, of the form a reviewer can otherwise only catch by hand.

Several modules in `src/` say "pinned by `test_module.ClassName`" to tell a
reader that a stated behaviour is guarded rather than merely asserted. That
pointer is load-bearing -- it is the reason a reader stops looking for the
guard -- and nothing checked it. Two such references in
`reporting/identifiability_figure.py` named `test_identifiability_figure`, a
module that does not exist; the classes were real and lived in
`test_identifiability`. The claim "this is pinned" was true and the address was
wrong, which is the worst combination: it survives every test run and sends a
reader to nothing.

Scope is deliberately one pattern, `test_<module>.<ClassName>`, in `src/`. It
does not check that the named class asserts what the comment says it asserts --
no test can -- only that following the pointer arrives somewhere.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
TESTS = ROOT / "tests"

#: `test_something.ClassName`, the form these pointers actually take. Bounded to
#: a leading `test_` so it cannot start matching ordinary dotted attributes.
REFERENCE = re.compile(r"\b(test_[a-z0-9_]+)\.([A-Z][A-Za-z0-9_]*)\b")


def _test_classes() -> dict[str, set[str]]:
    """Every class defined in every test module, keyed by module stem.

    Parsed rather than imported: importing the suite to check a comment would
    make this test's cost the suite's cost, and a syntax error in an unrelated
    test module would surface here as a confusing failure.
    """
    found: dict[str, set[str]] = {}
    for path in TESTS.rglob("test_*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - reported by its own module
            continue
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        found.setdefault(path.stem, set()).update(names)
    return found


class SourceTestReferencesResolveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classes = _test_classes()

    def test_the_test_modules_were_found(self) -> None:
        """A guard that silently scanned nothing would always pass."""
        self.assertGreater(len(self.classes), 10)
        self.assertIn("test_identifiability", self.classes)

    def test_every_named_test_class_exists(self) -> None:
        missing: list[str] = []
        for path in sorted(SRC.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for module, klass in set(REFERENCE.findall(text)):
                if module not in self.classes:
                    missing.append(
                        f"{path.relative_to(ROOT)}: no test module {module!r} "
                        f"(referenced as {module}.{klass})"
                    )
                elif klass not in self.classes[module]:
                    missing.append(
                        f"{path.relative_to(ROOT)}: {module} has no class {klass!r}"
                    )
        self.assertEqual(
            missing,
            [],
            "source comments point at tests that do not exist:\n  "
            + "\n  ".join(missing),
        )

    def test_the_two_references_this_was_written_for_resolve(self) -> None:
        """Named, so a general guard that stopped covering them would fail."""
        for klass in ("PerturbationMarkerCoverageTest", "PanelScopeTest"):
            self.assertIn(klass, self.classes["test_identifiability"])
