"""Phase 2B: fail-closed behaviour of reference qualification for E_KLF12_HIGH.

Every refusal is paired with a positive control, so no refusal can pass
vacuously. Nothing here reads a real candidate's expression value: the
derivation is exercised on synthetic donors only.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc import closure_replay
from dt_adoc.personalization import phase2a_contract as P
from dt_adoc.personalization.phase2b import audit as A
from dt_adoc.personalization.phase2b import derivation as D
from dt_adoc.personalization.phase2b import guard as G
from dt_adoc.personalization.phase2b import identity as I
from dt_adoc.personalization.phase2b import qualification as Q
from dt_adoc.personalization.phase2b import values as V

PHASE2B = ROOT / "docs/phase2b"
_TMPS: list[tempfile.TemporaryDirectory] = []


def _donor(
    name: str,
    seed: int,
    high_share: float,
    *,
    n: int = 700,
    lo: float = 0.2,
    hi: float = 12.0,
    depth_sd: float = 0.4,
) -> D.DonorCells:
    """Negative-binomial counts from one or two latent rates, decontX-like shrinkage."""
    draw = random.Random(seed)
    counts, depths = [], []
    for _ in range(n):
        depth = draw.lognormvariate(math.log(8000), depth_sd)
        rate = (hi if draw.random() < high_share else lo) * depth / 8000
        k = D._poisson(draw.gammavariate(20, rate / 20), draw)
        counts.append(k * draw.gauss(0.92, 0.05) if k else 0.0)
        depths.append(depth)
    return D.DonorCells(name, tuple(counts), tuple(depths))


TWO_STATE = [_donor(f"REF{i}", i, 0.3) for i in range(3)]
STATELESS = [_donor(f"NUL{i}", 10 + i, 0.0, lo=0.6) for i in range(3)]


# Closed phases are reproduced against their closure-time models/ snapshot
# (src/dt_adoc/closure_replay.py); later model versions are outside it.
_CLOSURE_TMP = tempfile.TemporaryDirectory(prefix="closure-replay-")
CLOSURE, _CLOSURE_INDEX = closure_replay.build_view(ROOT, Path(_CLOSURE_TMP.name))
CLOSURE_ENV = {"GIT_INDEX_FILE": str(_CLOSURE_INDEX)}


def tearDownModule() -> None:
    _CLOSURE_TMP.cleanup()


class Derivation(unittest.TestCase):
    """The pre-registered threshold derivation, on synthetic donors."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.two_state = D.derive(TWO_STATE, min_reference_donors=3)
        cls.stateless = D.derive(STATELESS, min_reference_donors=3)

    def test_a_real_two_state_population_yields_a_primary_and_two_variants(
        self,
    ) -> None:
        result = self.two_state
        self.assertEqual(result["verdict"], D.QUALIFIED)
        low, high = result["threshold_variants"]
        self.assertLess(low, result["primary_threshold"])
        self.assertLess(result["primary_threshold"], high)
        self.assertEqual(result["variant_selection"], "all_reported_none_selected")
        self.assertEqual(result["quantity"], "count_per_10k")
        self.assertEqual(result["aggregation_unit"], "donor")
        for donor in result["per_donor"]:
            null = donor["null_specificity"]
            self.assertEqual(null["null_replicates_at_or_above_observed"], 0)
            self.assertLessEqual(
                null["plugin_null_exceedance_score"],
                1 / (D.NULL_REPLICATES + 1) + 1e-12,
            )

    def test_an_unfitted_null_replicate_counts_against_the_separation(self) -> None:
        # Review blocker (amendment 01): with only 80 of 99 replicates fitted
        # the score could reach 1/81, not the stated 1/100. Unfitted now counts.
        real = D.separation
        calls = {"n": 0}

        def drop_some(values, floor):
            calls["n"] += 1
            if 1 < calls["n"] <= 1 + 19:  # the first call is the observed fit
                return {
                    "qualifies": False,
                    "reason": "too_few_detected",
                    "n_detected": 0,
                }
            return real(values, floor)

        with mock.patch.object(D, "separation", side_effect=drop_some):
            result = D.donor_result(TWO_STATE[0], D.PRIMARY_QUANTITY)
        null = result["null_specificity"]
        self.assertEqual(null["fitted"], 80)
        self.assertEqual(null["null_replicates_unfitted_counted_as_exceeding"], 19)
        self.assertGreater(null["plugin_null_exceedance_score"], 0.01)
        self.assertFalse(null["passes"])
        self.assertFalse(result["qualifies"])

    def test_a_passing_donor_has_an_exceedance_score_of_at_most_one_in_a_hundred(
        self,
    ) -> None:
        for donor in self.two_state["per_donor"]:
            null = donor["null_specificity"]
            self.assertLessEqual(null["plugin_null_exceedance_score"], 0.01)
            self.assertEqual(null["fitted"], D.NULL_REPLICATES)

    def test_a_stateless_population_yields_no_threshold(self) -> None:
        self.assertEqual(self.stateless["verdict"], D.NOT_QUALIFIED)
        self.assertNotIn("primary_threshold", self.stateless)
        self.assertNotIn("threshold_variants", self.stateless)

    def test_a_one_molecule_lattice_is_never_a_threshold(self) -> None:
        # Constant depth and a low rate: the log-scale data are the integer
        # lattice itself, the Phase-1B failure mode.
        lattice = [
            _donor(f"LAT{i}", 20 + i, 0.0, lo=0.25, depth_sd=0.0) for i in range(3)
        ]
        self.assertEqual(
            D.derive(lattice, min_reference_donors=3)["verdict"], D.NOT_QUALIFIED
        )

    def test_the_null_rejects_a_criterion_that_certifies_anything(self) -> None:
        # A separation rule that says yes to every input: the observed data pass
        # S1-S3 by construction, and only the stateless null can refuse it.
        def always(values, floor):
            detected = sum(1 for v in values if v > 0)
            return {
                "qualifies": True,
                "n_detected": detected,
                "ashman_d": 2.0,
                "boundaries": {"0.25": 1.0, "0.5": 2.0, "0.75": 3.0},
            }

        with mock.patch.object(D, "separation", side_effect=always):
            result = D.donor_result(STATELESS[0], D.PRIMARY_QUANTITY)
        null = result["null_specificity"]
        self.assertFalse(result["qualifies"])
        self.assertFalse(null["passes"])
        self.assertEqual(null["null_replicates_at_or_above_observed"], null["fitted"])

    def test_one_failing_donor_fails_the_reference_rather_than_being_dropped(
        self,
    ) -> None:
        mixed = [*TWO_STATE[:2], STATELESS[0]]
        result = D.derive(mixed, min_reference_donors=2)
        self.assertEqual(result["verdict"], D.NOT_QUALIFIED)
        self.assertEqual(result["n_reference_donors"], 3)

    def test_too_few_reference_donors_fails(self) -> None:
        result = D.derive(TWO_STATE[:2], min_reference_donors=3)
        self.assertEqual(result["verdict"], D.NOT_QUALIFIED)
        self.assertEqual(
            result["reason"], "fewer_reference_donors_than_min_reference_donors"
        )

    def test_adoc_donors_can_never_be_reference_donors(self) -> None:
        for name in (
            "SZ09",
            "sz-10",
            "donor_SZ25TE",
            "SZ 09",
            "SZ9",
            "\uff33\uff3a\uff10\uff19",
        ):
            with self.subTest(name=name):
                cells = D.DonorCells(name, TWO_STATE[0].counts, TWO_STATE[0].depths)
                with self.assertRaises(D.DerivationError):
                    D.derive([cells, *TWO_STATE[1:]], min_reference_donors=3)

    def test_a_repeated_donor_is_one_donor(self) -> None:
        with self.assertRaises(D.DerivationError):
            D.derive([TWO_STATE[0], TWO_STATE[0], TWO_STATE[1]], min_reference_donors=2)

    def test_min_reference_donors_must_be_an_owner_integer(self) -> None:
        for bad in (0, True, 2.5, None):
            with self.subTest(bad=bad), self.assertRaises(D.DerivationError):
                D.derive(TWO_STATE, min_reference_donors=bad)  # type: ignore[arg-type]

    def test_the_derivation_admits_no_outcome_or_model_input(self) -> None:
        self.assertEqual(
            list(inspect.signature(D.derive).parameters),
            ["donors", "min_reference_donors"],
        )
        self.assertEqual(
            [f for f in D.DonorCells.__dataclass_fields__],
            ["donor_id", "counts", "depths"],
        )

    def test_the_count_scale_is_a_diagnostic_and_never_a_variant(self) -> None:
        result = self.two_state
        self.assertEqual(len(result["threshold_variants"]), 2)
        self.assertIn("diagnostic only", result["diagnostic_count_scale"]["role"])
        self.assertNotIn("primary_threshold", result["diagnostic_count_scale"])

    def test_the_derivation_is_deterministic(self) -> None:
        again = D.derive(TWO_STATE, min_reference_donors=3)
        self.assertEqual(
            json.dumps(again, sort_keys=True),
            json.dumps(self.two_state, sort_keys=True),
        )

    def test_posterior_half_roots_match_the_phase1b_solver(self) -> None:
        fit = {
            "high_component_weight": 0.3,
            "log_mean_low": 0.0,
            "log_sd_low": 0.5,
            "log_mean_high": 2.0,
            "log_sd_high": 0.4,
        }
        from dt_adoc.scrna.klf12_state import _component_crossings

        for ours, theirs in zip(
            D.posterior_roots(fit, 0.5),
            _component_crossings(0.0, 0.25, 2.0, 0.16, 0.3),
            strict=True,
        ):
            self.assertAlmostEqual(ours, theirs, places=9)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


PINS = ("impl/derivation.py",)


def _repo(*, layout: str = "normal", pins: dict | None = None) -> Path:
    """A throwaway repository: owner decisions, then the rules on their own."""
    tmp = tempfile.TemporaryDirectory()
    _TMPS.append(tmp)
    root = Path(tmp.name)
    _git(root, "init", "-q", "-b", "main")
    _write(
        root,
        "config/external_data_manifest.tsv",
        f"asset_id\tsha256\n{P.ASSET_ID}\t{'a' * 64}\n",
    )
    _write(root, "config/data_manifest.tsv", f"path\tsha256\ndata/x\t{'b' * 64}\n")
    _write(root, "impl/derivation.py", "RULE = '>='\n")
    _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "owner decisions")
    if pins is None:
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
    _write(root, str(G.PREREG_JSON), json.dumps({"pinned_implementation_sha256": pins}))
    _write(root, str(G.PREREG_MD), "# rules\n")
    if layout == "with_other_file":
        _write(root, "other.txt", "x\n")
    if layout == "split":
        _git(root, "add", str(G.PREREG_JSON))
        _git(root, "commit", "-qm", "json")
    if layout == "decisions_with_rules":
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 4}\n')
    if layout != "uncommitted":
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules")
    return root


def _frozen(root: Path) -> dict[str, str]:
    return G.assert_rules_frozen(root, required_pins=PINS)


class OrderingGuard(unittest.TestCase):
    """No candidate value may be read before the rules are provably frozen."""

    def test_positive_control(self) -> None:
        self.assertEqual(len(_frozen(_repo())["rules_commit"]), 40)

    def test_uncommitted_rules_refuse(self) -> None:
        with self.assertRaises(G.OrderingError):
            _frozen(_repo(layout="uncommitted"))

    def test_rules_must_be_their_own_commit(self) -> None:
        for layout in ("with_other_file", "split", "decisions_with_rules"):
            with self.subTest(layout=layout), self.assertRaises(G.OrderingError):
                _frozen(_repo(layout=layout))

    def test_an_edited_rule_refuses_even_uncommitted(self) -> None:
        root = _repo()
        _write(root, str(G.PREREG_MD), "# rules, edited after the fact\n")
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_a_rewritten_then_restored_rule_refuses(self) -> None:
        root = _repo()
        _write(root, str(G.PREREG_MD), "# changed\n")
        _git(root, "commit", "-qam", "change")
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "commit", "-qam", "restore")
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_an_earlier_draft_on_a_merged_side_branch_refuses(self) -> None:
        # Probe B1: rules v1 on a side branch, values read there, rules v2 on
        # main, then `merge -s ours` hides v1 from default history simplification.
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        _git(root, "init", "-q", "-b", "main")
        _write(root, "impl/derivation.py", "RULE = '>='\n")
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "decisions")
        pins = json.dumps(
            {
                "pinned_implementation_sha256": {
                    "impl/derivation.py": G.sha256(root / "impl/derivation.py")
                }
            }
        )
        _git(root, "checkout", "-qb", "draft")
        _write(root, str(G.PREREG_JSON), pins)
        _write(root, str(G.PREREG_MD), "# rules v1\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules v1")
        _write(root, "peek.txt", "values read\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "peek")
        _git(root, "checkout", "-q", "main")
        _write(root, str(G.PREREG_JSON), pins)
        _write(root, str(G.PREREG_MD), "# rules v2, tuned\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules v2")
        _git(root, "merge", "-q", "-s", "ours", "draft", "-m", "merge")
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_a_shallow_clone_refuses(self) -> None:
        # Probe B2: a shallow boundary can hide an earlier add.
        source = _repo()
        _write(source, "later.txt", "x\n")
        _git(source, "add", "-A")
        _git(source, "commit", "-qm", "later")
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        clone = Path(tmp.name) / "clone"
        subprocess.run(
            ["git", "clone", "-q", "--depth", "1", f"file://{source}", str(clone)],
            check=True,
            capture_output=True,
        )
        with self.assertRaises(G.OrderingError):
            _frozen(clone)

    def test_replace_refs_refuse(self) -> None:
        # Probe B3: a replace ref rewrites what history the guard sees.
        root = _repo()
        head = _git(root, "rev-parse", "HEAD")
        _git(root, "replace", "--graft", head)
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_inherited_git_environment_is_ignored(self) -> None:
        root = _repo()
        other = _repo(layout="uncommitted")
        with mock.patch.dict("os.environ", {"GIT_DIR": str(other / ".git")}):
            self.assertEqual(len(_frozen(root)["rules_commit"]), 40)

    def test_changed_owner_decisions_refuse(self) -> None:
        root = _repo()
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 2}\n')
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_a_changed_pinned_implementation_refuses(self) -> None:
        root = _repo()
        _write(root, "impl/derivation.py", "RULE = '>'\n")
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_pins_must_cover_the_required_set_and_stay_inside(self) -> None:
        # Probe B4: a pin set that omits the derivation, or points outside.
        root = _repo(pins={"config/data_manifest.tsv": "0" * 64})
        with self.assertRaises(G.OrderingError):
            _frozen(root)
        for bad in ("/etc/hostname", "../x", "impl/../impl/derivation.py"):
            root = _repo(pins={"impl/derivation.py": "0" * 64, bad: "0" * 64})
            with self.subTest(pin=bad), self.assertRaises(G.OrderingError):
                _frozen(root)
        with self.assertRaises(G.OrderingError):
            G.assert_rules_frozen(_repo())  # default REQUIRED_PINS are not pinned

    def test_required_pins_are_the_real_import_closure(self) -> None:
        code = (
            "import sys; sys.path.insert(0, 'src');"
            "from pathlib import Path;"
            "import dt_adoc.personalization.phase2b.values,"
            " dt_adoc.personalization.phase2b.derivation,"
            " dt_adoc.personalization.phase2b.qualification;"
            "r = Path('.').resolve();"
            "print('\\n'.join(sorted(str(Path(m.__file__).resolve().relative_to(r))"
            " for n, m in sys.modules.items() if n.startswith('dt_adoc')"
            " and getattr(m, '__file__', None) and not m.__file__.endswith('__init__.py'))))"
        )
        loaded = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        code_pins = sorted(p for p in G.REQUIRED_PINS if p.endswith(".py"))
        self.assertEqual(loaded, code_pins)
        self.assertIn(str(G.OWNER_DECISIONS), G.REQUIRED_PINS)


class Identity(unittest.TestCase):
    """Probe B5/B6: no spelling of an ADOC donor or accession gets through."""

    def test_adoc_donor_spellings(self) -> None:
        for name in (
            "SZ09",
            "sz-10",
            "SZ25TE",
            "ＳＺ０９",
            "SZ٠٩",
            "ЅZ09",
            "SZ⁰⁹",
            "SZ9",
            "SZ009",
            "SZ-O9",
            "SZO10",
        ):
            with self.subTest(name=name):
                self.assertTrue(I.names_adoc_donor(name))
        for name in ("U1", "U2", "B44", "E001", "B080", "REF1"):
            with self.subTest(name=name):
                self.assertFalse(I.names_adoc_donor(name))

    def test_adoc_accession_spellings(self) -> None:
        for acc in (
            "E-MTAB-15842",
            "E-MTAB-１５８４２",
            "Ε-MTAB-15842",
            "EMTAB-015842",
            "PRJEB101736",
            "ERP183140",
            "ERR15772621",
            "SAMEA120442949",
        ):
            with self.subTest(acc=acc):
                self.assertTrue(I.names_adoc_accession(acc))
        for acc in ("E-MTAB-10283", "GSE168405", "E-MTAB-15330"):
            with self.subTest(acc=acc):
                self.assertFalse(I.names_adoc_accession(acc))

    def test_donor_ids_are_strict_and_case_folded(self) -> None:
        self.assertEqual(I.donor_key("B44"), I.donor_key("b44"))
        for bad in ("", " ", "D1 ", " D1", "D 1", "D1\t", "SZ09", "Ｄ１"):
            with self.subTest(bad=bad), self.assertRaises(I.IdentityError):
                I.donor_key(bad)


class ValueAccess(unittest.TestCase):
    """The only reader of candidate values refuses before the guard and on ADOC input."""

    TABLE = "donor_id\tklf12_count\tdepth\nR1\t0.9\t8000\nR2\t0\t9000\n"
    MD5 = "0123456789abcdef0123456789abcdef"

    def _source(
        self,
        root: Path,
        text: str | None = None,
        name: str = "ext/cells.tsv",
        **provenance: object,
    ) -> tuple[Path, Path]:
        _write(root, name, text if text is not None else self.TABLE)
        path = root / name
        record = {
            "source_accession": "E-MTAB-10283",
            "per_cell_table_sha256": G.sha256(path),
            "input_files": [
                {
                    "name": "WSSS_END9397531_R2.fastq.gz",
                    "md5": self.MD5,
                    "published_md5": self.MD5,
                }
            ],
            **provenance,
        }
        _write(root, name + ".provenance.json", json.dumps(record))
        return path, root / (name + ".provenance.json")

    def _open(self, root: Path, path: Path, sidecar: Path, digest: str | None = None):
        with mock.patch.object(G, "REQUIRED_PINS", PINS):
            return V.open_reference_values(
                root, path, digest or G.sha256(path), sidecar
            )

    def test_positive_control(self) -> None:
        root = _repo()
        proof, accession, cells = self._open(root, *self._source(root))
        self.assertEqual([c.donor_id for c in cells], ["R1", "R2"])
        self.assertEqual(accession, "E-MTAB-10283")
        self.assertIn("rules_commit", proof)

    def test_values_cannot_be_read_before_the_rules_are_committed(self) -> None:
        root = _repo(layout="uncommitted")
        path, sidecar = self._source(root)
        with (
            mock.patch.object(Path, "read_bytes", side_effect=AssertionError("read")),
            mock.patch.object(Path, "read_text", side_effect=AssertionError("read")),
            self.assertRaises(G.OrderingError),
        ):
            V.open_reference_values(root, path, "0" * 64, sidecar)

    def test_adoc_accessions_and_fastqs_are_refused(self) -> None:
        adoc_md5 = min(I.adoc_fastq_md5s())
        for provenance in (
            {"source_accession": "E-MTAB-15842"},
            {"source_accession": "E‐MTAB‐15842"},
            {"source_accession": "PRJEB101736"},
            {"source_accession": ""},
            {
                "input_files": [
                    {
                        "name": "renamed.fastq.gz",
                        "md5": adoc_md5,
                        "published_md5": adoc_md5,
                    }
                ]
            },
            {
                "input_files": [
                    {
                        "name": "SZ09TE_CNT_R1.fastq.gz",
                        "md5": self.MD5,
                        "published_md5": self.MD5,
                    }
                ]
            },
            {
                "input_files": [
                    {"name": "x.fastq.gz", "md5": self.MD5, "published_md5": "f" * 32}
                ]
            },
            {"input_files": []},
        ):
            root = _repo()
            with (
                self.subTest(provenance=provenance),
                self.assertRaises(V.ValueAccessError),
            ):
                self._open(root, *self._source(root, **provenance))

    def test_adoc_donors_and_data_paths_are_refused(self) -> None:
        for donor in ("SZ09", "ＳＺ０９", "SZ9"):
            root = _repo()
            with self.subTest(donor=donor), self.assertRaises(V.ValueAccessError):
                self._open(root, *self._source(root, self.TABLE.replace("R1", donor)))
        root = _repo()
        with self.assertRaises(V.ValueAccessError):
            self._open(root, *self._source(root, name="data/cells.tsv"))

    def test_one_donor_cannot_be_split_by_spelling(self) -> None:
        for extra in ("r1", "R1 ", " "):
            root = _repo()
            table = self.TABLE + f"{extra}\t1\t8000\n"
            with self.subTest(extra=extra), self.assertRaises(V.ValueAccessError):
                self._open(root, *self._source(root, table))

    def test_a_forbidden_or_undeclared_digest_is_refused(self) -> None:
        root = _repo()
        path, sidecar = self._source(root)
        with self.assertRaises(V.ValueAccessError):
            self._open(root, path, sidecar, "f" * 64)
        with (
            mock.patch.object(
                V, "forbidden_reference_shas", return_value=frozenset({G.sha256(path)})
            ),
            self.assertRaises(V.ValueAccessError),
        ):
            self._open(root, path, sidecar)

    def test_malformed_tables_are_refused(self) -> None:
        for table in (
            "barcode\tdonor_id\tklf12_count\tdepth\nAAAC\tR1\t1\t8000\n",
            "donor_id\tklf12_count\tdepth\nR1\t1\n",
            "donor_id\tklf12_count\tdepth\nR1\t1\t8000\textra\n",
            "donor_id\tklf12_count\tdepth\nR1\t1_0\t8000\n",
            "donor_id\tklf12_count\tdepth\nR1\t-0\t8000\n",
            "donor_id\tklf12_count\tdepth\nR1\tnan\t8000\n",
            "donor_id\tklf12_count\tdepth\nR1\t1e400\t8000\n",
            "donor_id\tklf12_count\tdepth\nR1\t1\t0\n",
            "donor_id\tklf12_count\tdepth\n",
        ):
            root = _repo()
            with self.subTest(table=table), self.assertRaises(V.ValueAccessError):
                self._open(root, *self._source(root, table))


def _row(**changes: str) -> dict[str, str]:
    rows = Q.read_inventory((ROOT / Q.INVENTORY).read_text(encoding="utf-8"))
    base = next(r for r in rows if r["candidate_id"] == "C03")
    return {**base, **changes}


class Inventory(unittest.TestCase):
    """The candidate inventory is metadata-only, and qualification is mechanical."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (ROOT / Q.INVENTORY).read_text(encoding="utf-8")
        cls.rows = Q.read_inventory(cls.text)

    def test_the_committed_inventory_validates(self) -> None:
        Q.validate_inventory(self.rows)
        self.assertNotIn("klf12", self.text.lower())

    def test_an_expression_column_is_refused_whatever_its_name(self) -> None:
        header, _, rest = self.text.partition("\n")
        for column in (
            "KLF12_mean",
            "detection_rate",
            "high_fraction",
            "q90",
            "adhesion",
        ):
            text = header + f"\t{column}\n" + rest
            with self.subTest(column=column), self.assertRaises(Q.InventoryError):
                Q.read_inventory(text)

    def test_a_klf12_mention_in_any_cell_is_refused(self) -> None:
        # Probe B9: separators and full-width forms too.
        for note in (
            "KLF12 looks high here",
            "KLF 12 in 40% of cells",
            "klf-12",
            "\uff2b\uff2c\uff26\uff11\uff12",
        ):
            with self.subTest(note=note), self.assertRaises(Q.InventoryError):
                Q.validate_inventory([_row(notes=note)])

    def test_the_adoc_dataset_and_donors_are_never_candidates(self) -> None:
        for changes in (
            {"accessions": "E-MTAB-15842"},
            {"donor_identity_source": "SZ10"},
            {"notes": "reanalysis of the E-MTAB-15842 donors"},
            {"sources": "https://www.ebi.ac.uk/ena/browser/view/PRJEB101736"},
            {"notes": "donor SZ9"},
            {"n_independent_donors_in_arm": "\u0665"},
        ):
            with self.subTest(changes=changes), self.assertRaises(Q.InventoryError):
                Q.validate_inventory([_row(**changes)])

    def test_selection_is_c03_alone_by_metadata(self) -> None:
        selected = Q.select(self.rows, min_reference_donors=3)
        self.assertEqual([r["candidate_id"] for r in selected], ["C03"])

    def test_insufficient_donors_fail(self) -> None:
        for n in ("2", "unknown"):
            with self.subTest(n=n):
                verdict, reasons = Q.qualify(
                    _row(n_independent_donors_in_arm=n), min_reference_donors=3
                )
                self.assertNotEqual(verdict, Q.QUALIFIED)
                self.assertTrue(any(r.startswith("D2") for r in reasons))

    def test_an_unmatched_or_unresolved_context_fails(self) -> None:
        for changes in (
            {"system": "tissue"},
            {"progestogen": "unknown"},
            {"camp": "no", "xav939": "no"},
            {"estrogen": "no"},
        ):
            with self.subTest(changes=changes):
                verdict, reasons = Q.qualify(_row(**changes), min_reference_donors=3)
                self.assertNotEqual(verdict, Q.QUALIFIED)
                self.assertTrue(any(r.startswith("D1") for r in reasons))

    def test_same_pipeline_is_the_only_comparability_route(self) -> None:
        for changes in (
            {"raw_fastq_open": "unknown"},
            {"chemistry": "drop_seq"},
            {"chemistry": "10x_3p_v3;smart_seq2"},
        ):
            with self.subTest(changes=changes):
                verdict, reasons = Q.qualify(_row(**changes), min_reference_donors=3)
                self.assertEqual(verdict, "EXCLUDED")
                self.assertTrue(any(r.startswith("D5") for r in reasons))

    def test_chemistry_is_a_closed_vocabulary(self) -> None:
        # Probe B9: "Smart-seq2 (not 10x)" must not pass a substring test.
        with self.assertRaises(Q.InventoryError):
            Q.validate_inventory([_row(chemistry="Smart-seq2 (not 10x)")])

    def test_fcs_linked_candidates_stay_blocked_until_disjointness_is_documented(
        self,
    ) -> None:
        self.assertEqual(
            Q.qualify(_row(fcs_linked="yes"), min_reference_donors=3)[0],
            Q.BLOCKED_DONOR_OVERLAP,
        )
        self.assertEqual(
            Q.qualify(_row(fcs_linked="unknown"), min_reference_donors=3)[0],
            Q.BLOCKED_DONOR_OVERLAP,
        )
        self.assertEqual(
            Q.qualify(
                _row(fcs_linked="yes", donor_overlap_documented_disjoint="yes"),
                min_reference_donors=3,
            )[0],
            Q.QUALIFIED,
        )

    def test_controlled_access_and_integrated_atlases_are_excluded(self) -> None:
        for changes in (
            {"controlled_access": "yes"},
            {"integrates_other_candidates": "yes"},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(
                    Q.qualify(_row(**changes), min_reference_donors=3)[0], "EXCLUDED"
                )


class Boundaries(unittest.TestCase):
    """What Phase 2B may not import, emit or claim."""

    def test_no_phase2b_module_loads_outcome_or_model_code(self) -> None:
        code = (
            "import sys; sys.path.insert(0, 'src');"
            "import dt_adoc.personalization.phase2b.audit, dt_adoc.personalization.phase2b.derivation,"
            " dt_adoc.personalization.phase2b.guard, dt_adoc.personalization.phase2b.qualification,"
            " dt_adoc.personalization.phase2b.values;"
            "print('\\n'.join(sorted(m for m in sys.modules if m.startswith('dt_adoc'))))"
        )
        loaded = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        for forbidden in (
            "dt_adoc.simulation",
            "dt_adoc.concordance",
            "dt_adoc.calibration",
            "dt_adoc.scoring",
            "dt_adoc.perturbations",
            "dt_adoc.experiments",
            "dt_adoc.observations",
        ):
            self.assertFalse(
                any(m == forbidden or m.startswith(forbidden + ".") for m in loaded),
                forbidden,
            )

    def test_no_model_probability_rate_clamp_mutation_or_topology_artifact(
        self,
    ) -> None:
        texts = {
            p.relative_to(ROOT): p.read_text(encoding="utf-8")
            for p in PHASE2B.rglob("*")
            if p.is_file()
        }
        self.assertTrue(texts)
        self.assertEqual(P.forbidden_emission(texts), [])
        for path in texts:
            self.assertNotIn(path.suffix, (".bnd", ".cfg"))
        for bad in ("initial_on_probability", "rate_modifier", "clamp", "mutation"):
            for path, text in texts.items():
                if path.suffix == ".json":
                    self.assertNotIn(f'"{bad}"', text, f"{path} has a {bad} field")

    def test_rr13_is_not_satisfied(self) -> None:
        gate = json.loads(
            (ROOT / "docs/phase2a/reference_gate.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            gate["measured_personalization_verdict"], "BLOCKED_BRIDGE_UNVALIDATED"
        )
        self.assertFalse(any("bridge_validation" in p.name for p in PHASE2B.rglob("*")))

    def test_personalization_yaml_is_not_activated(self) -> None:
        import yaml

        policy = yaml.safe_load((ROOT / P.PERSONALIZATION).read_text(encoding="utf-8"))
        self.assertIsNone(policy["reference_strategy"]["reference_path"])


class Phase2AAudit(unittest.TestCase):
    """Step 1: the starting state is audited, not repaired."""

    def test_the_committed_audit_is_current(self) -> None:
        committed = json.loads((ROOT / A.OUT).read_text(encoding="utf-8"))
        with closure_replay.git_index(CLOSURE_ENV):
            self.assertEqual(committed, A.compute(CLOSURE))

    def test_the_starting_state_is_the_one_phase2b_assumes(self) -> None:
        with closure_replay.git_index(CLOSURE_ENV):
            checks = A.compute(CLOSURE)["starting_state_checks"]
        self.assertTrue(checks and all(checks.values()), checks)

    def test_an_unapproved_frozen_change_refuses(self) -> None:
        with (
            mock.patch.object(A, "frozen_changes", return_value=["models/x.bnd"]),
            closure_replay.git_index(CLOSURE_ENV),
            self.assertRaises(A.AuditError),
        ):
            A.compute(CLOSURE)

    def test_an_approved_path_with_other_content_refuses(self) -> None:
        # Probe B8: approval is bound to the approved bytes, not to the path.
        path = "src/dt_adoc/personalization/phase2a_contract.py"
        altered = {**A.OWNER_APPROVED_CHANGES, path: ("D2", "0" * 64)}
        with (
            mock.patch.object(A, "OWNER_APPROVED_CHANGES", altered),
            closure_replay.git_index(CLOSURE_ENV),
            self.assertRaises(A.AuditError),
        ):
            A.compute(CLOSURE)

    def test_a_new_file_under_a_frozen_prefix_is_a_change(self) -> None:
        # Probe B8: files absent at the base were invisible before.
        real = A._present_now(ROOT)
        with mock.patch.object(
            A, "_present_now", return_value=real | {"models/new.bnd"}
        ):
            self.assertIn("models/new.bnd", A.frozen_changes(ROOT))


class RulesPreregistration(unittest.TestCase):
    """The repository's own rules agree with the code they freeze, by CONTENT.

    Whether the guard passes depends on the history of whichever checkout runs
    it (the review snapshot is a synthetic two-commit history in which no real
    rules commit is an ancestor), so no test asserts it; the guard is enforced
    at run time by values.open_reference_values, in the real checkout.
    """

    def test_the_rules_agree_with_the_code_they_freeze(self) -> None:
        path = ROOT / G.PREREG_JSON
        if not path.exists():
            self.skipTest("rules not written yet")
        number = 1
        while (ROOT / G.amendment_files(number)[0]).exists():
            path = ROOT / G.amendment_files(number)[0]
            number += 1
        rules = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(rules["pinned_implementation_sha256"]), sorted(G.REQUIRED_PINS)
        )
        # By content, so it holds in any checkout: a pinned file changed without
        # a governing amendment would make every guarded value read refuse.
        for relative, digest in sorted(rules["pinned_implementation_sha256"].items()):
            self.assertEqual(G.sha256(ROOT / relative), digest, f"{path}: {relative}")
        for name in (
            "owner_decisions",
            "candidate_inventory",
            "adoc_identity_denylist",
        ):
            frozen = rules["inputs_frozen"][name]
            self.assertEqual(G.sha256(ROOT / frozen["path"]), frozen["sha256"], name)
        spec = json.loads(
            (ROOT / "docs/phase2a/mapping_specification.json").read_text()
        )
        self.assertEqual(
            rules["inputs_frozen"]["min_reference_donors"]["value"],
            spec["parameters"]["min_reference_donors"]["value"],
        )
        inventory = Q.read_inventory((ROOT / Q.INVENTORY).read_text(encoding="utf-8"))
        selected = Q.select(inventory, min_reference_donors=3)
        self.assertEqual(
            [
                c["candidate_id"]
                for c in rules["candidate_selection"]["selected_in_order"]
            ],
            [r["candidate_id"] for r in selected],
        )
        constants = rules["derivation"]["constants"]
        for name in (
            "MIN_DETECTED_CELLS",
            "NULL_REPLICATES",
            "NULL_SEED",
            "RULE",
        ):
            self.assertEqual(constants[name], getattr(D, name), name)
        self.assertEqual(constants["POSTERIOR_LEVELS"], list(D.POSTERIOR_LEVELS))
        self.assertEqual(
            rules["derivation"]["variant_selection"], "all_reported_none_selected"
        )
        citation = rules["rr14_citations"]["threshold_derivation"]
        self.assertTrue("repo:" in citation or "NONE VALID" in citation, citation)


class SecondProbeRegressions(unittest.TestCase):
    """Bypasses found by the second adversarial probe, each now refused."""

    def test_separator_and_lookalike_donor_spellings(self) -> None:
        for name in (
            "SZ9_2",
            "SZ9-2",
            "SZ9.10",
            "SZ009.1",
            "SZ010.1",
            "SZ025_2",
            "SZI0",
            "SZl0",
            "5Z09",
            "S209",
        ):
            with self.subTest(name=name):
                self.assertTrue(I.names_adoc_donor(name))
                with self.assertRaises(I.IdentityError):
                    I.donor_key(name)
        for name in ("U1", "U2", "B44", "E001", "B080"):
            with self.subTest(name=name):
                self.assertEqual(I.donor_key(name), name.casefold())

    def test_lookalike_accession_spellings(self) -> None:
        for acc in ("PRJEB1O1736", "ERR1577262l", "E-MTAB-l5842"):
            with self.subTest(acc=acc):
                self.assertTrue(I.names_adoc_accession(acc))

    def test_duplicate_provenance_keys_and_malformed_names(self) -> None:
        values = ValueAccess()
        root = _repo()
        path, sidecar = values._source(root)
        text = sidecar.read_text(encoding="utf-8")
        sidecar.write_text(
            text.replace(
                '"source_accession"',
                '"source_accession": "E-MTAB-15842", "source_accession"',
                1,
            ),
            encoding="utf-8",
        )
        with self.assertRaises(V.ValueAccessError):
            values._open(root, path, sidecar)
        for name in (None, 7, ""):
            root = _repo()
            files = [{"name": name, "md5": values.MD5, "published_md5": values.MD5}]
            with self.subTest(name=name), self.assertRaises(V.ValueAccessError):
                values._open(root, *values._source(root, input_files=files))

    def test_a_draft_elsewhere_in_docs_phase2b_refuses(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        _git(root, "init", "-q", "-b", "main")
        _write(root, "impl/derivation.py", "RULE = '>='\n")
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "decisions")
        _write(root, "docs/phase2b/draft_rules.md", "# v1\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "draft")
        _git(root, "rm", "-q", "docs/phase2b/draft_rules.md")
        _git(root, "commit", "-qm", "drop draft")
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
        _write(
            root, str(G.PREREG_JSON), json.dumps({"pinned_implementation_sha256": pins})
        )
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules")
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_a_case_variant_or_unmerged_draft_refuses(self) -> None:
        for layout in ("case", "branch"):
            root = _repo()
            _git(root, "checkout", "-qb", "side", "HEAD~1")
            name = (
                "docs/phase2b/Preregistration.md"
                if layout == "case"
                else str(G.PREREG_MD)
            )
            _write(root, name, "# v0\n")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "draft")
            _git(root, "checkout", "-q", "main")
            with self.subTest(layout=layout), self.assertRaises(G.OrderingError):
                _frozen(root)

    def test_later_phase2b_work_does_not_trip_the_draft_check(self) -> None:
        root = _repo()
        _write(root, "docs/phase2b/qualification_table.tsv", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "C4")
        self.assertEqual(len(_frozen(root)["rules_commit"]), 40)

    def test_ignored_files_and_symlinks_under_frozen_prefixes_are_changes(self) -> None:
        real = A._present_now(ROOT)
        with mock.patch.object(
            A, "_present_now", return_value=real | {"models/results/x.bnd"}
        ):
            self.assertIn("models/results/x.bnd", A.frozen_changes(ROOT))
        target = "src/dt_adoc/personalization/phase2a_contract.py"
        with mock.patch.object(
            A, "_links_inside", side_effect=lambda r, rel: rel == target
        ):
            self.assertIn(target, A.frozen_changes(ROOT))
            self.assertIn(target, A.unapproved(ROOT, [target]))

    def test_a_real_symlink_swap_is_a_change_and_a_mirror_is_not(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        base = Path(tmp.name)
        repo = base / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _write(repo, "models/x.bnd", "rule\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "x")
        outside = base / "outside.bnd"
        outside.write_text("rule\n", encoding="utf-8")
        (repo / "models/x.bnd").unlink()
        (repo / "models/x.bnd").symlink_to(outside)
        self.assertTrue(A._links_inside(repo, "models/x.bnd"))
        (repo / "models/x.bnd").unlink()
        _write(repo, "models/x.bnd", "rule\n")
        mirror = base / "mirror"
        mirror.mkdir()
        (mirror / ".git").symlink_to(repo / ".git")
        (mirror / "models").symlink_to(repo / "models")
        self.assertFalse(A._links_inside(repo, "models/x.bnd"))
        self.assertFalse(A._links_inside(mirror, "models/x.bnd"))

    def test_select_validates_the_inventory_itself(self) -> None:
        rows = [_row(notes="KLF12 high")]
        with self.assertRaises(Q.InventoryError):
            Q.select(rows, min_reference_donors=3)


class Amendments(unittest.TestCase):
    """A value-blind amendment may re-pin the code; only before any value work."""

    def _amend(self, root: Path, number: int, *, extra: str | None = None) -> None:
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
        js, md = G.amendment_files(number)
        _write(root, str(js), json.dumps({"pinned_implementation_sha256": pins}))
        _write(root, str(md), f"# amendment {number}\n")
        if extra:
            _write(root, extra, "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", f"amendment {number}")

    def _fix_code(self, root: Path) -> None:
        _write(root, "impl/derivation.py", "RULE = '>='  # fixed\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "fix")

    def test_positive_control(self) -> None:
        root = _repo()
        self._fix_code(root)
        with self.assertRaises(G.OrderingError):
            _frozen(root)  # the old pins no longer hold
        self._amend(root, 1)
        proof = _frozen(root)
        self.assertTrue(proof["amendments"].startswith("01:"))
        self.assertEqual(proof["governing_pins"], str(G.amendment_files(1)[0]))

    def test_an_amendment_after_value_work_is_refused(self) -> None:
        root = _repo()
        _write(root, "docs/phase2b/derivation_result.json", "{}\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "values")
        self._fix_code(root)
        self._amend(root, 1)
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_regenerating_the_value_blind_audit_between_stages_is_allowed(self) -> None:
        root = _repo()
        _write(root, "docs/phase2b/phase2a_audit.json", "{}\n")
        self._fix_code(root)
        self._amend(root, 1)
        self.assertTrue(_frozen(root)["amendments"].startswith("01:"))

    def test_an_amendment_must_be_its_own_commit_and_numbered(self) -> None:
        root = _repo()
        self._fix_code(root)
        self._amend(root, 1, extra="impl/other.py")
        with self.assertRaises(G.OrderingError):
            _frozen(root)
        root = _repo()
        self._fix_code(root)
        self._amend(root, 2)
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_an_edited_amendment_is_refused(self) -> None:
        root = _repo()
        self._fix_code(root)
        self._amend(root, 1)
        _write(root, str(G.amendment_files(1)[1]), "# changed\n")
        with self.assertRaises(G.OrderingError):
            _frozen(root)


def _stateless(
    name: str,
    seed: int,
    *,
    depths: str = "lognormal",
    shape: float | None = None,
    dropout: bool = False,
    n: int = 700,
    mean: float = 0.6,
) -> D.DonorCells:
    """One latent state only, with a named confounder: depth batches, depth-driven
    dropout, or negative-binomial overdispersion (gamma-Poisson of `shape`)."""
    draw = random.Random(seed)
    counts, depths_out = [], []
    for index in range(n):
        if depths == "lognormal":
            depth = draw.lognormvariate(math.log(8000), 0.4)
        else:  # "batch2" / "batch4": two libraries at a 2x or 4x depth ratio
            ratio = 2.0 if depths == "batch2" else 4.0
            depth = draw.lognormvariate(
                math.log(8000 * (ratio if index % 2 else 1.0)), 0.2
            )
        rate = mean * depth / 8000
        if shape is not None:
            rate = draw.gammavariate(shape, rate / shape)
        k = D._poisson(rate, draw)
        if dropout:
            keep = min(1.0, depth / 16000)
            k = sum(1 for _ in range(k) if draw.random() < keep)
        counts.append(k * draw.gauss(0.92, 0.05) if k else 0.0)
        depths_out.append(depth)
    return D.DonorCells(name, tuple(counts), tuple(depths_out))


class OperatingCharacteristics(unittest.TestCase):
    """The pre-registration's stateless-confounder claims, backed by committed runs."""

    def _never(self, **kwargs: object) -> None:
        donors = [_stateless(f"OC{i}", 100 + i, **kwargs) for i in range(3)]
        self.assertEqual(
            D.derive(donors, min_reference_donors=3)["verdict"], D.NOT_QUALIFIED
        )

    def test_depth_batches_at_2x_and_4x_do_not_qualify(self) -> None:
        for depths in ("batch2", "batch4"):
            with self.subTest(depths=depths):
                self._never(depths=depths)

    def test_depth_dependent_dropout_does_not_qualify(self) -> None:
        self._never(dropout=True)

    def test_negative_binomial_overdispersion_does_not_qualify(self) -> None:
        for shape in (0.5, 1.0, 2.0):
            with self.subTest(shape=shape):
                self._never(shape=shape)


class MergedHistory(unittest.TestCase):
    """Amendment 07: an ordinary --no-ff merge of the branch that froze the
    rules is not a second write; a merge that brings its own bytes still is."""

    def _merged(self) -> tuple[Path, str]:
        """Decisions on main; rules, a code fix and amendment 01 on a branch;
        main merged with --no-ff although it could fast-forward (PR #8's shape)."""
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        _git(root, "init", "-q", "-b", "main")
        _write(root, "impl/derivation.py", "RULE = '>='\n")
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "decisions")
        _git(root, "checkout", "-qb", "feature")
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
        _write(
            root, str(G.PREREG_JSON), json.dumps({"pinned_implementation_sha256": pins})
        )
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules")
        amend = Amendments()
        amend._fix_code(root)
        amend._amend(root, 1)
        _git(root, "checkout", "-q", "main")
        _git(root, "merge", "-q", "--no-ff", "feature", "-m", "merge")
        return root, _git(root, "rev-parse", "HEAD")

    def test_a_no_ff_merge_of_the_frozen_branch_passes(self) -> None:
        root, merge = self._merged()
        self.assertFalse(G._writes(root, merge, G.PREREG_JSON))
        self.assertTrue(_frozen(root)["amendments"].startswith("01:"))

    def test_an_amendment_after_the_merge_still_chains(self) -> None:
        root, _ = self._merged()
        _write(root, "impl/derivation.py", "RULE = '>='  # fixed again\n")
        _git(root, "commit", "-qam", "fix 2")
        Amendments()._amend(root, 2)
        proof = _frozen(root)
        self.assertEqual(
            [part.split(":")[0] for part in proof["amendments"].split(";")],
            ["01", "02"],
        )
        self.assertEqual(proof["governing_pins"], str(G.amendment_files(2)[0]))

    def _merge_with(self, change) -> tuple[Path, str]:
        """A true two-sided merge of the frozen rules, `change` applied inside it."""
        root = _repo()
        _git(root, "checkout", "-qb", "side")
        _write(root, "side.txt", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "side")
        _git(root, "checkout", "-q", "main")
        _write(root, "main.txt", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "main")
        _git(root, "merge", "-q", "--no-ff", "--no-commit", "side")
        change(root)
        _git(root, "commit", "-qm", "merge")
        return root, _git(root, "rev-parse", "HEAD")

    def test_an_evil_merge_writing_new_bytes_refuses(self) -> None:
        def rewrite(root: Path) -> None:
            _write(root, str(G.PREREG_MD), "# rules, tuned inside the merge\n")
            _git(root, "add", "-A")

        root, merge = self._merge_with(rewrite)
        self.assertTrue(G._writes(root, merge, G.PREREG_MD))
        self.assertTrue(G._writes(root, merge, G.PREREG_MD, inherited_absence=True))
        # Restoring the frozen bytes afterwards does not hide the merge's write.
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "commit", "-qam", "restore")
        with self.assertRaisesRegex(G.OrderingError, "written by 3 commits"):
            _frozen(root)

    def test_a_merge_that_drops_the_file_writes_it(self) -> None:
        def drop(root: Path) -> None:
            _git(root, "rm", "-q", str(G.PREREG_MD))

        root, merge = self._merge_with(drop)
        # Both parents hold the file: a write under either rule.
        self.assertTrue(G._writes(root, merge, G.PREREG_MD))
        self.assertTrue(G._writes(root, merge, G.PREREG_MD, inherited_absence=True))
        with self.assertRaises(G.OrderingError):
            _frozen(root)

    def test_a_merge_changing_only_the_mode_writes_it(self) -> None:
        def chmod(root: Path) -> None:
            (root / G.PREREG_MD).chmod(0o755)
            _git(root, "add", "-A")

        root, merge = self._merge_with(chmod)
        self.assertTrue(G._writes(root, merge, G.PREREG_MD))
        self.assertTrue(G._writes(root, merge, G.PREREG_MD, inherited_absence=True))

    def _branch_commit(self, root: Path, branch: str, name: str) -> None:
        _git(root, "checkout", "-q", branch)
        _write(root, name, "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", name)

    def _second_amendment(self, root: Path) -> None:
        _write(root, "impl/derivation.py", "RULE = '>='  # fixed again\n")
        _git(root, "commit", "-qam", "fix 2")
        Amendments()._amend(root, 2)

    def test_an_evil_merge_writing_between_amendments_refuses(self) -> None:
        # Amendment 10: the merge itself adds a value-derived file that neither
        # parent holds; diff-tree without -m lists nothing for a merge.
        root = _repo()
        amend = Amendments()
        amend._fix_code(root)
        amend._amend(root, 1)
        _git(root, "checkout", "-qb", "side")
        self._branch_commit(root, "side", "side.txt")
        self._branch_commit(root, "main", "main.txt")
        _git(root, "merge", "-q", "--no-ff", "--no-commit", "side")
        _write(root, "docs/phase2b/derivation_result.json", "{}\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "merge, carrying values")
        merge = _git(root, "rev-parse", "HEAD")
        for parent in ("HEAD^1", "HEAD^2"):
            self.assertIsNone(
                G._tree_entry(
                    root,
                    _git(root, "rev-parse", parent),
                    Path("docs/phase2b/derivation_result.json"),
                )
            )
        result = Path("docs/phase2b/derivation_result.json")
        self.assertTrue(G._writes(root, merge, result))
        self.assertTrue(G._writes(root, merge, result, inherited_absence=True))
        self._second_amendment(root)
        with self.assertRaisesRegex(G.OrderingError, "written between"):
            _frozen(root)

    def test_a_merge_carrying_a_deletion_between_amendments_passes(self) -> None:
        # Amendment 12 (the between check only): main deleted a pre-rules
        # docs/phase2b/ file before the rules; a branch cut before that
        # deletion, merged between amendments, leaves the merge with main's
        # absence of the file. That inherited absence is not a new write.
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        inventory = Path("docs/phase2b/candidate_inventory.tsv")
        _git(root, "init", "-q", "-b", "main")
        _write(root, "impl/derivation.py", "RULE = '>='\n")
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
        _write(root, str(inventory), "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "decisions and inventory")
        _git(root, "branch", "old")
        _git(root, "rm", "-q", str(inventory))
        _git(root, "commit", "-qm", "drop the inventory")
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
        _write(
            root, str(G.PREREG_JSON), json.dumps({"pinned_implementation_sha256": pins})
        )
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules")
        amend = Amendments()
        amend._fix_code(root)
        amend._amend(root, 1)
        self._branch_commit(root, "old", "old.txt")
        _git(root, "checkout", "-q", "main")
        _git(root, "merge", "-q", "--no-ff", "old", "-m", "merge old")
        merge = _git(root, "rev-parse", "HEAD")
        self.assertFalse(G._writes(root, merge, inventory, inherited_absence=True))
        # _only_commit's rule (amendment 07) still calls a merge deletion a write.
        self.assertTrue(G._writes(root, merge, inventory))
        self._second_amendment(root)
        self.assertEqual(_frozen(root)["governing_pins"], str(G.amendment_files(2)[0]))

    def test_only_commit_counts_a_merge_deletion_of_a_frozen_file(self) -> None:
        # Amendment 07's frozen rule, restored by amendment 12: a merge that
        # drops a frozen file is a write for _only_commit, even when the other
        # parent (here an unrelated root) never held the file.
        root = _repo()
        _git(root, "checkout", "-q", "--orphan", "bare")
        _git(root, "rm", "-rqf", ".")
        _write(root, "bare.txt", "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "unrelated root")
        _git(root, "checkout", "-q", "main")
        _git(
            root,
            "merge",
            "-q",
            "--no-ff",
            "--no-commit",
            "--allow-unrelated-histories",
            "bare",
        )
        _git(root, "rm", "-q", str(G.PREREG_MD))
        _git(root, "commit", "-qm", "merge, dropping the rules text")
        merge = _git(root, "rev-parse", "HEAD")
        self.assertTrue(G._writes(root, merge, G.PREREG_MD))
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "restore")
        with self.assertRaisesRegex(G.OrderingError, "written by 3 commits"):
            G._only_commit(root, G.PREREG_MD)

    def _inventory_repo(self) -> tuple[Path, Path]:
        """Decisions and a pre-rules inventory, then the rules, then amendment 01."""
        tmp = tempfile.TemporaryDirectory()
        _TMPS.append(tmp)
        root = Path(tmp.name)
        inventory = Path("docs/phase2b/candidate_inventory.tsv")
        _git(root, "init", "-q", "-b", "main")
        _write(root, "impl/derivation.py", "RULE = '>='\n")
        _write(root, str(G.OWNER_DECISIONS), '{"D2": 3}\n')
        _write(root, str(inventory), "x\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "decisions and inventory")
        pins = {"impl/derivation.py": G.sha256(root / "impl/derivation.py")}
        _write(
            root, str(G.PREREG_JSON), json.dumps({"pinned_implementation_sha256": pins})
        )
        _write(root, str(G.PREREG_MD), "# rules\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "rules")
        amend = Amendments()
        amend._fix_code(root)
        amend._amend(root, 1)
        return root, inventory

    def test_a_merge_deleting_a_file_every_parent_holds_between_amendments_refuses(
        self,
    ) -> None:
        # The between check: a deletion inside a merge, of a docs/phase2b/ file
        # both parents hold, is a write between stages.
        for drop in (False, True):
            with self.subTest(drop=drop):
                root, inventory = self._inventory_repo()
                _git(root, "checkout", "-qb", "side")
                self._branch_commit(root, "side", "side.txt")
                self._branch_commit(root, "main", "main.txt")
                _git(root, "merge", "-q", "--no-ff", "--no-commit", "side")
                if drop:
                    _git(root, "rm", "-q", str(inventory))
                _git(root, "commit", "-qm", "merge")
                merge = _git(root, "rev-parse", "HEAD")
                self._second_amendment(root)
                if not drop:  # positive control: the same history, no deletion
                    self.assertEqual(
                        _frozen(root)["governing_pins"], str(G.amendment_files(2)[0])
                    )
                    continue
                self.assertTrue(
                    G._writes(root, merge, inventory, inherited_absence=True)
                )
                with self.assertRaisesRegex(G.OrderingError, "amendment 02"):
                    _frozen(root)

    def test_a_merge_of_an_older_branch_between_amendments_passes(self) -> None:
        # The merge carries amendment 01's files relative to its older parent
        # but writes nothing itself; a plain -m listing would refuse it.
        root = _repo()
        _git(root, "checkout", "-qb", "old")
        self._branch_commit(root, "old", "old.txt")
        _git(root, "checkout", "-q", "main")
        amend = Amendments()
        amend._fix_code(root)
        amend._amend(root, 1)
        _git(root, "merge", "-q", "--no-ff", "old", "-m", "merge old")
        merge = _git(root, "rev-parse", "HEAD")
        carried = _git(
            root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-m", merge
        ).splitlines()
        self.assertIn(str(G.amendment_files(1)[0]), carried)
        self._second_amendment(root)
        proof = _frozen(root)
        self.assertEqual(proof["governing_pins"], str(G.amendment_files(2)[0]))


class FrozenCitation(unittest.TestCase):
    """Amendment 05: the C5 threshold_derivation citation is frozen and verifies;
    amendment 04 stays the implementation-pin authority."""

    def setUp(self) -> None:
        path = ROOT / G.amendment_files(5)[0]
        if not path.exists():
            self.skipTest("amendment 05 not written")
        self.a05 = json.loads(path.read_text(encoding="utf-8"))
        self.a04 = json.loads(
            (ROOT / G.amendment_files(4)[0]).read_text(encoding="utf-8")
        )

    def test_amendment_05_carries_amendment_04_pins_verbatim(self) -> None:
        self.assertEqual(
            self.a05["pinned_implementation_sha256"],
            self.a04["pinned_implementation_sha256"],
        )
        authority = self.a05["implementation_pin_authority"]
        self.assertEqual(authority["amendment"], 4)
        self.assertEqual(G.sha256(ROOT / authority["path"]), authority["sha256"])

    def test_the_frozen_citation_names_amendment_03_and_verifies(self) -> None:
        frozen = self.a05["frozen_threshold_derivation_citation"]
        self.assertEqual(frozen["commit"], "d5db35ded71b68b0dd4ceb38ff605de2bb0fde75")
        self.assertEqual(frozen["path"], str(G.amendment_files(3)[0]))
        self.assertEqual(G.sha256(ROOT / frozen["path"]), frozen["sha256"])
        self.assertEqual(
            frozen["value"],
            f"repo:{frozen['path']}@{frozen['commit']}#sha256:{frozen['sha256']}",
        )
        self.assertEqual(
            self.a05["rr14_citations"]["threshold_derivation"], frozen["value"]
        )
        # By content, never by ancestry: the cited commit holds exactly these
        # bytes at that path (the object is readable in any clone of this
        # repository, including the review snapshot).
        held = subprocess.run(
            ["git", "-C", str(ROOT), "show", f"{frozen['commit']}:{frozen['path']}"],
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(hashlib.sha256(held).hexdigest(), frozen["sha256"])
        self.assertTrue(P._REPO_CITATION.match(frozen["value"]))


class ThirdReviewRegressions(unittest.TestCase):
    """Independent-review blockers B3-B5, each now refused or corrected."""

    def test_the_null_rate_reproduces_the_expected_detection_fraction(self) -> None:
        equal = [8000.0] * 100
        rate = D.calibrated_rate(equal, 0.5)
        self.assertAlmostEqual(D.expected_detection(equal, rate), 0.5, places=9)
        draw = random.Random(7)
        spread = [draw.lognormvariate(math.log(8000), 0.5) for _ in range(500)]
        for fraction in (0.02, 0.1, 0.25, 0.5, 0.75, 0.9, 0.98):
            with self.subTest(fraction=fraction):
                rate = D.calibrated_rate(spread, fraction)
                self.assertAlmostEqual(
                    D.expected_detection(spread, rate), fraction, places=9
                )

    def test_the_overflow_safe_fit_is_the_frozen_fit(self) -> None:
        from dt_adoc.scrna import klf12_state

        draw = random.Random(3)
        for trial in range(6):
            values = [
                draw.lognormvariate(0.0 if draw.random() < 0.6 else 2.0, 0.4)
                for _ in range(300)
            ]
            with self.subTest(trial=trial):
                self.assertEqual(
                    json.dumps(D.fit_mixture(values), sort_keys=True),
                    json.dumps(
                        klf12_state.fit_two_component_mixture(values), sort_keys=True
                    ),
                )
        self.assertEqual(D._SaturatingMath.exp(1e6), math.inf)
        self.assertIs(klf12_state.math, math)  # restored after every fit

    def test_a_report_only_overflow_returns_a_fit_through_fit_mixture(self) -> None:
        # Deterministic input on which the FROZEN fitter overflows: two
        # equal-width log clusters make the second posterior crossing lie so
        # far out that exp() of it overflows after EM has converged.
        from dt_adoc.scrna import klf12_state

        draw = random.Random(85)
        values = [math.exp(draw.gauss(0.0, 0.3)) for _ in range(40)] + [
            math.exp(draw.gauss(3.0, 0.3)) for _ in range(40)
        ]
        with self.assertRaises(OverflowError):
            klf12_state.fit_two_component_mixture(values)
        self.assertIs(klf12_state.math, math)
        fit = D.fit_mixture(values)
        self.assertIs(klf12_state.math, math)  # restored after the overflowing fit
        self.assertTrue(fit["ordered_separation"])
        self.assertIn(math.inf, fit["posterior_crossings_value"])
        self.assertTrue(math.isfinite(fit["boundary_value"]))
        verdict = D.separation(values, floor=0.5)
        self.assertNotEqual(verdict.get("reason"), "fit_failed")

    def test_an_uncalibratable_detection_fraction_fails_s5_closed(self) -> None:
        self.assertIsNone(D.calibrated_rate([8000.0] * 10, 1.0))
        self.assertIsNone(D.calibrated_rate([8000.0] * 10, 0.0))
        everywhere = D.DonorCells("ALL1", tuple([2.0] * 50), tuple([8000.0] * 50))
        null = D.null_specificity(everywhere, D.PRIMARY_QUANTITY, 5.0)
        self.assertFalse(null["passes"])

    def test_unknown_cocktail_components_never_qualify_as_t2(self) -> None:
        for extras in (
            ("yes", "unknown"),
            ("unknown", "yes"),
            ("unknown", "unknown"),
            ("no", "unknown"),
        ):
            with self.subTest(extras=extras):
                row = _row(camp=extras[0], xav939=extras[1])
                self.assertEqual(Q.protocol_tier(row), Q.TIER_UNRESOLVED)
                verdict, reasons = Q.qualify(row, min_reference_donors=3)
                self.assertNotEqual(verdict, Q.QUALIFIED)
                self.assertTrue(any(r.startswith("D1") for r in reasons))
        self.assertEqual(
            Q.protocol_tier(_row(camp="yes", xav939="no")), Q.TIER_ONE_MISSING
        )
        self.assertEqual(
            Q.protocol_tier(_row(camp="no", xav939="yes")), Q.TIER_ONE_MISSING
        )

    def test_a_count_above_its_cells_depth_is_refused(self) -> None:
        with self.assertRaises(V.ValueAccessError):
            V.parse_per_cell(b"donor_id\tklf12_count\tdepth\nR1\t9001\t9000\n")
        cells = V.parse_per_cell(b"donor_id\tklf12_count\tdepth\nR1\t9000\t9000\n")
        self.assertEqual(cells[0].counts, (9000.0,))


if __name__ == "__main__":
    unittest.main()
