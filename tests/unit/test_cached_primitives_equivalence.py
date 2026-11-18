"""The two cached primitives agree exactly with what they replaced.

`perturbations.engine._value` compiles each rule string once instead of on
every call, and `model.runtime._provenance_payload` parses each distinct
`provenance.toml` text once instead of on every read (the 2026-10-15 audit
measured them at about 33 % and 16 % of the suite; see
docs/verification/cache_design.md). Both are performance changes only, so the
acceptance criterion is exact agreement with the uncached implementation, with
no tolerance.

The uncached references are written here, not imported from the code under
test: string `eval` under the same restricted globals, and `tomllib.loads` of
the text just read. Equality covers results *and* refusals: an exception must
have the same type and the same `args`.

The TOML cache is keyed by content, so the cases below edit and restore files
in place while keeping their size and modification time, which a path, size or
mtime key would get wrong.
"""

from __future__ import annotations

import csv
import itertools
import os
import random
import shutil
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

from dt_adoc.maboss_adapter import LOGIC_LINE_RE
from dt_adoc.model import runtime
from dt_adoc.perturbations import engine

#: Rules with at most this many inputs are checked on every assignment.
EXHAUSTIVE_INPUTS = 12
#: Seeded random assignments for a rule with more inputs.
RANDOM_ASSIGNMENTS = 10_000
SEED = 20261016

V060 = "adoc-literature-superset-v0.6.0"


def _reference_value(expression: object, assignment: dict[str, bool]) -> bool:
    """The uncached implementation: ``eval`` of the expression itself."""
    return bool(eval(expression, {"__builtins__": {}}, assignment))


def _reference_payload(path: Path) -> dict[str, object]:
    """The uncached implementation: parse the text just read."""
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _outcome(function, *args) -> tuple[str, object]:
    try:
        return ("value", function(*args))
    except Exception as error:  # noqa: BLE001 - the refusal is what is compared
        return (type(error).__qualname__, error.args)


def _committed_rules() -> dict[str, set[str]]:
    """Every rule text of every committed model version, with where it occurs.

    Every ``network.bnd`` under ``models/`` (including generated subvariants)
    and every expression of every ``rule_variants.tsv``. Identical texts are
    one entry, because the cache key is the text.
    """
    rules: dict[str, set[str]] = {}
    for bnd in sorted(ROOT.glob("models/**/network.bnd")):
        where = str(bnd.relative_to(ROOT))
        for match in LOGIC_LINE_RE.finditer(bnd.read_text(encoding="utf-8")):
            rules.setdefault(match.group(2), set()).add(where)
    for table in sorted(ROOT.glob("models/**/rule_variants.tsv")):
        where = str(table.relative_to(ROOT))
        with table.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                rules.setdefault(row["expression"], set()).add(where)
    return rules


def _assignments(expression: str, names: frozenset[str]):
    ordered = sorted(names)
    if len(ordered) <= EXHAUSTIVE_INPUTS:
        for values in itertools.product((False, True), repeat=len(ordered)):
            yield dict(zip(ordered, values))
        return
    rng = random.Random(f"{SEED}:{expression}")
    for _ in range(RANDOM_ASSIGNMENTS):
        yield {name: rng.random() < 0.5 for name in ordered}


class CompiledExpressionsMatchStringEval(unittest.TestCase):
    """Optimisation A: compiled ``_value`` equals string ``eval`` everywhere."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = _committed_rules()

    def setUp(self) -> None:
        engine._compiled.cache_clear()

    def test_the_corpus_covers_every_model_version(self) -> None:
        versions = {
            str(path.parent.relative_to(ROOT))
            for path in ROOT.glob("models/*/*/network.bnd")
        }
        covered = {
            str(Path(where).parent)
            for places in self.rules.values()
            for where in places
            if where.endswith("network.bnd")
        }
        self.assertTrue(versions)
        self.assertLessEqual(versions, covered)
        self.assertIn(f"models/superset/{V060}", covered)

    def _assert_agrees(self, expression: str, names: frozenset[str]) -> int:
        checked = 0
        for assignment in _assignments(expression, names):
            expected = _outcome(_reference_value, expression, dict(assignment))
            self.assertEqual(
                _outcome(engine._value, expression, dict(assignment)),
                expected,
                f"{expression!r} at {assignment}",
            )
            checked += 1
        return checked

    def test_every_committed_rule_agrees_on_its_assignments(self) -> None:
        checked = 0
        for logic, places in sorted(self.rules.items()):
            with self.subTest(rule=logic, where=min(places)):
                expression, names = engine._evaluable(logic)
                # The text as the engine evaluates it and as it was written.
                for text in dict.fromkeys((expression, logic)):
                    checked += self._assert_agrees(text, names)
        self.assertGreater(checked, len(self.rules))
        self.assertGreater(engine._compiled.cache_info().hits, 0)

    def test_every_vetoed_rendering_agrees(self) -> None:
        # The engine evaluates the rendered veto, not only the rule as written.
        for logic in sorted(self.rules):
            with self.subTest(rule=logic):
                rendered = engine.activity_veto_logic(logic)
                expression, names = engine._evaluable(rendered)
                self._assert_agrees(rendered, names)
                self._assert_agrees(expression, names)

    def test_leading_and_trailing_whitespace_is_handled_as_eval_handles_it(
        self,
    ) -> None:
        # String ``eval`` strips leading spaces and tabs before compiling, and
        # plain ``compile`` does not: without the strip, "  A" would turn from
        # True into an IndentationError.
        for logic in sorted(self.rules)[:10]:
            expression, names = engine._evaluable(logic)
            for text in (
                f" {expression}",
                f"\t{expression}",
                f" \t {expression}",
                f"{expression} ",
                f"{expression}\n",
                f"\x0c{expression}",
                f"\n {expression}",
            ):
                with self.subTest(text=text):
                    self._assert_agrees(text, names)

    def test_a_missing_input_is_refused_as_before(self) -> None:
        # Short-circuiting means a missing name is not always read, so the
        # reference decides which cases are refusals; both kinds must agree.
        refused = 0
        for logic in sorted(self.rules):
            expression, names = engine._evaluable(logic)
            for missing, fill in itertools.product(sorted(names), (False, True)):
                assignment = dict.fromkeys(sorted(names - {missing}), fill)
                with self.subTest(rule=logic, missing=missing, fill=fill):
                    expected = _outcome(_reference_value, expression, dict(assignment))
                    refused += expected[0] == "NameError"
                    self.assertEqual(
                        _outcome(engine._value, expression, dict(assignment)), expected
                    )
        self.assertGreater(refused, len(self.rules))

    def test_malformed_and_unsafe_expressions_are_refused_identically(self) -> None:
        assignment = {"A": True, "B": False, "C": True}
        for text in (
            "",
            " ",
            "A and",
            "(A",
            "A)",
            "A B",
            "A && B",
            "A & B",
            "A | B",
            "!A",
            "A; B",
            "A\x00",
            "A = B",
            "lambda: A",
            "__import__('os')",
            "open('x')",
            "print(A)",
            "A.__class__",
            "1 / 0",
            "D",
            "not",
            "\n A",
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    _outcome(engine._value, text, dict(assignment)),
                    _outcome(_reference_value, text, dict(assignment)),
                )
                # A refusal is never cached, so it is raised again.
                before = engine._compiled.cache_info().currsize
                self.assertEqual(
                    _outcome(engine._value, text, dict(assignment)),
                    _outcome(_reference_value, text, dict(assignment)),
                )
                self.assertLessEqual(engine._compiled.cache_info().currsize, before)

    def test_inputs_that_are_not_str_go_to_eval_unchanged(self) -> None:
        class Text(str):
            pass

        code = compile("A or B", "<string>", "eval")
        assignment = {"A": False, "B": True}
        for value in (b"A and B", b"  A", code, Text("A and B"), None, 1, ["A"]):
            with self.subTest(value=value):
                self.assertEqual(
                    _outcome(engine._value, value, dict(assignment)),
                    _outcome(_reference_value, value, dict(assignment)),
                )
        self.assertEqual(engine._compiled.cache_info().currsize, 0)

    def test_the_restricted_environment_is_unchanged(self) -> None:
        # No builtins reach the rule, cached or not.
        for text in ("len", "True.__class__.__mro__", "__builtins__"):
            with self.subTest(text=text):
                self.assertEqual(
                    _outcome(engine._value, text, {}),
                    _outcome(_reference_value, text, {}),
                )
        self.assertEqual(_outcome(engine._value, "len", {})[0], "NameError")


class ExpressionCacheHygiene(unittest.TestCase):
    """Optimisation A: the key is the whole expression, and nothing else."""

    def setUp(self) -> None:
        engine._compiled.cache_clear()

    def test_expressions_sharing_a_prefix_keep_their_own_values(self) -> None:
        assignment = {"A": True, "B": False, "C": True, "D": True}
        texts = (
            "A",
            "A and B",
            "A and B or C",
            "A and B or C and not D",
            "A and B or C and not D or B",
        )
        for _ in range(2):
            for text in texts:
                with self.subTest(text=text):
                    self.assertEqual(
                        engine._value(text, dict(assignment)),
                        _reference_value(text, dict(assignment)),
                    )
        self.assertEqual(engine._compiled.cache_info().currsize, len(texts))

    def test_one_expression_under_many_assignments(self) -> None:
        text = "(A and not B) or (C and D)"
        names = ("A", "B", "C", "D")
        for values in itertools.product((False, True), repeat=4):
            assignment = dict(zip(names, values))
            self.assertEqual(
                engine._value(text, assignment),
                _reference_value(text, dict(assignment)),
            )
        # Sixteen assignments, one entry: the assignment is never part of the key.
        self.assertEqual(engine._compiled.cache_info().currsize, 1)

    def test_a_reused_assignment_dict_is_read_afresh(self) -> None:
        assignment = {"A": True, "B": True}
        self.assertTrue(engine._value("A and B", assignment))
        assignment["B"] = False
        self.assertFalse(engine._value("A and B", assignment))

    def test_the_cache_is_bounded(self) -> None:
        maxsize = engine._compiled.cache_info().maxsize
        self.assertIsNotNone(maxsize)
        self.assertLessEqual(maxsize, 4096)
        texts = [f"N{i} or not N{i}" for i in range(maxsize + 50)]
        for index, text in enumerate(texts):
            self.assertTrue(engine._value(text, {f"N{index}": False}))
        self.assertEqual(engine._compiled.cache_info().currsize, maxsize)
        # An evicted entry is recompiled, not returned stale or lost.
        self.assertFalse(engine._value("N0 and not N0", {"N0": True}))
        self.assertTrue(engine._value(texts[0], {"N0": True}))


class RuleRefusalsAreUnchanged(unittest.TestCase):
    """The checks built on ``_value`` still accept and refuse as before."""

    def test_unparseable_rules_are_refused_before_evaluation(self) -> None:
        for logic in ("A & B", "A | B", "!A", "A; B", "A + B", "A == B", "A, B", "'A'"):
            with (
                self.subTest(logic=logic),
                self.assertRaisesRegex(engine.InterventionError, "cannot check rule"),
            ):
                engine._evaluable(logic)

    def test_the_migrated_rule_check_accepts_and_refuses_as_before(self) -> None:
        check = engine._check_migrated_rule
        # The child is the parent with the marker OFF, and the marker vetoes.
        check("T", "A and B", "A and B and not IN_X", "IN_X", {"IN_X"})
        with self.assertRaisesRegex(
            engine.InterventionError,
            r"T: the rule is not the parent's with \['IN_X'\] OFF",
        ):
            check("T", "A or B", "A and B and not IN_X", "IN_X", {"IN_X"})
        with self.assertRaisesRegex(
            engine.InterventionError, "T: the parent's rule with IN_X ON is not a veto"
        ):
            check("T", "A and B", "(A and B) or IN_X", "IN_X", {"IN_X"})
        with self.assertRaisesRegex(
            engine.InterventionError, "T: the rule still reads"
        ):
            check("T", "A and IN_X", "A and not IN_X", "IN_X", {"IN_X"})


class TomlPayloadsMatchTheParse(unittest.TestCase):
    """Optimisation B: the cached payload is the parse, and callers own it."""

    def setUp(self) -> None:
        runtime._parsed_toml.cache_clear()

    def test_every_committed_provenance_parses_identically(self) -> None:
        paths = sorted(ROOT.glob("models/**/provenance.toml"))
        self.assertGreaterEqual(len(paths), 9)
        for path in paths:
            with self.subTest(path=str(path.relative_to(ROOT))):
                expected = _reference_payload(path)
                first = runtime._provenance_payload(path)
                second = runtime._provenance_payload(path)
                self.assertEqual(first, expected)
                self.assertEqual(second, expected)
                self.assertIsNot(first, second)

    def test_mutating_a_payload_cannot_reach_another_caller(self) -> None:
        def wreck(value: object) -> None:
            if isinstance(value, dict):
                for item in list(value.values()):
                    wreck(item)
                value.clear()
                value["wrecked"] = True
            elif isinstance(value, list):
                for item in value:
                    wreck(item)
                value.clear()
                value.append("wrecked")

        for path in sorted(ROOT.glob("models/**/provenance.toml")):
            with self.subTest(path=str(path.relative_to(ROOT))):
                expected = _reference_payload(path)
                wreck(runtime._provenance_payload(path))
                self.assertEqual(runtime._provenance_payload(path), expected)

    def test_the_cache_is_bounded(self) -> None:
        maxsize = runtime._parsed_toml.cache_info().maxsize
        self.assertIsNotNone(maxsize)
        self.assertLessEqual(maxsize, 256)


class RegistryMatchesTheUncachedRegistry(unittest.TestCase):
    """Optimisation B: the registry and its validation are unchanged."""

    def setUp(self) -> None:
        runtime._parsed_toml.cache_clear()

    def test_the_registry_equals_the_uncached_registry(self) -> None:
        with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
            expected = runtime.available_models(ROOT)
            expected_resolved = {v: runtime.resolve_model(v, ROOT) for v in expected}
        for _ in range(2):  # cold, then warm
            self.assertEqual(runtime.available_models(ROOT), expected)
            self.assertEqual(
                {v: runtime.resolve_model(v, ROOT) for v in expected}, expected_resolved
            )

    def test_an_unknown_version_is_refused_identically(self) -> None:
        with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
            expected = _outcome(runtime.resolve_model, "adoc-nonexistent-v9", ROOT)
        self.assertEqual(expected[0], "ValueError")
        self.assertEqual(
            _outcome(runtime.resolve_model, "adoc-nonexistent-v9", ROOT), expected
        )

    def test_every_provenance_file_is_still_read_on_every_resolution(self) -> None:
        original = Path.read_text

        def reads(implementation) -> list[str]:
            seen: list[str] = []

            def spy(self, *args, **kwargs):
                if self.name == "provenance.toml":
                    seen.append(str(self.relative_to(ROOT)))
                return original(self, *args, **kwargs)

            with (
                mock.patch.object(runtime, "_provenance_payload", implementation),
                mock.patch.object(Path, "read_text", spy),
            ):
                for _ in range(3):
                    runtime.resolve_model(V060, ROOT)
            return seen

        expected = reads(_reference_payload)
        self.assertEqual(reads(runtime._provenance_payload), expected)
        self.assertGreater(len(expected), 3 * 3)


class CacheFollowsTheFilesystem(unittest.TestCase):
    """Optimisation B under in-place edits and sandbox copies of ``models/``."""

    def setUp(self) -> None:
        runtime._parsed_toml.cache_clear()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "a"
        shutil.copytree(ROOT / "models", self.root / "models")
        self.provenance = self.root / "models" / "superset" / V060 / "provenance.toml"
        self.original = self.provenance.read_text(encoding="utf-8")

    def _rewrite_keeping_size_and_mtime(self, path: Path, text: str) -> None:
        before = path.stat()
        path.write_text(text, encoding="utf-8")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = path.stat()
        self.assertEqual(
            (after.st_size, after.st_mtime_ns), (before.st_size, before.st_mtime_ns)
        )

    def _same_length_edit(self, old: str, new: str) -> str:
        self.assertEqual(len(old), len(new))
        self.assertEqual(self.original.count(old), 1)
        return self.original.replace(old, new)

    def test_an_edit_and_its_restoration_within_one_mtime_tick(self) -> None:
        initial = runtime.resolve_model(V060, self.root)
        edited = self._same_length_edit(
            f'model_version = "{V060}"',
            'model_version = "adoc-literature-superset-v0.6.9"',
        )
        for _ in range(2):
            self._rewrite_keeping_size_and_mtime(self.provenance, edited)
            with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
                expected = _outcome(runtime.resolve_model, V060, self.root)
            self.assertEqual(expected[0], "ValueError")
            self.assertIn("adoc-literature-superset-v0.6.9", expected[1][0])
            self.assertEqual(_outcome(runtime.resolve_model, V060, self.root), expected)

            self._rewrite_keeping_size_and_mtime(self.provenance, self.original)
            self.assertEqual(runtime.resolve_model(V060, self.root), initial)

    def test_an_edited_value_is_seen_immediately(self) -> None:
        self.assertEqual(
            runtime.resolve_model(V060, self.root).model_id,
            "adoc_literature_superset_v060",
        )
        self._rewrite_keeping_size_and_mtime(
            self.provenance,
            self._same_length_edit(
                'family_id = "adoc_literature_superset_v060"',
                'family_id = "adoc_literature_superset_v069"',
            ),
        )
        self.assertEqual(
            runtime.resolve_model(V060, self.root).model_id,
            "adoc_literature_superset_v069",
        )
        self._rewrite_keeping_size_and_mtime(self.provenance, self.original)
        self.assertEqual(
            runtime.resolve_model(V060, self.root).model_id,
            "adoc_literature_superset_v060",
        )

    def test_malformed_toml_is_refused_every_time_then_recovers(self) -> None:
        broken = self.original.replace("model_version =", "model_version ==", 1)
        self.provenance.write_text(broken, encoding="utf-8")
        with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
            expected = _outcome(runtime.resolve_model, V060, self.root)
        self.assertEqual(expected[0], "TOMLDecodeError")
        for _ in range(2):
            self.assertEqual(_outcome(runtime.resolve_model, V060, self.root), expected)
        self.provenance.write_text(self.original, encoding="utf-8")
        self.assertEqual(runtime.resolve_model(V060, self.root).model_version, V060)

    def test_a_missing_provenance_is_refused_as_before(self) -> None:
        baseline = (
            self.root / "models" / "baseline" / "adoc-core-v0.1.0" / "provenance.toml"
        )
        baseline.unlink()
        with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
            expected = _outcome(runtime.resolve_model, V060, self.root)
        self.assertEqual(expected[0], "FileNotFoundError")
        self.assertEqual(_outcome(runtime.resolve_model, V060, self.root), expected)

    def test_two_roots_that_differ_in_one_value_resolve_differently(self) -> None:
        other = Path(self._tmp.name) / "b"
        shutil.copytree(self.root / "models", other / "models")
        other_provenance = other / "models" / "superset" / V060 / "provenance.toml"
        self._rewrite_keeping_size_and_mtime(
            other_provenance,
            self._same_length_edit(
                'family_id = "adoc_literature_superset_v060"',
                'family_id = "adoc_literature_superset_v069"',
            ),
        )
        for _ in range(2):  # interleaved, so each root follows a warm cache
            a = runtime.resolve_model(V060, self.root)
            b = runtime.resolve_model(V060, other)
            self.assertEqual(a.model_id, "adoc_literature_superset_v060")
            self.assertEqual(b.model_id, "adoc_literature_superset_v069")
            self.assertEqual(a.model_root, self.root / "models" / "superset" / V060)
            self.assertEqual(b.model_root, other / "models" / "superset" / V060)

    def test_identical_roots_share_a_parse_but_keep_their_own_paths(self) -> None:
        other = Path(self._tmp.name) / "b"
        shutil.copytree(self.root / "models", other / "models")
        a = runtime.resolve_model(V060, self.root)
        hits = runtime._parsed_toml.cache_info().hits
        b = runtime.resolve_model(V060, other)
        self.assertGreater(runtime._parsed_toml.cache_info().hits, hits)
        self.assertEqual(a.model_id, b.model_id)
        self.assertEqual(
            b.provenance, other / "models" / "superset" / V060 / "provenance.toml"
        )
        self.assertEqual(
            b, runtime.resolve_model(V060, other)
        )  # and the same spec again
        with mock.patch.object(runtime, "_provenance_payload", _reference_payload):
            self.assertEqual(runtime.resolve_model(V060, other), b)
            self.assertEqual(runtime.resolve_model(V060, self.root), a)


if __name__ == "__main__":
    unittest.main()
