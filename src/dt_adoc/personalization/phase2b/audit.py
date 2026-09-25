"""Phase 2B step 1: audit the Phase-2A starting state, and prove what changed since.

Reads Phase-2A artifacts at the pinned Phase-2B base commit (`BASE_COMMIT`,
main at the start of Phase 2B) and in the working tree. It repairs nothing. It
records:

- the Phase-2A facts Phase 2B starts from (only `E_KLF12_HIGH` eligible,
  numerical personalization blocked, `min_reference_donors` unset, CNT
  unresolved, RR13 separate from the scenario gate);
- the same facts now;
- every frozen file (Phase 1B, Phase 2A, v0.5.1 models, the KLF12
  pre-registration, `config/`) that differs from its base bytes. Each one must
  be on `OWNER_APPROVED_CHANGES`, the owner's 2026-09-25 RR11 update (D2),
  or the audit refuses to build.

Value-blind: no expression file is opened.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from dt_adoc.personalization import phase2a_contract as P

REPO = Path(__file__).resolve().parents[4]
TASK = "build-phase2b-audit"
OUT = Path("docs/phase2b/phase2a_audit.json")

#: main when Phase 2B started (Merge of PR #7, Phase 2A).
BASE_COMMIT = "51b8bd11bc797e4867b895d2c9df3417be422fe3"

FROZEN_PREFIXES = (
    "docs/phase2a/",
    "docs/phase1b_closure/",
    "docs/scrna/",
    "docs/experiments/",
    "models/",
    "config/",
    "src/dt_adoc/personalization/phase2a_contract.py",
)

#: D2 (owner, 2026-09-25): set min_reference_donors = 3, owner_decided, in the
#: canonical Phase-2A specification before any value is read, and regenerate.
#: Each approval is bound to the exact bytes approved, not to the path: any
#: other content at these paths is an unapproved change.
OWNER_APPROVED_CHANGES = {
    "src/dt_adoc/personalization/phase2a_contract.py": (
        (
            "D2: min_reference_donors = 3, owner_decided; and the owner's RR14"
            " schema change (amendments 03-04): a custom threshold method may cite"
            " a repository-local artifact by commit, path and sha256"
        ),
        "55a743e8940f34d61e012425b528ba13823674d41bc8dbff67a3333b5ea9d053",
    ),
    "docs/phase2a/reference_requirements.tsv": (
        "RR14 schema change (owner, amendment 03): regenerated requirement text",
        "c7d9a1991449c8c7c7bde315290053a33338d2bb20850ad74ac9059844415868",
    ),
    "docs/phase2a/mapping_specification.json": (
        "D2: regenerated specification",
        "6eaccfdad32ed8c708691c1ca2736b09cb902544aaee433ae0df5d418382b482",
    ),
    "docs/phase2a/reference_gate.json": (
        "D2: regenerated gate (RR11 no longer unmet)",
        "ca8a984bc455a6517c0f8229117bf891165a0fe603364e9774a006e286d6583b",
    ),
    "docs/phase2a/phase2a_status.json": (
        "D2: regenerated status (decision moved from open to applied)",
        "db5507576480e7cb657e45637b4f167d8ceb63e0177e0680fcbcfd1de2ebdd15",
    ),
    "docs/phase2a/phase2a_contract.md": (
        "D2: prose that said the parameter was open; RR14 schema change (amendment 03)",
        "159d647eafb912771bbb303ac120d1a1084d6cd24b60b79dead3b145b4751907",
    ),
}


class AuditError(RuntimeError):
    pass


def _git(root: Path, *args: str) -> bytes:
    done = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )
    if done.returncode != 0:
        raise AuditError(f"git {' '.join(args)}: {done.stderr.decode().strip()}")
    return done.stdout


def _facts(read: Any) -> dict[str, Any]:
    """The five Phase-2A facts, from a reader of repository-relative JSON."""
    gate = read("docs/phase2a/reference_gate.json")
    spec = read("docs/phase2a/mapping_specification.json")
    status = read("docs/phase2a/phase2a_status.json")
    return {
        "eligible_nodes": gate["eligible_nodes"],
        "scenario_gate_verdict": gate["verdict"],
        "scenario_unmet_requirements": gate["unmet_requirements"],
        "numerical_personalization": status["numerical_personalization"],
        "min_reference_donors": spec["parameters"]["min_reference_donors"],
        "cnt_condition_class": status["owner_decisions_applied"]["Q4"],
        "measured_personalization_verdict": gate["measured_personalization_verdict"],
        "rr13_is_separate_from_scenario_gate": not any(
            req.startswith("RR13")
            for reqs in gate["unmet_requirements"].values()
            for req in reqs
        )
        and any(
            req.startswith("RR13")
            for reqs in gate["measured_unmet_requirements"].values()
            for req in reqs
        ),
        "claim_level_if_ready": gate["claim_level_if_ready"],
    }


def _present_now(root: Path) -> set[str]:
    """Every file under a frozen prefix: tracked, untracked AND gitignored."""
    listed: set[str] = set()
    for extra in (
        [],
        ["--others", "--exclude-standard"],
        ["--others", "--ignored", "--exclude-standard"],
    ):
        listed |= set(
            subprocess.run(
                ["git", "-C", str(root), "ls-files", "--cached", *extra],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        )
    return {line for line in listed if line.startswith(FROZEN_PREFIXES)}


def _main_worktree(root: Path) -> Path:
    common = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(common).resolve().parent


def _has_link(base: Path, relative: str) -> bool:
    probe = base / relative
    while probe != base:
        if probe.is_symlink():
            return True
        probe = probe.parent
    return False


def _links_inside(root: Path, relative: str) -> bool:
    """A symlink on the path that leads anywhere but the same file of this repository.

    A frozen file replaced by a link to identical bytes elsewhere would pass a
    byte comparison today and change silently tomorrow, so it counts as a
    change. The one link that is not a change is a mirror of the repository's
    own main work tree at the same relative path, where that main path has no
    link of its own (the generator-determinism test builds its shadow root that
    way).
    """
    if not _has_link(root, relative):
        return False
    main = _main_worktree(root)
    if main == root.resolve() or _has_link(main, relative):
        return True
    return (root / relative).resolve() != (main / relative)


def frozen_changes(root: Path) -> list[str]:
    """Every frozen path that differs from the base: changed, deleted, new,
    gitignored, or reached through a symlink."""
    base = {
        line
        for line in _git(root, "ls-tree", "-r", "--name-only", BASE_COMMIT)
        .decode()
        .splitlines()
        if line.startswith(FROZEN_PREFIXES)
    }
    changed = []
    for relative in sorted(base | _present_now(root)):
        path = root / relative
        if (
            relative not in base
            or _links_inside(root, relative)
            or not path.is_file()
            or path.read_bytes() != _git(root, "show", f"{BASE_COMMIT}:{relative}")
        ):
            changed.append(relative)
    return changed


def unapproved(root: Path, changed: list[str]) -> list[str]:
    """Changed frozen paths whose current bytes are not the exact bytes approved."""
    refused = []
    for relative in changed:
        approval = OWNER_APPROVED_CHANGES.get(relative)
        path = root / relative
        if (
            approval is None
            or _links_inside(root, relative)
            or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != approval[1]
        ):
            refused.append(relative)
    return refused


def compute(root: Path = REPO) -> dict[str, Any]:
    root = root.resolve()
    changed = frozen_changes(root)
    refused = unapproved(root, changed)
    if refused:
        raise AuditError(f"frozen artifacts changed without owner approval: {refused}")
    at_base = _facts(lambda rel: json.loads(_git(root, "show", f"{BASE_COMMIT}:{rel}")))
    now = _facts(lambda rel: json.loads((root / rel).read_text(encoding="utf-8")))
    checks = {
        "only_E_KLF12_HIGH_structurally_eligible": at_base["eligible_nodes"]
        == ["E_KLF12_HIGH"],
        "numerical_personalization_blocked": at_base["numerical_personalization"]
        == "BLOCKED",
        "min_reference_donors_intentionally_unset": at_base["min_reference_donors"]
        == {"value": None, "provenance": P.PENDING},
        "cnt_condition_class_unresolved": "unresolved"
        in at_base["cnt_condition_class"],
        "rr13_separate_from_scenario_gate": at_base[
            "rr13_is_separate_from_scenario_gate"
        ]
        and at_base["measured_personalization_verdict"] == "BLOCKED_BRIDGE_UNVALIDATED",
    }
    if not all(checks.values()):
        raise AuditError(
            f"the Phase-2A starting state is not the one Phase 2B assumes: {checks}"
        )
    return {
        "schema_version": 1,
        "task": TASK,
        "base_commit": BASE_COMMIT,
        "phase2a_at_base": at_base,
        "starting_state_checks": checks,
        "phase2a_now": now,
        "frozen_prefixes": list(FROZEN_PREFIXES),
        "frozen_files_changed_since_base": [
            {
                "path": c,
                "owner_approval": OWNER_APPROVED_CHANGES[c][0],
                "approved_sha256": OWNER_APPROVED_CHANGES[c][1],
            }
            for c in changed
        ],
        "repaired": "nothing: Phase 2A is audited, not repaired; the only changes are the owner-approved D2 update and the owner-approved RR14 citation-schema change",
    }


def build(root: Path | None = None) -> Path:
    active = root or REPO
    out = active / OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(compute(active), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    print(f"wrote {build()}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
