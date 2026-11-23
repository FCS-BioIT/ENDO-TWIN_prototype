"""Per-module cost from an audit suite profile, tests and class fixtures together.

Usage: python src/scripts/summarize_profile_modules.py <profile.json[.gz]> <module>...

A profile (e.g. docs/verification/benchmark_raw/baseline_3474s_audit_9b9bf5b_
profile.json.gz) records each test's ``wall`` under ``tests`` and each
setUpClass/tearDownClass under ``fixtures``. A module's cost is the sum of
both: the per-test walls alone leave out the class fixtures.
"""

import gzip
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
raw = path.read_bytes()
profile = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
rows = {}
for module in sys.argv[2:]:
    tests = sum(
        v["wall"] for k, v in profile["tests"].items() if k.startswith(module + ".")
    )
    fixtures = sum(
        x["s"] for x in profile["fixtures"] if x["label"].startswith(module + ".")
    )
    rows[module] = {
        "tests_s": round(tests, 1),
        "fixtures_s": round(fixtures, 1),
        "total_s": round(tests + fixtures, 1),
    }
total = round(sum(r["total_s"] for r in rows.values()), 1)
print(
    json.dumps(
        {
            "run_s": round(profile["run_s"], 1),
            "modules": rows,
            "total_s": total,
            "share_of_run": round(total / profile["run_s"], 3),
        },
        indent=1,
    )
)
