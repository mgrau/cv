#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    # Provide an empty local biblatex data model file to prevent TeX Live
    # from attempting to install a non-existent package.
    dm_cfg = root / "biblatex-dm.cfg"
    if not dm_cfg.exists():
        dm_cfg.write_text("% Local biblatex data model (empty)\n", encoding="utf-8")

    # Touch expected .bbl files so TeX Live doesn't try to install them.
    stems = [
        "cv-full",
        "cv-odu",
        "cv-1p",
        "cv-2p",
        "cv-3p",
        "cv-web",
    ]
    output_dir = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", root / "_build"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for stem in stems:
        (root / f"{stem}.bbl").touch()
        (output_dir / f"{stem}.bbl").touch()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
