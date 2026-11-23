#!/usr/bin/env python
"""Render the sequential MaBoSS pathway-dynamics animation.

Thin wrapper around ``dt_adoc.cli render-dynamics`` so the animation can be
regenerated without remembering the module path. Every option is forwarded
unchanged; see ``docs/visualization.md`` for what the figure does and does not
claim.

    python -B src/scripts/render_maboss_dynamics.py --model adoc-literature-v0.2.0
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dt_adoc.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["render-dynamics", *sys.argv[1:]]))
