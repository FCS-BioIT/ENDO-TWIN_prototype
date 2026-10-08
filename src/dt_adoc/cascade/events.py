"""Per-node switching events read off one single-trajectory MaBoSS run.

cmaboss exposes no event stream. A ``sample_count = 1`` run reports, for every
tick window ``[t_j, t_j + tick)``, the fraction of that window the trajectory
spent with each node ON. This module reads switching events off that table.

What the table determines, and what it does not:

- A **whole** window (occupancy 0 or 1) holds no switch: any departure would
  lower the occupancy. A **fractional** window holds at least one.
- A run of ``L`` consecutive fractional windows between known states ``a``
  (before) and ``b`` (after) needs at least ``L`` switches, plus one when the
  parity of ``L`` cannot carry ``a`` to ``b`` (each window alone needs one switch
  if its end states differ, two if they agree). That minimum is ``n_min``. It is
  a **lower bound**: a window can hide further out-and-back pairs.
- When a fractional window is entered in state ``s`` and left in ``1 - s`` with
  exactly one switch inside, the switch time is ``t_j + tick * occupancy(s)``,
  exactly. Whether there was exactly one is not observable; ``first_resolved``
  says the window is *consistent* with one switch (single fractional window,
  differing end states). Otherwise the reported time is an upper bound on the
  first departure, which happened within that window.
- A fractional last window leaves the final state unknown (``final`` is None).
- So the first switch is only known to lie in ``[first_lower, first_upper]``:
  the start of its window and the reconstructed time. Two nodes are ordered
  only when one interval ends before the other begins, which holds whenever
  their first switches fall in different windows, and never within one.

Validated against the installed backend (``docs/perturbation_cascade/README.md``,
Stage A): reconstructed one-switch times agree to 1e-16 across ticks from 1.0
to 0.001 for the same seed, and on a rate-1 toggle ``n_min`` equals the fine-tick
count in every trajectory at tick 0.01.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: Occupancies within this distance of 0 or 1 are float dust from the window
#: integral, not switches (values like 0.9999999999 occur in practice).
SNAP_TOLERANCE = 1e-9

NO_SWITCH = "no_switch"
#: Net change with ``n_min == 1``: consistent with exactly one switch, but
#: ``n_min`` is a lower bound, so a fractional window may hide further pairs.
#: The name says what is known; it does not claim the node switched once.
NET_CHANGE_N_MIN_1 = "net_change_n_switches_min_1"
#: Net change that needs at least three switches (``n_min > 1``, odd).
NET_CHANGE_N_MIN_GT_1 = "net_change_n_switches_min_gt_1"
TRANSIENT_RETURN = "transient_return"
UNRESOLVED_END = "unresolved_end"
CATEGORIES = (
    NO_SWITCH,
    NET_CHANGE_N_MIN_1,
    NET_CHANGE_N_MIN_GT_1,
    TRANSIENT_RETURN,
    UNRESOLVED_END,
)


@dataclass(frozen=True)
class NodeEvents:
    initial: int | None
    final: int | None
    n_min: int
    first_time: float
    first_resolved: bool | None
    last_time: float
    last_resolved: bool | None
    category: str
    first_lower: float = np.nan
    """Earliest time the first switch can have happened: the start of its window."""
    first_upper: float = np.nan
    """Latest time it can have happened. Equal to ``first_time`` when that is
    known; a hidden out-and-back pair earlier in the window can only make the
    true first switch earlier, never later. Order between two nodes is
    identifiable only when one interval ends before the other begins."""


def snap(values: np.ndarray, tolerance: float = SNAP_TOLERANCE) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return np.where(
        values < tolerance, 0.0, np.where(values > 1.0 - tolerance, 1.0, values)
    )


def _segment_min(length: int, before: int | None, after: int | None) -> int:
    if before is None or after is None:
        return length
    reachable = before if length % 2 == 0 else 1 - before
    return length if reachable == after else length + 1


def _crossing_time(start: float, tick: float, occupancy_on: float, entered: int):
    occupancy_entered = occupancy_on if entered == 1 else 1.0 - occupancy_on
    return start + tick * occupancy_entered


def node_events(
    occupancy: np.ndarray,
    window_starts: np.ndarray,
    tick: float,
    initial: int | None,
) -> NodeEvents:
    """Events of one node. ``initial`` is the known t = 0 state, or None."""
    x = snap(occupancy)
    starts = np.asarray(window_starts, dtype=float)
    if x.shape != starts.shape or x.ndim != 1 or x.size == 0:
        raise ValueError("occupancy and window_starts must be equal-length 1-D")
    whole = (x == 0.0) | (x == 1.0)
    if initial is None and whole[0]:
        initial = int(x[0])
    if initial is not None and whole[0] and int(x[0]) != initial:
        raise ValueError("the first window contradicts the declared initial state")
    final = int(x[-1]) if whole[-1] else None

    # Switches: runs of fractional windows, plus a state change between two
    # adjacent whole windows (a switch the snap placed on the boundary).
    events: list[
        tuple[int, int, int | None, int | None]
    ] = []  # (j0, j1, before, after)
    n = x.size
    boundary = np.nonzero(whole[1:] & whole[:-1] & (x[1:] != x[:-1]))[0] + 1
    for j in boundary:
        events.append((int(j), int(j) - 1, int(x[j - 1]), int(x[j])))
    frac = np.nonzero(~whole)[0]
    if frac.size:
        breaks = np.nonzero(np.diff(frac) > 1)[0]
        run_starts = np.concatenate(([frac[0]], frac[breaks + 1]))
        run_ends = np.concatenate((frac[breaks], [frac[-1]]))
        for j, k in zip(run_starts.tolist(), run_ends.tolist()):
            before = initial if j == 0 else int(x[j - 1])
            after = final if k == n - 1 else int(x[k + 1])
            events.append((j, k, before, after))
    events.sort(key=lambda e: e[0])

    if not events:
        return NodeEvents(initial, final, 0, np.nan, None, np.nan, None, NO_SWITCH)

    n_min = 0
    for j0, j1, before, after in events:
        n_min += 1 if j1 < j0 else _segment_min(j1 - j0 + 1, before, after)

    def timing(event):
        j0, j1, before, after = event
        if j1 < j0:  # boundary switch between two whole windows
            return float(starts[j0]), True
        if before is None:
            return np.nan, False
        resolved = j0 == j1 and after is not None and after != before
        return _crossing_time(starts[j0], tick, x[j0], before), resolved

    first_time, first_resolved = timing(events[0])
    j0 = events[0][0]
    if events[0][1] < j0:  # boundary switch: within the snap tolerance of t_j0
        first_lower = float(starts[j0]) - tick * SNAP_TOLERANCE
        first_upper = float(starts[j0]) + tick * SNAP_TOLERANCE
    else:
        first_lower = float(starts[j0])
        first_upper = (
            float(first_time) if np.isfinite(first_time) else float(starts[j0]) + tick
        )
    last_event = events[-1]
    if last_event[1] < last_event[0] or last_event[0] == last_event[1]:
        last_time, last_resolved = timing(last_event)
    else:
        # Several fractional windows in a row: the last switch lies in the last
        # of them, entered in an unknown state.
        last_time, last_resolved = float(starts[last_event[1]]), False

    if final is None or initial is None:
        category = UNRESOLVED_END
    elif final == initial:
        category = TRANSIENT_RETURN
    else:
        category = NET_CHANGE_N_MIN_1 if n_min == 1 else NET_CHANGE_N_MIN_GT_1
    return NodeEvents(
        initial,
        final,
        int(n_min),
        float(first_time),
        first_resolved,
        float(last_time),
        last_resolved,
        category,
        first_lower,
        first_upper,
    )


def trajectory_events(
    table: np.ndarray,
    window_starts: np.ndarray,
    nodes: list[str],
    tick: float,
    initial_states: dict[str, int],
) -> dict[str, NodeEvents]:
    """Events of every node of one trajectory (``table`` is windows x nodes)."""
    table = np.asarray(table, dtype=float)
    if table.shape != (len(window_starts), len(nodes)):
        raise ValueError("table shape does not match windows x nodes")
    return {
        node: node_events(table[:, i], window_starts, tick, initial_states.get(node))
        for i, node in enumerate(nodes)
    }
