"""Load the ENDO-TWIN regulatory network, its rule variants and its interface.

This module is deliberately independent of protocols, data, simulation and
figures: it reads the versioned model directory and returns plain Boolean rules
and MaBoSS text. That separation is what lets the same network be executed as
one integrated MaBoSS model here, or split per compartment for a future
per-cell coupling (:func:`split_compartments`).
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

from endotwin import DEFAULT_MODEL_VERSION
from endotwin.paths import model_dir
from endotwin.topology import derive_dependencies, parse_bnd_rules

INPUT_LAYER = "experimental_input"
OUTPUT_LAYER = "functional_output"
INTERFACE_LAYER = "intercompartmental_signal"
COMPARTMENTS = ("epithelium", "extracellular", "stroma")
RECEIVED_PREFIX = "RX_"

_TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_KEYWORDS = frozenset({"and", "or", "not"})


class ModelError(ValueError):
    """The model files are inconsistent, or a request does not fit the model."""


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


@dataclass(frozen=True)
class RuleVariant:
    variant_id: str
    family: str
    node: str
    logic: str
    is_default: bool
    hypothesis: str
    status: str


@dataclass(frozen=True)
class Model:
    version: str
    root: Path
    rules: dict[str, str]
    node_info: dict[str, dict[str, str]]
    edges: tuple[dict[str, str], ...]
    variants: dict[str, RuleVariant]
    interface: tuple[dict[str, str], ...]
    provenance: dict[str, object] = field(repr=False)

    # -- node roles -------------------------------------------------------
    @property
    def nodes(self) -> tuple[str, ...]:
        return tuple(self.rules)

    @property
    def inputs(self) -> tuple[str, ...]:
        return tuple(n for n in self.rules if self.node_info[n]["layer"] == INPUT_LAYER)

    @property
    def outputs(self) -> tuple[str, ...]:
        return tuple(
            n for n in self.rules if self.node_info[n]["layer"] == OUTPUT_LAYER
        )

    @property
    def readout_nodes(self) -> tuple[str, ...]:
        """Nodes with at least one declared experimental readout."""
        return tuple(n for n in self.rules if self.node_info[n]["readouts"].strip())

    def compartment(self, node: str) -> str:
        return self.node_info[node]["compartment"]

    # -- rule variants ----------------------------------------------------
    def families(self) -> dict[str, tuple[str, ...]]:
        out: dict[str, list[str]] = {}
        for variant in self.variants.values():
            out.setdefault(variant.family, []).append(variant.variant_id)
        return {family: tuple(ids) for family, ids in out.items()}

    def default_selection(self) -> dict[str, str]:
        return {v.family: v.variant_id for v in self.variants.values() if v.is_default}

    def resolve_selection(self, selection: Mapping[str, str] | None) -> dict[str, str]:
        """Complete a partial ``{family: variant_id}`` choice with the defaults.

        A value may also be given as a bare variant id list via
        :meth:`selection_from_ids`.
        """
        resolved = self.default_selection()
        for family, variant_id in (selection or {}).items():
            if family not in resolved:
                raise ModelError(f"unknown rule-variant family: {family}")
            variant = self.variants.get(variant_id)
            if variant is None or variant.family != family:
                raise ModelError(f"{variant_id!r} is not a variant of family {family}")
            resolved[family] = variant_id
        return resolved

    def selection_from_ids(
        self, variant_ids: list[str] | tuple[str, ...]
    ) -> dict[str, str]:
        selection: dict[str, str] = {}
        for variant_id in variant_ids:
            if variant_id not in self.variants:
                raise ModelError(f"unknown rule variant: {variant_id}")
            family = self.variants[variant_id].family
            if family in selection:
                raise ModelError(f"two variants given for family {family}")
            selection[family] = variant_id
        return self.resolve_selection(selection)

    def rules_for(self, selection: Mapping[str, str] | None = None) -> dict[str, str]:
        rules = dict(self.rules)
        for variant_id in self.resolve_selection(selection).values():
            variant = self.variants[variant_id]
            rules[variant.node] = variant.logic
        return rules

    def scenarios(self) -> list[dict[str, str]]:
        """Every combination of one variant per family, defaults first."""
        families = self.families()
        combos: list[dict[str, str]] = [{}]
        for family in sorted(families):
            ordered = sorted(
                families[family], key=lambda v: (not self.variants[v].is_default, v)
            )
            combos = [{**c, family: v} for c in combos for v in ordered]
        return combos


def scenario_label(selection: Mapping[str, str]) -> str:
    return "+".join(selection[f] for f in sorted(selection))


def load_model(version: str = DEFAULT_MODEL_VERSION) -> Model:
    root = model_dir(version)
    rules = parse_bnd_rules(root / "network.bnd")
    node_rows = read_tsv(root / "node_dictionary.tsv")
    node_info = {row["node_id"]: row for row in node_rows}
    if list(node_info) != list(rules):
        raise ModelError(
            "node_dictionary.tsv and network.bnd must list the same nodes in the "
            "same order"
        )
    variants: dict[str, RuleVariant] = {}
    for row in read_tsv(root / "rule_variants.tsv"):
        if row["node"] not in rules:
            raise ModelError(f"variant {row['variant_id']} targets unknown node")
        variants[row["variant_id"]] = RuleVariant(
            variant_id=row["variant_id"],
            family=row["family"],
            node=row["node"],
            logic=row["logic"],
            is_default=row["is_default"] == "true",
            hypothesis=row["hypothesis"],
            status=row["status"],
        )
    model = Model(
        version=version,
        root=root,
        rules=rules,
        node_info=node_info,
        edges=tuple(read_tsv(root / "edges.tsv")),
        variants=variants,
        interface=tuple(read_tsv(root / "interface.tsv")),
        provenance=tomllib.loads((root / "provenance.toml").read_text("utf-8")),
    )
    _check_defaults(model)
    return model


def _check_defaults(model: Model) -> None:
    for family, ids in model.families().items():
        defaults = [v for v in ids if model.variants[v].is_default]
        if len(defaults) != 1:
            raise ModelError(f"family {family} must have exactly one default variant")
        variant = model.variants[defaults[0]]
        if _normalise(model.rules[variant.node]) != _normalise(variant.logic):
            raise ModelError(
                f"default variant {variant.variant_id} differs from network.bnd "
                f"for {variant.node}"
            )
    owners: dict[str, str] = {}
    for variant in model.variants.values():
        owner = owners.setdefault(variant.node, variant.family)
        if owner != variant.family:
            raise ModelError(
                f"node {variant.node} is overridden by two families "
                f"({owner}, {variant.family}); families must own disjoint nodes"
            )


def _normalise(logic: str) -> str:
    return " ".join(logic.replace("(", " ( ").replace(")", " ) ").split())


def dependencies(rules: Mapping[str, str]) -> dict[tuple[str, str], str]:
    """Non-self ``(source, target)`` pairs with structural sign."""
    return derive_dependencies(dict(rules))


def referenced_nodes(logic: str) -> set[str]:
    return {t for t in _TOKEN.findall(logic) if t not in _KEYWORDS}


# -- MaBoSS rendering -------------------------------------------------------


def render_bnd(
    rules: Mapping[str, str],
    *,
    rates: Mapping[str, tuple[float, float]] | None = None,
    forced: Mapping[str, int] | None = None,
    header: str = "",
) -> str:
    """MaBoSS network text for ``rules``.

    ``rates`` scales a node's activation and inactivation rates (default 1, the
    MaBoSS default). ``forced`` pins a node: 0 means it can only switch OFF (a
    knockdown or neutralisation), 1 that it can only switch ON. A forced node
    reaches its pinned value at unit rate, so the intervention has a dynamic
    onset rather than an instantaneous jump.
    """
    rates = dict(rates or {})
    forced = dict(forced or {})
    unknown = (set(rates) | set(forced)) - set(rules)
    if unknown:
        raise ModelError(f"rate or intervention on unknown nodes: {sorted(unknown)}")
    lines = [f"// {line}" for line in header.splitlines()] if header else []
    for node, logic in rules.items():
        lines.append(f"Node {node} {{")
        lines.append(f"  logic = {logic};")
        if node in forced:
            state = forced[node]
            if state not in (0, 1):
                raise ModelError(f"forced state for {node} must be 0 or 1")
            lines.append(f"  rate_up = {1.0 if state else 0.0};")
            lines.append(f"  rate_down = {0.0 if state else 1.0};")
        elif node in rates:
            up, down = rates[node]
            if up <= 0 or down <= 0:
                raise ModelError(f"rates for {node} must be positive")
            lines.append(f"  rate_up = @logic ? {up!r} : 0.0;")
            lines.append(f"  rate_down = @logic ? 0.0 : {down!r};")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# -- compartment decomposition ----------------------------------------------


@dataclass(frozen=True)
class CompartmentNetwork:
    compartment: str
    rules: dict[str, str]
    #: Inputs that come from the medium (experimental conditions).
    medium_inputs: tuple[str, ...]
    #: Inputs that stand for a signal produced by the other compartment.
    received_inputs: dict[str, str]
    #: Nodes of this compartment that another compartment reads.
    exported_signals: tuple[str, ...]


def split_compartments(
    model: Model, selection: Mapping[str, str] | None = None
) -> dict[str, CompartmentNetwork]:
    """Split the integrated network into stand-alone per-compartment networks.

    Every dependency on a node of another compartment (epithelium, the shared
    extracellular space, stroma) is replaced by a received input ``RX_<node>``; medium inputs are copied into each compartment that reads
    them. Feeding each compartment's exported signals into the other's received
    inputs reproduces the integrated network exactly (tested in
    ``tests/mainline/test_interface.py``). This is the decomposition a per-cell
    coupling would use: the extracellular network holds the ligand and secreted
    protein pools that would become diffusing fields. Nothing here assumes
    physical time or space.
    """
    rules = model.rules_for(selection)
    out: dict[str, CompartmentNetwork] = {}
    exported: dict[str, set[str]] = {c: set() for c in COMPARTMENTS}
    for compartment in COMPARTMENTS:
        own = [n for n in rules if model.compartment(n) == compartment]
        medium: set[str] = set()
        received: dict[str, str] = {}
        new_rules: dict[str, str] = {}
        for node in own:
            logic = rules[node]
            for ref in sorted(referenced_nodes(logic)):
                ref_compartment = model.compartment(ref)
                if ref_compartment == compartment or ref == node:
                    continue
                if ref_compartment == "medium":
                    medium.add(ref)
                    continue
                rx = RECEIVED_PREFIX + ref
                received[rx] = ref
                exported[ref_compartment].add(ref)
                logic = re.sub(rf"\b{re.escape(ref)}\b", rx, logic)
            new_rules[node] = logic
        ordered_inputs = [n for n in rules if n in medium]
        full = {n: n for n in ordered_inputs}
        full.update({rx: rx for rx in received})
        full.update(new_rules)
        out[compartment] = CompartmentNetwork(
            compartment=compartment,
            rules=full,
            medium_inputs=tuple(ordered_inputs),
            received_inputs=received,
            exported_signals=(),
        )
    return {
        c: CompartmentNetwork(
            compartment=net.compartment,
            rules=net.rules,
            medium_inputs=net.medium_inputs,
            received_inputs=net.received_inputs,
            exported_signals=tuple(n for n in rules if n in exported[c]),
        )
        for c, net in out.items()
    }
