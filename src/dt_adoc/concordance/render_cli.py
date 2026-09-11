"""Redraw the concordance figure from tracked source data, without simulating."""

from __future__ import annotations

import json
from pathlib import Path

from dt_adoc.concordance.build import FIGURE_SOURCE_DATA, RUN_SETTINGS
from dt_adoc.concordance.render import render
from dt_adoc.model.provenance import repo_root

FIGURE = Path("docs") / "assets" / "adoc_concordance_v0.4.0.png"


def main() -> None:
    root = repo_root()
    provenance = json.loads((root / RUN_SETTINGS).read_text(encoding="utf-8"))[
        "provenance"
    ]
    destination = render(
        source_data=root / FIGURE_SOURCE_DATA,
        destination=root / FIGURE,
        provenance=provenance,
    )
    print(destination)


if __name__ == "__main__":
    main()
