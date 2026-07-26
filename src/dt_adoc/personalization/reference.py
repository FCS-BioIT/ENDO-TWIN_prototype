"""Reference-policy helpers for future donor contextualization."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ReferencePolicy:
    mode: str
    reference_path: str | None
    note: str

    @property
    def requires_external_reference(self) -> bool:
        return self.mode == "external_reference_required"

    def resolved_reference_path(self, root: Path) -> Path | None:
        if self.reference_path is None:
            return None
        return (root / self.reference_path).resolve()


def load_reference_policy(path: Path) -> ReferencePolicy:
    payload: dict[str, Any] = yaml.safe_load(path.read_text())
    ref = payload["reference_strategy"]
    return ReferencePolicy(
        mode=str(ref["mode"]),
        reference_path=ref.get("reference_path"),
        note=str(ref["note"]),
    )
