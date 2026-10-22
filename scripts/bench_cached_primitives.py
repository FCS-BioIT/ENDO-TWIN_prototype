"""Focused benchmarks of the two cached primitives (docs/verification/cache_design.md).

Usage: python -B scripts/bench_cached_primitives.py <tree> <label>

<tree> is any directory holding ``src/`` and ``models/``: this checkout for
"after", or an extract of the pre-cache commit for "before", e.g.

    git archive 87c56ab src models | tar -x -C <dir>

It imports ``dt_adoc`` from ``<tree>/src`` and times, best and median of five
warm repetitions: ``engine._value`` on 200 seeded assignments of every rule
row in every ``network.bnd`` and ``rule_variants.tsv`` under ``models/``
(generated subvariants included); ``runtime._provenance_payload`` on every
``provenance.toml`` under ``models/``, 50 times; and ``resolve_model`` of v0.6.0, 50
times. Timings depend on the machine; the record in
docs/verification/cache_benchmark_record.json says which one.
"""

import csv
import json
import platform
import random
import statistics
import sys
import time
from pathlib import Path

root = Path(sys.argv[1]).resolve()
label = sys.argv[2]
sys.path.insert(0, str(root / "src"))

from dt_adoc.maboss_adapter import LOGIC_LINE_RE
from dt_adoc.model import runtime
from dt_adoc.perturbations import engine

# Every rule row of every committed model: each network.bnd under models/,
# generated subvariants included, and each rule_variants.tsv expression.
texts = []
for bnd in sorted(root.glob("models/**/network.bnd")):
    texts += [
        m.group(2) for m in LOGIC_LINE_RE.finditer(bnd.read_text(encoding="utf-8"))
    ]
for table in sorted(root.glob("models/**/rule_variants.tsv")):
    with table.open(encoding="utf-8", newline="") as handle:
        texts += [row["expression"] for row in csv.DictReader(handle, delimiter="\t")]
rules = [engine._evaluable(text.strip()) for text in texts]

rng = random.Random(20261016)
points = []
for expression, names in rules:
    ordered = sorted(names)
    for _ in range(200):
        points.append((expression, {n: rng.random() < 0.5 for n in ordered}))


def best(fn, repeats=5):
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return min(times), statistics.median(times)


def run_values():
    for expression, assignment in points:
        engine._value(expression, assignment)


provenances = sorted(root.glob("models/**/provenance.toml"))


def run_payloads():
    for _ in range(50):
        for path in provenances:
            runtime._provenance_payload(path)


def run_resolve():
    for _ in range(50):
        runtime.resolve_model("adoc-literature-superset-v0.6.0", root)


out = {
    "label": label,
    "python": sys.version.split()[0],
    "machine": platform.machine(),
    "rule_rows": len(texts),
    "distinct_rules": len(set(texts)),
    "provenance_files": len(provenances),
    "value_calls": len(points),
    "payload_calls": 50 * len(provenances),
    "resolve_calls": 50,
}
for name, fn in (
    ("value", run_values),
    ("payload", run_payloads),
    ("resolve", run_resolve),
):
    fn()  # warm
    low, median = best(fn)
    out[name] = {"best_s": low, "median_s": median}
print(json.dumps(out, indent=1))
