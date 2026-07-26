"""Mapping rows for source-to-model personalization."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MappingRow:
    source_artifact: str
    donor: str
    condition: str
    compartment: str
    raw_value_ref: str
    missingness_state: str
    reference_name: str
    mapping_function: str
    target_node: str
    mapping_layer: str
    uncertainty: str
    leakage_control_status: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
