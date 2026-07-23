#!/usr/bin/env python3
"""Experience the exact bounded two-domain effect-separation observation."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from semantic_packages.effect_separation import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(root=ROOT))
