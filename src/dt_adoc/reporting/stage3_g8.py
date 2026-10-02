"""Gate G8: v0.6.0 with named interventions reproduces v0.5.2 with marker nodes.

Stage 3 of the intervention-layer refactor (``docs/intervention_layer_stage3.md``
§8) deletes ``IN_MIFEPRISTONE``, ``IN_ANTI_SPP1`` and ``IN_HAND2_LOSS``. G8 is
the proof that nothing biological moved. The parent is v0.5.2 run with its
marker-timed protocols; the child is v0.6.0 run with its name-timed protocols.
Both go through the production ``run_protocol`` / ``protocol_continuation``,
unpatched.

The projection ``project`` drops the deleted nodes. Within a phase they are
constant, so it is a relabelling, and ``_project_states`` refuses a collapse.

- **Stage A** (no MaBoSS). ``composed_equivalence`` compares every node's composed
  function over all free variables, for every combination of marker values.
  ``_network_equivalence`` compares, per executed phase, the rendered rules MaBoSS
  loaded, by exhaustive evaluation. ``_cfg_lines`` compares the merged cfgs as
  text.
- **Stage B.** ``compare_phase`` requires, per phase and exactly after
  projection: every node trajectory, the last-node marginals, the last-state
  distribution, the continuation handed on, the vetoed targets, and the phase's
  identity.

The pre-registered fallback (§8) is not implemented here. It is used only if
Stage B fails for a draw-sequence reason, and it has not been needed.

``python -m dt_adoc.reporting.stage3_g8`` writes
``docs/intervention_layer_stage3/g8_report.json``. The integration test
``tests/integration/test_stage3_g8_runtime.py`` runs the same comparison
independently and does not read that file.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import re
import shutil
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from dt_adoc.maboss_adapter import render_network_with_logic_overrides
from dt_adoc.model.runtime import resolve_model
from dt_adoc.model.topology import parse_bnd_rules
from dt_adoc.perturbations.engine import (
    LIBRARY_PATH,
    _evaluable,
    _value,
    intervention_logic_overrides,
    library_for_version,
    load_intervention_library,
)
from dt_adoc.protocols.conditions import (
    MARKERLESS_PROTOCOLS_PATH,
    protocol_definitions,
)
from dt_adoc.reporting.structure import _topological_order
from dt_adoc.reporting.v060_increment import (
    DELETED_NODES,
    MIGRATED_INTERVENTIONS,
)
from dt_adoc.reporting.v060_increment import (
    MODEL_VERSION as CHILD,
)
from dt_adoc.reporting.v060_increment import (
    PARENT_VERSION as PARENT,
)
from dt_adoc.simulation import runner

SEEDS = (1, 2, 3)
SAMPLE_COUNT = 1000
REPORT = Path("docs/intervention_layer_stage3/g8_report.json")
VETO_SUFFIX = ") and not 1"
_DELETED = frozenset(DELETED_NODES)
_LABEL_SEPARATOR = " -- "


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Projection.


def _project_states(last_states: Any) -> tuple[dict[frozenset[str], float], int]:
    """The last-state distribution without the deleted nodes, and how many collapsed.

    A state label is the set of its active tracked nodes. Two parent labels
    reaching one child label would mean a deleted node varied inside the phase.
    """
    row = last_states.iloc[-1]
    projected: dict[frozenset[str], float] = {}
    collapsed = 0
    for label in sorted(row.index):
        probability = float(row[label])
        if probability == 0.0:
            continue
        active = frozenset(
            token.strip()
            for token in str(label).split(_LABEL_SEPARATOR)
            if token.strip() and token.strip() != "<nil>"
        )
        key = active - _DELETED
        if key in projected:
            collapsed += 1
        projected[key] = projected.get(key, 0.0) + probability
    return projected, collapsed


def project(result: runner.ConditionRunResult) -> dict[str, Any]:
    """What one phase reports, with the deleted nodes projected out."""
    traj = result.nodes_probtraj
    keep = [c for c in traj.columns if c not in _DELETED]
    last_nodes = result.last_nodes_probtraj
    states, collapsed = _project_states(result.last_states_probtraj)
    return {
        "times": [float(t) for t in traj.index],
        "columns": keep,
        "trajectory": traj[keep].to_numpy().tolist(),
        "last_nodes": last_nodes[[c for c in last_nodes.columns if c not in _DELETED]]
        .to_numpy()
        .tolist(),
        "last": {k: v for k, v in result.last.items() if k not in _DELETED},
        "last_states": states,
        "collapsed_labels": collapsed,
    }


def project_continuation(state: runner.ContinuationState | None) -> Any:
    if state is None:
        return None
    return {
        "mode": state.mode,
        "method": state.continuation_method,
        "node_ids": tuple(state.node_ids),
        "distribution": dict(state.distribution),
        "forced": {k: v for k, v in state.forced_nodes.items() if k not in _DELETED},
        "cutoff": state.probability_cutoff,
        "counts": (state.source_state_count, state.retained_state_count),
        "dropped": state.dropped_probability_mass,
        "policy": state.memory_node_policy,
        "source_protocol": state.source_protocol,
    }


def vetoed(result: runner.ConditionRunResult) -> dict[str, str]:
    return {
        node: logic
        for node, logic in result.executed_network["logic_overrides"].items()
        if logic.endswith(VETO_SUFFIX)
    }


def _cfg_lines(result: runner.ConditionRunResult) -> list[str]:
    pattern = re.compile(rf"^\s*(?:{'|'.join(DELETED_NODES)})\.\w+\s*=")
    return [
        line
        for line in result.merged_cfg.read_text(encoding="utf-8").splitlines()
        if not pattern.match(line)
    ]


def _executed_rules(
    result: runner.ConditionRunResult, model_version: str, root: Path
) -> dict[str, str]:
    text = resolve_model(model_version, root).network_bnd.read_text(encoding="utf-8")
    rendered = render_network_with_logic_overrides(
        text, logic_overrides=result.executed_network["logic_overrides"]
    )
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if digest != result.executed_network["network_sha256"]:
        raise AssertionError("the executed-network record does not rebuild its text")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "network.bnd"
        path.write_text(rendered, encoding="utf-8")
        return parse_bnd_rules(path)


def _rules_equivalent(left: str, right: str) -> bool:
    left_expression, left_names = _evaluable(left)
    right_expression, right_names = _evaluable(right)
    names = sorted(left_names | right_names)
    for values in itertools.product((False, True), repeat=len(names)):
        point = dict(zip(names, values))
        if _value(left_expression, point) != _value(right_expression, point):
            return False
    return True


def _network_equivalence(parent: dict[str, str], child: dict[str, str]) -> list[str]:
    """Rule-by-rule differences between two executed networks, after projection."""
    problems = []
    if set(child) != set(parent) - _DELETED:
        problems.append(
            f"node sets differ: {sorted(set(child) ^ (set(parent) - _DELETED))}"
        )
    for node in sorted(set(child) & set(parent)):
        names = _evaluable(parent[node])[1] | _evaluable(child[node])[1]
        if names & _DELETED and node not in _DELETED:
            problems.append(f"{node} reads a deleted node in an executed rule")
            continue
        if not _rules_equivalent(parent[node], child[node]):
            problems.append(f"{node}: executed rules are not equivalent")
    return problems


# ---------------------------------------------------------------------------
# Stage A.1: composed functions, for every combination of marker values.


def _column_rules(rules: dict[str, str]) -> dict[str, str]:
    """Rules as bitwise expressions where the literals 0 and 1 are whole columns."""

    def bitwise(logic: str) -> str:
        text = re.sub(r"\b0\b", "ZERO", re.sub(r"\b1\b", "ONE", logic))
        return text.replace(" and ", " & ").replace(" or ", " | ").replace("not ", "~")

    return {node: bitwise(logic) for node, logic in rules.items()}


def _composed(rules: dict[str, str], free: tuple[str, ...]) -> dict[str, int]:
    states = 2 ** len(free)
    mask = (1 << states) - 1
    columns: dict[str, int] = {"ZERO": 0, "ONE": mask}
    for index, node in enumerate(free):
        block = 1 << index
        column = 0
        for start in range(block, states, block * 2):
            column |= ((1 << block) - 1) << start
        columns[node] = column
    order = _topological_order(rules, set(free))
    expressions = _column_rules(rules)
    for node in order:
        if node not in columns:
            columns[node] = eval(expressions[node], {}, columns) & mask
    return {node: columns[node] for node in rules}


def composed_equivalence(root: Path) -> dict[str, Any]:
    """Stage A.1: for each marker combination, the child's vetoed functions equal the parent's.

    The parent's markers are fixed to the combination. The child renders, through
    the engine, the interventions whose markers are ON. Both are then evaluated
    over all assignments of the child's free variables.
    """
    library = load_intervention_library(root)
    parent_text = resolve_model(PARENT, root).network_bnd.read_text(encoding="utf-8")
    child_text = resolve_model(CHILD, root).network_bnd.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "p.bnd"
        path.write_text(parent_text, encoding="utf-8")
        parent_rules = parse_bnd_rules(path)
    child_rules_base = parse_bnd_rules(resolve_model(CHILD, root).network_bnd)
    free = tuple(n for n in child_rules_base if child_rules_base[n].strip() == n)
    combinations = []
    for values in itertools.product((False, True), repeat=len(DELETED_NODES)):
        setting = dict(zip(DELETED_NODES, values))
        fixed = {}
        for node, logic in parent_rules.items():
            if node in _DELETED:
                continue
            for marker, on in setting.items():
                logic = re.sub(rf"\b{marker}\b", "1" if on else "0", logic)
            fixed[node] = logic
        named = [MIGRATED_INTERVENTIONS[m] for m, on in setting.items() if on]
        overrides = intervention_logic_overrides(
            child_text, named, model_version=CHILD, library=library
        )
        child_rules = {**child_rules_base, **overrides}
        parent_columns = _composed(fixed, free)
        child_columns = _composed(child_rules, free)
        differing = sorted(
            n for n in child_columns if child_columns[n] != parent_columns.get(n)
        )
        combinations.append(
            {
                "markers_on": [m for m, on in setting.items() if on],
                "named_interventions": named,
                "nodes_compared": len(child_columns),
                "nodes_whose_composed_function_differs": differing,
            }
        )
    return {
        "free_variables": list(free),
        "enumerated_assignments": 2 ** len(free),
        "combinations": combinations,
        "passed": all(
            not c["nodes_whose_composed_function_differs"] for c in combinations
        ),
    }


# ---------------------------------------------------------------------------
# Protocol mapping (the §5 projection of the phase structure).


def projected_definition(definition: Any, *, parent: bool) -> dict[str, Any]:
    """A definition with markers turned into names, for comparing versions."""
    steps = []
    for step in definition.steps:
        names = set(step.interventions)
        if parent:
            names |= {
                MIGRATED_INTERVENTIONS[n]
                for n, on in step.input_states.items()
                if n in MIGRATED_INTERVENTIONS and on
            }
        steps.append(
            {
                "step_id": step.step_id,
                "relative_order": step.relative_order,
                "relative_duration": step.relative_duration,
                "duration_note": step.duration_note,
                "input_states": {
                    k: v for k, v in step.input_states.items() if k not in _DELETED
                },
                "interventions": sorted(names),
            }
        )
    return {
        "protocol_id": definition.protocol_id,
        "protocol_class": definition.protocol_class,
        "condition_cfg": Path(definition.condition_cfg).name,
        "comparator_role": definition.comparator_role,
        "continuation_from": definition.continuation_from,
        "continuation": definition.continuation,
        "evidence_ids": definition.evidence_ids,
        "notes": definition.notes,
        "steps": steps,
    }


def protocol_mapping(root: Path, child_root: Path | None = None) -> list[str]:
    """Differences between the v0.5.2 and v0.6.0 phase structures under §5."""
    parent = protocol_definitions(root, model_version=PARENT)
    child = protocol_definitions(child_root or root, model_version=CHILD)
    problems = []
    if set(parent) != set(child):
        problems.append(f"protocol ids differ: {sorted(set(parent) ^ set(child))}")
    for protocol_id in sorted(set(parent) & set(child)):
        a = projected_definition(parent[protocol_id], parent=True)
        b = projected_definition(child[protocol_id], parent=False)
        for key in a:
            if a[key] != b[key]:
                problems.append(f"{protocol_id}: {key} differs")
    return problems


# ---------------------------------------------------------------------------
# Stage B: running the lineages.


@dataclass
class Phase:
    protocol_id: str
    outputs: dict[str, Any]
    initialisation: Any
    vetoed: dict[str, str]
    executed_rules: dict[str, str]
    cfg_lines: list[str]
    named: tuple[str, ...]
    legacy_input_values: dict[str, bool]
    executed_network: dict[str, Any] = field(repr=False, default_factory=dict)


def _phase(run: runner.ProtocolRunResult, model_version: str, root: Path) -> Phase:
    if len(run.step_results) != 1:
        raise AssertionError(f"{run.protocol_id} is not a one-step protocol")
    result = run.step_results[0]
    return Phase(
        protocol_id=run.protocol_id,
        outputs=project(result),
        initialisation=project_continuation(run.step_initializations[0]),
        vetoed=vetoed(result),
        executed_rules=_executed_rules(result, model_version, root),
        cfg_lines=_cfg_lines(result),
        named=tuple(result.executed_network["named_interventions"]),
        legacy_input_values=dict(result.executed_network["legacy_input_values"]),
        executed_network=dict(result.executed_network),
    )


def run_lineages(
    model_version: str,
    seed: int,
    *,
    root: Path,
    protocol_ids: tuple[str, ...] | None = None,
    sample_count: int = SAMPLE_COUNT,
) -> dict[str, Phase]:
    """Every protocol run as the last phase of its declared lineage.

    Each protocol runs once per seed, from the continuation of its own
    ``continuation_from`` run, so a shared prefix is simulated once. Every
    run's temporary cfg directory is released before this returns.
    """
    definitions = protocol_definitions(root, model_version=model_version)
    wanted = protocol_ids or tuple(definitions)
    runs: dict[str, runner.ProtocolRunResult] = {}
    phases: dict[str, Phase] = {}

    def ensure(protocol_id: str) -> runner.ProtocolRunResult:
        if protocol_id in runs:
            return runs[protocol_id]
        parent_id = definitions[protocol_id].continuation_from
        continuation = None
        if parent_id is not None:
            continuation = runner.protocol_continuation(
                protocol_id, ensure(parent_id), model_version=model_version, root=root
            )
        run = runner.run_protocol(
            protocol_id,
            model_version=model_version,
            root=root,
            continuation=continuation,
            seed=seed,
            sample_count=sample_count,
        )
        runs[protocol_id] = run
        phases[protocol_id] = _phase(run, model_version, root)
        return run

    try:
        for protocol_id in wanted:
            ensure(protocol_id)
    finally:
        for run in runs.values():
            run.release()
    return {pid: phases[pid] for pid in wanted}


def compare_phase(parent: Phase, child: Phase) -> list[str]:
    """Every difference between a parent and a child phase, after projection."""
    problems = []
    for key in ("times", "columns", "trajectory", "last_nodes", "last", "last_states"):
        if parent.outputs[key] != child.outputs[key]:
            problems.append(key)
    if parent.outputs["collapsed_labels"] or child.outputs["collapsed_labels"]:
        problems.append("collapsed_labels")
    if parent.initialisation != child.initialisation:
        problems.append("initialisation")
    if set(parent.vetoed) != set(child.vetoed):
        problems.append("vetoed_targets")
    network = _network_equivalence(parent.executed_rules, child.executed_rules)
    if network:
        problems.append("executed_network: " + "; ".join(network))
    if parent.cfg_lines != child.cfg_lines:
        problems.append("merged_cfg")
    expected_names = sorted(
        MIGRATED_INTERVENTIONS[m] for m, on in parent.legacy_input_values.items() if on
    ) + sorted(parent.named)
    if sorted(child.named) != sorted(expected_names):
        problems.append("named_interventions")
    if child.legacy_input_values:
        problems.append("child legacy_input_values")
    return problems


def _max_difference(parent: Phase, child: Phase) -> float | None:
    a, b = parent.outputs["trajectory"], child.outputs["trajectory"]
    if parent.outputs["columns"] != child.outputs["columns"] or len(a) != len(b):
        return None
    return max(
        (abs(x - y) for row_a, row_b in zip(a, b) for x, y in zip(row_a, row_b)),
        default=0.0,
    )


def compare_lineages(
    parent: dict[str, Phase], child: dict[str, Phase]
) -> dict[str, dict[str, Any]]:
    return {
        protocol_id: {
            "identical": not (
                problems := compare_phase(parent[protocol_id], child[protocol_id])
            ),
            "differences": problems,
            "max_abs_trajectory_difference": _max_difference(
                parent[protocol_id], child[protocol_id]
            ),
            "vetoed_targets": sorted(child[protocol_id].vetoed),
            "named_interventions": list(child[protocol_id].named),
        }
        for protocol_id in parent
    }


# ---------------------------------------------------------------------------
# The standalone condition suite.


def _suite(root: Path) -> list[str]:
    import tomllib

    spec = resolve_model(PARENT, root)
    payload = tomllib.loads(spec.provenance.read_text(encoding="utf-8"))
    return [Path(c).name for c in payload["condition_suite"]["conditions"]]


def _cfg_markers(path: Path) -> list[str]:
    on = []
    for marker in DELETED_NODES:
        match = re.search(
            rf"^{marker}\.istate\s*=\s*(\w+);", path.read_text(), re.MULTILINE
        )
        if match and match.group(1) in {"TRUE", "1"}:
            on.append(MIGRATED_INTERVENTIONS[marker])
    return sorted(on)


def _condition_phase(
    model_version: str, cfg: str, seed: int, root: Path, interventions: tuple[str, ...]
) -> Phase:
    spec = resolve_model(model_version, root)
    result = runner.run_cmaboss_condition(
        model_version=model_version,
        condition_cfg=spec.condition_dir / cfg,
        root=root,
        interventions=interventions,
        seed=seed,
        sample_count=SAMPLE_COUNT,
    )
    try:
        return Phase(
            protocol_id=cfg,
            outputs=project(result),
            initialisation=None,
            vetoed=vetoed(result),
            executed_rules=_executed_rules(result, model_version, root),
            cfg_lines=_cfg_lines(result),
            named=tuple(result.executed_network["named_interventions"]),
            legacy_input_values=dict(result.executed_network["legacy_input_values"]),
        )
    finally:
        result.release()


def condition_suite(root: Path, seed: int) -> dict[str, dict[str, Any]]:
    """Each condition run as one phase; the child names what the parent cfg marks ON."""
    parent_dir = resolve_model(PARENT, root).condition_dir
    parent, child = {}, {}
    for cfg in _suite(root):
        parent[cfg] = _condition_phase(PARENT, cfg, seed, root, ())
        child[cfg] = _condition_phase(
            CHILD, cfg, seed, root, tuple(_cfg_markers(parent_dir / cfg))
        )
    return compare_lineages(parent, child)


# ---------------------------------------------------------------------------
# Structural assertions (design §11).


def structural_violations(root: Path) -> list[str]:
    """Every way v0.6.0 still names a deleted marker where it would execute."""
    problems = []
    spec = resolve_model(CHILD, root)
    rules = parse_bnd_rules(spec.network_bnd)
    for node in DELETED_NODES:
        if node in rules:
            problems.append(f"{node} is a node of {CHILD}")
        readers = sorted(n for n, r in rules.items() if re.search(rf"\b{node}\b", r))
        if readers:
            problems.append(f"{node} is read by {readers}")
        for cfg in [spec.baseline_cfg, *sorted(spec.condition_dir.glob("*.cfg"))]:
            if re.search(rf"\b{node}\b", cfg.read_text(encoding="utf-8")):
                problems.append(f"{node} is set in {cfg.name}")
        with spec.node_dictionary.open(encoding="utf-8", newline="") as handle:
            if node in {r["node_id"] for r in csv.DictReader(handle, delimiter="\t")}:
                problems.append(f"{node} has a node_dictionary row")
    try:
        definitions = protocol_definitions(root, model_version=CHILD)
    except Exception as error:  # noqa: BLE001 - reported as a violation
        problems.append(
            f"the protocols do not resolve: {type(error).__name__}: {error}"
        )
        definitions = {}
    for protocol_id, definition in definitions.items():
        for step in definition.steps:
            named = sorted(set(step.input_states) & _DELETED)
            if named:
                problems.append(f"{protocol_id} sets {named}")
    try:
        library = load_intervention_library(root)
    except Exception as error:  # noqa: BLE001 - reported as a violation
        # Reported alongside the network checks above rather than instead of
        # them, so a refused library does not hide what the model still names.
        problems.append(f"the library does not load: {type(error).__name__}: {error}")
        return problems
    view = library_for_version(library, CHILD)
    parent_view = library_for_version(library, PARENT)
    for intervention_id in MIGRATED_INTERVENTIONS.values():
        rows = view.get(intervention_id, ())
        if not rows:
            problems.append(f"{intervention_id} has no {CHILD} row")
            continue
        if any(r.legacy_input_node in _DELETED for r in rows):
            problems.append(f"{intervention_id} requires a deleted marker")
        targets = {r.target_node for r in rows}
        expected = {r.target_node for r in parent_view.get(intervention_id, ())}
        if targets != expected:
            problems.append(
                f"{intervention_id} targets {sorted(targets)}, not {sorted(expected)}"
            )
        child_text = spec.network_bnd.read_text(encoding="utf-8")
        rendered = intervention_logic_overrides(
            child_text, [intervention_id], model_version=CHILD, library=library
        )
        if set(rendered) != expected:
            problems.append(f"{intervention_id} renders {sorted(rendered)}")
    return problems


# ---------------------------------------------------------------------------
# Negative controls (design §8).


@contextmanager
def sandbox(root: Path, edit: Callable[[Path], None]) -> Iterator[Path]:
    """A copy of what the runner reads, with ``edit`` applied to the copy only."""
    with tempfile.TemporaryDirectory(prefix="stage3-g8-") as tmp:
        destination = Path(tmp)
        shutil.copytree(
            root / "models",
            destination / "models",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        shutil.copytree(root / "config", destination / "config")
        for relative in (
            "context/evidence-register.tsv",
            "docs/intervention_layer_stage3.md",
        ):
            (destination / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, destination / relative)
        edit(destination)
        yield destination


def edit_protocol_step(
    protocol_id: str, interventions: list[str]
) -> Callable[[Path], None]:
    """An edit that sets one v0.6.0 protocol's step interventions."""

    def apply(destination: Path) -> None:
        path = destination / MARKERLESS_PROTOCOLS_PATH
        payload = json.loads(path.read_text(encoding="utf-8"))
        (row,) = [r for r in payload["protocols"] if r["protocol_id"] == protocol_id]
        (step,) = row["steps"]
        step.pop("interventions", None)
        if interventions:
            step["interventions"] = list(interventions)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return apply


def _both(*edits: Callable[[Path], None]) -> Callable[[Path], None]:
    def apply(destination: Path) -> None:
        for edit in edits:
            edit(destination)

    return apply


#: Each control, and the lineages it is run on.
NEGATIVE_CONTROLS: dict[str, tuple[Callable[[Path], None], tuple[str, ...]]] = {
    "NC1_anti_spp1_omitted": (
        edit_protocol_step("hormone_treated_anti_spp1", []),
        ("hormone_treated_anti_spp1",),
    ),
    "NC2_anti_spp1_not_washed_out": (
        edit_protocol_step("washout", ["anti_spp1"]),
        ("washout",),
    ),
    "NC3_mifepristone_mistimed": (
        _both(
            edit_protocol_step("hormone_treated_mifepristone", []),
            edit_protocol_step(
                "adhesion_challenge_hormone_treated_mifepristone", ["mifepristone"]
            ),
        ),
        (
            "hormone_treated_mifepristone",
            "adhesion_challenge_hormone_treated_mifepristone",
        ),
    ),
}


def keep_gate_without_node(destination: Path) -> None:
    """NC4a: the HAND2 conjunct survives the deletion of its node."""
    path = destination / "models/superset" / CHILD / "network.bnd"
    text = path.read_text(encoding="utf-8")
    old = "  logic = S_BMP2 or S_PGR;\n"
    if text.count(old) != 1:
        raise AssertionError("v0.6.0 S_HAND2 rule not found")
    path.write_text(
        text.replace(old, "  logic = (S_BMP2 or S_PGR) and not IN_HAND2_LOSS;\n"),
        encoding="utf-8",
    )


def keep_gate_and_node(destination: Path) -> None:
    """NC4b: the node and its gate both survive, held OFF by the cfg."""
    keep_gate_without_node(destination)
    model = destination / "models/superset" / CHILD
    path = model / "network.bnd"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "Node IN_ER_STRESS_EXCESS {",
            "Node IN_HAND2_LOSS {\n  logic = IN_HAND2_LOSS;\n}\n\nNode IN_ER_STRESS_EXCESS {",
        ),
        encoding="utf-8",
    )
    cfg = model / "baseline.cfg"
    cfg.write_text(
        cfg.read_text(encoding="utf-8").replace(
            "IN_ER_STRESS_EXCESS.istate = FALSE;",
            "IN_HAND2_LOSS.istate = FALSE;\nIN_ER_STRESS_EXCESS.istate = FALSE;",
        ),
        encoding="utf-8",
    )


def gate_left_in_place(root: Path) -> dict[str, Any]:
    """NC4: which gates refuse a child that keeps a historical conjunct."""
    outcome: dict[str, Any] = {}
    for name, edit in (
        ("NC4a_gate_kept_node_deleted", keep_gate_without_node),
        ("NC4b_gate_and_node_kept_marker_off", keep_gate_and_node),
    ):
        with sandbox(root, edit) as box:
            refused = {}
            try:
                load_intervention_library(box)
                refused["library_licence"] = None
            except Exception as error:  # noqa: BLE001 - recorded, not swallowed
                refused["library_licence"] = f"{type(error).__name__}: {error}"
            try:
                violations = structural_violations(box)
            except Exception as error:  # noqa: BLE001
                violations = [f"{type(error).__name__}: {error}"]
            refused["structural_assertions"] = violations
            outcome[name] = {
                "detected": bool(refused["library_licence"]) and bool(violations),
                **refused,
            }
    return outcome


def negative_controls(
    root: Path, parent_runs: dict[str, Phase], seed: int
) -> dict[str, Any]:
    """Each control's comparison with the parent; every one must fail G8."""
    results: dict[str, Any] = {}
    for name, (edit, protocols) in NEGATIVE_CONTROLS.items():
        with sandbox(root, edit) as box:
            child = run_lineages(CHILD, seed, root=box, protocol_ids=protocols)
        compared = compare_lineages({p: parent_runs[p] for p in protocols}, child)
        results[name] = {
            "lineages": compared,
            "detected": any(not c["identical"] for c in compared.values()),
        }
    results.update(gate_left_in_place(root))
    return results


# ---------------------------------------------------------------------------
# The report.


def _serialisable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _serialisable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialisable(v) for v in value]
    return value


def build_report(root: Path, seeds: tuple[int, ...] = SEEDS) -> dict[str, Any]:
    stage_b: dict[str, Any] = {}
    suite: dict[str, Any] = {}
    controls: dict[str, Any] = {}
    for seed in seeds:
        parent = run_lineages(PARENT, seed, root=root)
        child = run_lineages(CHILD, seed, root=root)
        stage_b[str(seed)] = compare_lineages(parent, child)
        suite[str(seed)] = condition_suite(root, seed)
        if seed == seeds[0]:
            controls = negative_controls(root, parent, seed)
    stage_a = composed_equivalence(root)
    mapping = protocol_mapping(root)
    structural = structural_violations(root)
    exact = all(
        c["identical"] for runs in stage_b.values() for c in runs.values()
    ) and all(c["identical"] for runs in suite.values() for c in runs.values())
    report = {
        "gate": "G8",
        "design": "docs/intervention_layer_stage3.md",
        "parent_model_version": PARENT,
        "child_model_version": CHILD,
        "deleted_nodes": list(DELETED_NODES),
        "settings": {
            "seeds": list(seeds),
            "sample_count": SAMPLE_COUNT,
            "time": "each step's declared relative_duration; the model's time_tick",
            "criterion": "same-seed exact equality after projection",
            "maboss": metadata.version("maboss"),
        },
        "hashes": {
            "parent_network_bnd": _sha(resolve_model(PARENT, root).network_bnd),
            "child_network_bnd": _sha(resolve_model(CHILD, root).network_bnd),
            "intervention_library": _sha(root / LIBRARY_PATH),
            "protocols_yaml": _sha(root / "config/protocols.yaml"),
            "protocols_markerless_yaml": _sha(root / MARKERLESS_PROTOCOLS_PATH),
        },
        "stage_a": {
            "composed_functions": stage_a,
            "protocol_mapping_differences": mapping,
            "structural_violations": structural,
        },
        "stage_b": {
            "lineages": stage_b,
            "condition_suite": suite,
            "exact": exact,
        },
        "fallback_used": False,
        "negative_controls": controls,
        "passed": bool(
            stage_a["passed"]
            and not mapping
            and not structural
            and exact
            and controls
            and all(c["detected"] for c in controls.values())
        ),
    }
    return _serialisable(report)


def write_report(root: Path) -> Path:
    report = build_report(root)
    path = root / REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


# ---------------------------------------------------------------------------
# Structural counts (design §11), recomputed for both versions by one code path.

STRUCTURE = Path("docs/intervention_layer_stage3/structure_counts.json")


def structural_counts(root: Path) -> dict[str, Any]:
    """Nodes, inputs, free variables, distinct functions and alias classes.

    Computed by ``dt_adoc.reporting.structure.load_structure`` for v0.5.2 and
    v0.6.0 alike, so neither version's numbers are carried over from a document.
    The v0.6.0 figures describe the unperturbed network: its interventions are
    rendered by the engine, so they no longer appear among its free variables.
    """
    from dt_adoc.reporting.structure import load_structure

    versions = {}
    for version in (PARENT, CHILD):
        facts = load_structure(version, root)
        inputs = [n for n in facts.free if n.startswith("IN_")]
        versions[version] = {
            "nodes": len(facts.node_ids),
            "free_variables": len(facts.free),
            "enumerated_assignments": facts.enumerated_states,
            "input_nodes": len(inputs),
            "free_non_input_nodes": sorted(
                n for n in facts.free if not n.startswith("IN_")
            ),
            "inputs": sorted(inputs),
            "unread_inputs": sorted(facts.unread_inputs),
            "distinct_composed_functions": facts.distinct_function_count,
            "alias_classes": sorted(sorted(c) for c in facts.alias_classes),
            "alias_class_count": len(facts.alias_classes),
            "complement_pairs": sorted(list(p) for p in facts.complement_pairs),
            "phenotype_inert_nodes": sorted(facts.phenotype_inert),
            "dependencies": len(facts.edges),
        }
    parent, child = versions[PARENT], versions[CHILD]
    return {
        "design": "docs/intervention_layer_stage3.md",
        "computed_by": "dt_adoc.reporting.structure.load_structure",
        "versions": versions,
        "removed_inputs": sorted(set(parent["inputs"]) - set(child["inputs"])),
        "alias_classes_equal": parent["alias_classes"] == child["alias_classes"],
    }


def write_structure(root: Path) -> Path:
    path = root / STRUCTURE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(structural_counts(root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":  # pragma: no cover
    import sys

    from dt_adoc.model.provenance import repo_root

    if sys.argv[1:] == ["--structure"]:
        print(write_structure(repo_root()))
    else:
        print(write_structure(repo_root()))
        print(write_report(repo_root()))
